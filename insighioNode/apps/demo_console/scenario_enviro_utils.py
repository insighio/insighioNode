from utime import sleep_ms
from external.kpn_senml.senml_unit import SenmlUnits
from external.kpn_senml.senml_unit import SenmlSecondaryUnits
import logging
from sensors import set_sensor_power_on, set_sensor_power_off

from .dictionary_utils import set_value, set_value_float, set_value_int, _get, _has

from .sdi12_response_parsers import parse_sensor_meter, parse_sensor_acclima, parse_sensor_implexx, parse_sensor_licor, parse_generic_sdi12

from . import cfg

import gpio_handler
import _thread
import utime
from math import ceil

_i2c = None
_io_expander_addr = None

_ads_addr = None
_ads_rate = None

_sdi12_config = {}
_modbus_config = {}
_adc_config = []
_pulse_counter_config = []
_pcnt_active = True

V_LOW = 825  # mV
V_HIGH = 2475  # mV

_modbus_reg_quantity_per_format = {
    "uint16": 1,
    "int16": 1,
    "uint32": 2,
    "int32": 2,
    "float": 2,
}

_modbus_struct_format_options = {
    "uint16": "H",
    "int16": "h",
    "uint32": "I",
    "int32": "i",
    "float": "f",
}

_pulse_counter_thread_started = None
pcnt_1_edge_count = 0
pcnt_2_edge_count = 0
_thread_lock = _thread.allocate_lock()
pcnt_last_run_timestamp_ms = 0
pcnt_unstable_readings_1 = 0
pcnt_unstable_readings_2 = 0
pcnt_readings_1 = 0
pcnt_readings_2 = 0

# Add debounce timer variables
from machine import Timer
pcnt_1_debounce_timer = Timer(1)
pcnt_2_debounce_timer = Timer(2)
pcnt_1_pending_edge = False
pcnt_2_pending_edge = False
pcnt_1_filtered_edges = 0
pcnt_2_filtered_edges = 0
DEBOUNCE_TIME_MS = 1  # Debounce period in milliseconds

pcnt_voltage_min_1 = 0
pcnt_voltage_max_1 = 0
pcnt_voltage_min_2 = 0
pcnt_voltage_max_2 = 0


def _initialize_i2c():
    global _i2c
    if _i2c is None:
        from machine import SoftI2C, Pin

        I2C_SCL = cfg.get("_UC_IO_I2C_SCL")
        I2C_SDA = cfg.get("_UC_IO_I2C_SDA")

        if I2C_SCL is None or I2C_SDA is None:
            return None

        _i2c = SoftI2C(scl=Pin(I2C_SCL), sda=Pin(I2C_SDA), freq=400000)

    return _i2c


def _deinitialize_i2c():
    global _i2c
    if _i2c is not None:
        _i2c = None

    return _i2c


def _exec_i2c_op(func):
    _initialize_i2c()
    func()
    _deinitialize_i2c()


def io_expander_init():
    global _io_expander_addr
    _io_expander_addr = cfg.get("_UC_IO_EXPANDER_ADDR")

    # initialized = _initialize_i2c()
    # if not initialized:
    #     return False

    # set all output pins to LOW
    _exec_i2c_op(power_off_all_sensors)

    _exec_i2c_op(initialize_io_expander_ports)

    return True


def initialize_io_expander_ports():
    # set all ports as output except P3 which is input
    # and has UC_IO_XTNDR_ADC_ALERT_RDY
    _i2c.writeto_mem(_io_expander_addr, 3, b"\xf8")


def ads_init():
    global _ads_addr
    global _ads_rate
    _ads_addr = cfg.get("_UC_IO_ADS_ADDR")
    _ads_rate = cfg.get("_ADS_RATE")
    return True


def io_expander_power_on_sdi12_sensors():
    logging.debug("io_expander_power_on_sdi12_sensors - power on SDI12 sensors")
    _i2c.writeto_mem(_io_expander_addr, 1, b"\x02")
    sleep_ms(500)


def io_expander_power_off_sdi12_sensors():
    logging.debug("io_expander_power_off_sdi12_sensors - power off SDI12 sensors")
    power_off_all_sensors()


def io_expander_power_on_modbus():
    logging.debug("io_expander_power_on_modbus - power on MODBUS sensors")
    _i2c.writeto_mem(_io_expander_addr, 1, b"\x01")
    sleep_ms(500)


def io_expander_power_off_modbus():
    logging.debug("io_expander_power_off_modbus - power off MODBUS sensors")
    power_off_all_sensors()


def io_expander_power_on_ads_sensors():
    logging.debug("io_expander_power_on_ads_sensors - power on ADS sensors")
    _i2c.writeto_mem(_io_expander_addr, 1, b"\x04")
    sleep_ms(500)


def io_expander_power_off_adc_sensors():
    logging.debug("io_expander_power_off_adc_sensors - power off ADS sensors")
    power_off_all_sensors()


def power_off_all_sensors():
    _i2c.writeto_mem(_io_expander_addr, 1, b"\x00")


def enable_regulator():
    # power on SDI12 regulator
    logging.debug("enable_regulator - power on regulator")
    set_sensor_power_on(cfg.get("_UC_IO_SNSR_REG_ON"))


def disable_regulator():
    # power off SDI12 regulator
    logging.debug("disable_regulator - power off regulator")
    set_sensor_power_off(cfg.get("_UC_IO_SNSR_REG_ON"))


def initialize_configurations():
    global _sdi12_config
    global _modbus_config
    global _adc_config
    global _pulse_counter_config

    import json

    try:
        _sdi12_config = json.loads(cfg.get("_MEAS_SDI12"))
    except Exception as e:
        logging.exception(e, "Error loading SDI12 config")

    try:
        _modbus_config = json.loads(cfg.get("_MEAS_MODBUS"))
    except Exception as e:
        logging.exception(e, "Error loading MODBUS config")

    try:
        _adc_config = json.loads(cfg.get("_MEAS_ADC"))
    except Exception as e:
        logging.exception(e, "Error loading ADC config")

    try:
        _pulse_counter_config = json.loads(cfg.get("_MEAS_PULSECOUNTER"))
    except Exception as e:
        logging.exception(e, "Error loading Pulse Counter config")


def shield_measurements(measurements):
    initialize_configurations()

    enable_regulator()

    if not io_expander_init():
        logging.debug("io expander can not be initialized, aborting shiled measurements")
        return

    try:
        execute_sdi12_measurements(measurements)
    except:
        pass

    execute_modbus_measurements(measurements)

    execute_adc_measurements(measurements)

    execute_pulse_counter_measurements(measurements)

    _deinitialize_i2c()

    # power off SDI12 regulator
    disable_regulator()


##### SDI12 functions #####


# {"sensors":[{"sensorAddress":1,"measCmd":"M","measSubCmd":""}],"warmupTime":1000}
def execute_sdi12_measurements(measurements):
    sensor_list = _get(_sdi12_config, "sensors")

    if not sensor_list or len(sensor_list) == 0:
        logging.error("No sensors found in SDI12 config")
        return

    _exec_i2c_op(io_expander_power_on_sdi12_sensors)

    logging.info("Starting SDI12 measurements")

    config = _get(_sdi12_config, "config")
    if not config:
        logging.error("No config found in SDI12 config")
        return

    if _has(config, "warmupTimeMs"):
        t = _get(config, "warmupTimeMs")
        logging.debug("SDI12 warmup time: {}".format(t))
        try:
            t = int(t)
            sleep_ms(t)
        except Exception as e:
            logging.exception(e, "Error during SDI12 warmup time")

    from external.microsdi12.microsdi12 import SDI12

    sdi12 = None

    try:
        sdi12 = SDI12(cfg.get("_UC_IO_DRV_IN"), cfg.get("_UC_IO_RCV_OUT"), None, 1)
        sdi12.set_dual_direction_pins(cfg.get("_UC_IO_DRV_ON"), cfg.get("_UC_IO_RCV_ON"), 1, 1, 1, 1)
        # for 'v3-alpha-v2.6.12-sp34'
        # sdi12.set_dual_direction_pins(cfg.get("_UC_IO_DRV_ON"), cfg.get("_UC_IO_RCV_ON"))
        sdi12.set_wait_after_uart_write(True)
        sdi12.wait_after_each_send(500)

        for sensor in sensor_list:
            read_sdi12_sensor(sdi12, measurements, sensor)
            sleep_ms(2500)
    except Exception as e:
        set_value(measurements, "sdi12_e", "{}".format(e), None)
        logging.exception(e, "Exception while reading SDI-12 data")

    if sdi12:
        sdi12.close()

    _exec_i2c_op(io_expander_power_off_sdi12_sensors)


def read_sdi12_sensor(sdi12, measurements, sensor):
    address = str(_get(sensor, "address"))
    command = str(_get(sensor, "measCmd"))
    sub_cmd = str(_get(sensor, "measSubCmd"))

    # sdi12.set_wait_after_uart_write(False)

    logging.debug("read_sdi12_sensor - address: {}, command: {}, sub_cmd: {}".format(address, command, sub_cmd))

    try:
        is_active = False

        for i in range(0, 3):
            is_active = sdi12.is_active(address)
            if is_active:
                break

        if not is_active:
            set_value(measurements, "sdi12_{}_e".format(address), "not_found", None)
            logging.error("read_sdi12_sensor - No sensor found in address: [" + str(address) + "]")
            return

        manufacturer, model = sdi12.get_sensor_info(address)
        manufacturer = manufacturer.lower()
        model = model.lower()
        logging.debug("manufacturer: {}, model: {}".format(manufacturer, model))

        command_to_execute = command + sub_cmd
        force_wait = True if manufacturer == "in-situ" and (model == "at500" or model == "at400") else False
        responseArray = sdi12.get_measurement(address, command_to_execute, 1, force_wait)
        if not responseArray:
            set_value(measurements, "sdi12_{}_e".format(address), "no_response", None)
            logging.error("read_sdi12_sensor - No response from sensor in address: [" + str(address) + "]")
            return

        parse_sdi12_sensor_response_array(manufacturer, model, address, command_to_execute, responseArray, measurements)

        # post-parse actions
        if "li-cor" in manufacturer and command_to_execute == "M0":
            sdi12._send(address + "XT!")  # trigger next round of measurements

    except Exception as e:
        set_value(measurements, "sdi12_{}_e".format(address), "{}".format(e), None)
        logging.exception(e, "Exception while reading SDI-12 data for address: {}".format(address))
        return


def parse_sdi12_sensor_response_array(manufacturer, model, address, command_to_execute, responseArray, measurements):
    location = "1"
    set_value(measurements, "sdi12_{}_i".format(address), manufacturer, None)
    set_value(measurements, "sdi12_{}_m".format(address), model, None)

    if manufacturer == "meter":
        parse_sensor_meter(model, command_to_execute, address, responseArray, measurements, location)
    elif manufacturer == "in-situ" and (model == "at500" or model == "at400"):
        parse_generic_sdi12(address, responseArray, measurements, "sdi12", None, "", location)
    elif manufacturer == "acclima" and command_to_execute == "M":
        parse_sensor_acclima(model, command_to_execute, address, responseArray, measurements, location)
    elif manufacturer == "implexx" and command_to_execute == "M":
        parse_sensor_implexx(model, command_to_execute, address, responseArray, measurements, location)
    elif manufacturer == "ep100g":
        if command_to_execute == "C":  # EnviroPro
            parse_generic_sdi12(address, responseArray, measurements, "ep_vwc", SenmlSecondaryUnits.SENML_SEC_UNIT_PERCENT, "", location)
        elif command_to_execute == "C1":  # EnviroPro
            parse_generic_sdi12(address, responseArray, measurements, "ep_ec", "uS/cm", "", location)  # dS/m

        elif command_to_execute == "C2":  # EnviroPro
            parse_generic_sdi12(address, responseArray, measurements, "ep_temp", SenmlUnits.SENML_UNIT_DEGREES_CELSIUS, "", location)
        elif command_to_execute == "C5":
            parse_generic_sdi12(
                address, responseArray, measurements, "ep_temp", SenmlSecondaryUnits.SENML_SEC_UNIT_FAHRENHEIT, "", location
            )

    elif "li-cor" in manufacturer and command_to_execute == "M0":
        parse_sensor_licor(model, command_to_execute, address, responseArray, measurements, location)
    else:
        parse_generic_sdi12(address, responseArray, measurements, "sdi12", None, "_" + command_to_execute.lower(), location)


#### Modbus functions #####


# [{"slaveAddress":0,"register":0,"type":3,"format":"uint16","factor":1,"decimalDigits":0,"mswFirst":true,"littleEndian":false}]
def execute_modbus_measurements(measurements):

    if not _modbus_config:
        logging.error("No modbus config")
        return

    sensor_list = _get(_modbus_config, "sensors")
    if not sensor_list or len(sensor_list) == 0:
        logging.error("No sensors found in modbus config")
        return

    connectionSettings = _get(_modbus_config, "config")

    logging.info("Starting modbus measurements")

    from machine import Pin

    _exec_i2c_op(io_expander_power_on_modbus)

    # need to set the SHDN pin to HIGH for not shutdown
    gpio_handler.set_pin_value(cfg.get("_UC_IO_MODBUS_DRV_ON"), 1)
    gpio_handler.set_pin_value(cfg.get("_UC_IO_MODBUS_RCV_ON"), 1)

    modbus = None

    try:
        rtu_pins = (cfg.get("_UC_IO_MODBUS_DRV_IN"), cfg.get("_UC_IO_MODBUS_RCV_OUT"))  # (TX, RX)
        baudrate = _get(connectionSettings, "baudRate")  # optional, default 9600
        data_bits = _get(connectionSettings, "dataBits")  # optional, default 8
        stop_bits = _get(connectionSettings, "stopBits")  # optional, default 1
        parity = _get(connectionSettings, "parity")  # optional, default None

        logging.debug("baud: {}".format(baudrate))
        logging.debug("dataBits: {}".format(data_bits))
        logging.debug("parity: {}".format(parity))
        logging.debug("stopBits: {}".format(stop_bits))
        logging.debug("rtu_pins: {}".format(rtu_pins))

        from apps.demo_console import modbus

        inst = modbus.init_instance(rtu_pins, baudrate, data_bits, parity, stop_bits)

        sleep_ms(5000)  # cfg.get("_SDI12_WARM_UP_TIME_MSEC"))  # warmup time

        for sensor in sensor_list:
            read_modbus_sensor(modbus, measurements, sensor)

        inst._uart.deinit()
        modbus.modbus_instance = None

    except Exception as e:
        logging.exception(e, "Exception while reading MODBUS data")

    gpio_handler.set_pin_value(cfg.get("_UC_IO_MODBUS_DRV_ON"), 0)

    _exec_i2c_op(io_expander_power_off_modbus)


def read_modbus_sensor(modbus, measurements, sensor):
    slave_address = _get(sensor, "slaveAddress")
    register = _get(sensor, "register")
    type = _get(sensor, "type")
    format = _get(sensor, "format")
    factor = _get(sensor, "factor")
    decimal_digits = _get(sensor, "decimalDigits")
    msw_first = _get(sensor, "mswFirst")
    little_endian = _get(sensor, "littleEndian")

    if slave_address is None or register is None or not type or not format:
        logging.error("Invalid modbus sensor configuration: {}".format(sensor))
        return

    try:
        response = []

        number_of_registers = _get(_modbus_reg_quantity_per_format, format)
        if number_of_registers is None:
            logging.error("Unsupported MODBUS format: {}".format(format))
            number_of_registers = 1

        response = modbus.send_modbus_read(type, slave_address, register, number_of_registers, False)

        if not response:
            logging.error("read_modbus_sensor - No response from sensor in address: [" + str(slave_address) + "]")
            return

        # Parse the response based on the type and format
        value = parse_modbus_response(response, format, factor, decimal_digits, msw_first, little_endian)

        # Set the value in the measurements dictionary
        set_value(
            measurements,
            "modbus_{}_{}{}".format(
                slave_address, register, get_modbus_naming_postfix(format, factor, decimal_digits, msw_first, little_endian)
            ),
            value,
        )

    except Exception as e:
        logging.exception(e, "Exception while reading MODBUS data for address: {}".format(slave_address))
        return


def get_modbus_naming_postfix(format, factor, decimal_digits, msw_first, little_endian):
    # Generate a unique naming postfix based on the parameters
    postfix = ""

    if format:
        postfix += "_{}".format(format)

    if factor is not None:
        postfix += "_f{}".format(factor)

    if decimal_digits is not None:
        postfix += "_d{}".format(decimal_digits)

    if msw_first is not None:
        postfix += "_msw{}".format(1 if msw_first else 0)

    if little_endian is not None:
        postfix += "_le{}".format(1 if little_endian else 0)

    return postfix


def parse_modbus_response(response, format, factor, decimal_digits, msw_first, little_endian):
    # Implement the parsing logic based on the type and format
    # This is a placeholder implementation, you need to adjust it based on your requirements

    if not msw_first and len(response) > 1:
        response = [response[1], response[0]]

    # response array elements contain a 16-bit value, split each element into 2 bytes
    response_bytes = bytearray()
    for value in response:
        response_bytes.append((value >> 8) & 0xFF)
        response_bytes.append(value & 0xFF)

    import struct

    struct_endianess = "<" if little_endian else ">"

    struct_format = _get(_modbus_struct_format_options, format)

    if struct_format is None:
        logging.error("Unsupported MODBUS format: {}".format(format))
        return None

    value = struct.unpack(struct_endianess + struct_format, response_bytes)[0]

    # Apply factor and decimal digits
    if factor is not None:
        value = value * factor

    if decimal_digits is not None:
        if decimal_digits < 0:
            logging.error("Invalid decimal digits: {}".format(decimal_digits))
            return None
        if decimal_digits > 0:
            value = round(value, decimal_digits)
        else:
            value = int(value)
    return value


#### ADC functions #####


# [{"id":1,"enabled":false,"formula":"v"},{"id":2,"enabled":false,"formula":"v"},{"id":3,"enabled":true,"formula":"v"},{"id":4,"enabled":false,"formula":"v"}]
def execute_adc_measurements(measurements):
    if not _adc_config or len(_adc_config) == 0:
        logging.error("No sensors found in ADS config")
        return

    logging.info("Starting ADC measurements")

    has_enabled_sensor = False
    for sensor in _adc_config:
        if _get(sensor, "enabled"):
            has_enabled_sensor = True
            break

    if not has_enabled_sensor:
        logging.error("No enabled sensors found in ADS config")
        return

    _exec_i2c_op(ads_init)

    _exec_i2c_op(io_expander_power_on_ads_sensors)

    try:
        for sensor in _adc_config:
            read_adc_sensor(measurements, sensor)
    except Exception as e:
        logging.exception(e, "Exception while reading ADS data")

    _exec_i2c_op(io_expander_power_off_adc_sensors)


def read_adc_sensor(measurements, sensor):
    channel = _get(sensor, "id")
    enabled = _get(sensor, "enabled")
    formula = _get(sensor, "formula")
    gain = _get(sensor, "gain")

    if not enabled:
        return

    if channel is None or channel < 1 or channel > 4:
        logging.error("read_adc_sensor - Invalid channel: {}".format(channel))
        return

    from external.ads1x15.ads1x15 import ADS1115

    _initialize_i2c()

    adc = ADS1115(_i2c, address=_ads_addr, gain=gain)

    volt_analog = 1000 * adc.raw_to_v(adc.read(_ads_rate, channel - 1))
    meas_name = "adc_{}".format(channel)
    set_value_float(
        measurements,
        meas_name + "_raw",
        volt_analog,
        SenmlSecondaryUnits.SENML_SEC_UNIT_MILLIVOLT,
    )

    default_formula = "v"
    if formula is not None and formula != default_formula:
        execute_formula(measurements, meas_name, volt_analog, formula)

    _deinitialize_i2c()


#### Pulse Counter functions #####


# [{"id":1,"enabled":false,"formula":"v","highFreq":false},{"id":2,"enabled":false,"formula":"v","highFreq":false}]
def execute_pulse_counter_measurements(measurements):
    global _pulse_counter_thread_started
    global pcnt_last_run_timestamp_ms
    global pcnt_1_edge_count
    global pcnt_2_edge_count
    global _thread_lock
    global pcnt_1_debounce_timer
    global pcnt_2_debounce_timer
    global pcnt_1_pending_edge
    global pcnt_2_pending_edge
    global pcnt_1_filtered_edges
    global pcnt_2_filtered_edges

    logging.info("Starting Pulse Counter measurements")

    if not _pulse_counter_config or len(_pulse_counter_config) == 0:
        logging.error("No sensors found in ADS config")
        return

    has_enabled_sensor = False
    for sensor in _pulse_counter_config:
        if _get(sensor, "enabled"):
            has_enabled_sensor = True
            break

    if not has_enabled_sensor:
        logging.error("No enabled sensors found in Pulse Counter config")
        logging.debug("cfg: {}".format(cfg.get("_MEAS_PULSECOUNTER")))
        logging.debug("cfg: {}".format(_pulse_counter_config))

        import utils

        TIMESTAMP_FLAG_FILE = "/pcnt_last_read_timestamp"
        utils.deleteFlagFile(TIMESTAMP_FLAG_FILE)
        return

    for sensor in _pulse_counter_config:
        sensor["gpio"] = cfg.get("UC_IO_DGTL_SNSR_{}_READ".format(_get(sensor, "id")))

    if not cfg.get("_LIGHT_SLEEP_ON"):
        from . import scenario_pcnt_ulp

        scenario_pcnt_ulp.execute(measurements, _pulse_counter_config)
        return

    pcnt_method_1 = _pulse_counter_config[0].get("method") if _pulse_counter_config and len(_pulse_counter_config) > 0 else "interrupt"
    pcnt_method_2 = _pulse_counter_config[1].get("method") if _pulse_counter_config and len(_pulse_counter_config) > 1 else "interrupt"

    if _pulse_counter_thread_started is None:

        _pulse_counter_thread_started = True

        if pcnt_method_1 != "adc" and pcnt_method_2 != "adc":
            from machine import Pin

            def pcnt_1_timer_callback(timer):
                global pcnt_1_edge_count, pcnt_1_pending_edge
                # if pcnt_1_pending_edge:
                #     with _thread_lock:
                pcnt_1_edge_count += 1
                pcnt_1_pending_edge = False

            def pcnt_2_timer_callback(timer):
                global pcnt_2_edge_count, pcnt_2_pending_edge
                #if pcnt_2_pending_edge:
                #with _thread_lock:
                pcnt_2_edge_count += 1
                pcnt_2_pending_edge = False
                print("edge counted")

            def pcnt_1_interrupt(pin):
                global pcnt_1_debounce_timer, pcnt_1_pending_edge, pcnt_1_filtered_edges

                if pcnt_1_pending_edge:
                    # Already have a pending edge, this is noise/bounce
                    #with _thread_lock:
                    pcnt_1_filtered_edges += 1
                    # Reset the timer to extend the debounce period
                else:
                    # First edge detected, start debounce timer
                    pcnt_1_pending_edge = True
                #pcnt_1_debounce_timer.deinit()
                pcnt_1_debounce_timer.init(mode=Timer.ONE_SHOT, period=DEBOUNCE_TIME_MS, callback=pcnt_1_timer_callback)

            def pcnt_2_interrupt(pin):
                global pcnt_2_debounce_timer, pcnt_2_pending_edge, pcnt_2_filtered_edges

                if pcnt_2_pending_edge:
                    # Already have a pending edge, this is noise/bounce
                    #with _thread_lock:
                    pcnt_2_filtered_edges += 1
                    print("edge filtered")
                else:
                    # First edge detected, start debounce timer
                    pcnt_2_pending_edge = True
                    print("edge pending")

                #pcnt_2_debounce_timer.deinit()
                pcnt_2_debounce_timer.init(mode=Timer.ONE_SHOT, period=DEBOUNCE_TIME_MS, callback=pcnt_2_timer_callback)

            pcnt_1_enabled = _pulse_counter_config[0].get("enabled")
            pcnt_1_gpio = _pulse_counter_config[0].get("gpio")
            pcnt_2_enabled = _pulse_counter_config[1].get("enabled")
            pcnt_2_gpio = _pulse_counter_config[1].get("gpio")

            if pcnt_1_enabled and pcnt_1_gpio:
                pin1 = Pin(pcnt_1_gpio, Pin.IN)
                pin1.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=pcnt_1_interrupt)

            if pcnt_2_enabled and pcnt_2_gpio:
                pin2 = Pin(pcnt_2_gpio, Pin.IN)
                pin2.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=pcnt_2_interrupt)

        pcnt_last_run_timestamp_ms = utime.ticks_ms()

        for sensor in _pulse_counter_config:
            if _get(sensor, "enabled"):
                id = sensor.get("id")
                set_value_float(measurements, "pcnt_count_{}".format(id), 0, SenmlUnits.SENML_UNIT_COUNTER)
                set_value_int(measurements, "pcnt_edge_count_{}".format(id), 0, SenmlUnits.SENML_UNIT_COUNTER)
                set_value_float(measurements, "pcnt_period_s_{}".format(id), 0, SenmlUnits.SENML_UNIT_SECOND)
                set_value_float(measurements, "pcnt_count_formula_{}".format(id), 0)
                # Add filtered edge count for debugging
                if cfg.get("_MEAS_BOARD_STAT_ENABLE"):
                    set_value_int(measurements, "pcnt_filtered_edges_{}".format(id), 0, SenmlUnits.SENML_UNIT_COUNTER)
    else:
        time_diff = -1
        pcnt_1_val = 0
        pcnt_2_val = 0

        if pcnt_method_1 != "adc" and pcnt_method_2 != "adc":
            time_diff = (utime.ticks_ms() - pcnt_last_run_timestamp_ms) / 1000.0  # in seconds
            pcnt_last_run_timestamp_ms = utime.ticks_ms()
        else:
            time_diff = (pcnt_last_run_pause_timestamp_ms - pcnt_last_run_start_timestamp_ms) / 1000.0  # in seconds

        with _thread_lock:
            pcnt_1_val = pcnt_1_edge_count
            pcnt_1_edge_count = 0
            pcnt_1_filtered = pcnt_1_filtered_edges
            pcnt_1_filtered_edges = 0

        with _thread_lock:
            pcnt_2_val = pcnt_2_edge_count
            pcnt_2_edge_count = 0
            pcnt_2_filtered = pcnt_2_filtered_edges
            pcnt_2_filtered_edges = 0

        for sensor in _pulse_counter_config:
            if _get(sensor, "enabled"):
                id = sensor.get("id")
                filtered_count = pcnt_1_filtered if id == 1 else pcnt_2_filtered
                store_pulse_counter_measurements(
                    measurements,
                    id,
                    pcnt_1_val if id == 1 else pcnt_2_val,
                    time_diff,
                    _get(sensor, "formula"),
                    pcnt_unstable_readings_1 if id == 1 else pcnt_unstable_readings_2,
                    pcnt_readings_1 if id == 1 else pcnt_readings_2,
                    filtered_count,
                    pcnt_method_1 if id == 1 else pcnt_method_2,
                )


def store_pulse_counter_measurements(
    measurements, id, edge_cnt, time_diff_from_prev, formula, invalid_readings_cnt, readings_cnt, filtered_edges_cnt, method=None
):
    pulse_cnt = ceil(edge_cnt / 2)

    set_value_float(measurements, "pcnt_count_{}".format(id), pulse_cnt, SenmlUnits.SENML_UNIT_COUNTER)
    set_value_int(measurements, "pcnt_edge_count_{}".format(id), edge_cnt, SenmlUnits.SENML_UNIT_COUNTER)
    set_value_float(measurements, "pcnt_period_s_{}".format(id), time_diff_from_prev, SenmlUnits.SENML_UNIT_SECOND, 3)

    if cfg.get("_MEAS_BOARD_STAT_ENABLE"):

        if method == "adc":
            set_value_int(measurements, "pcnt_unstable_readings_{}".format(id), invalid_readings_cnt, SenmlUnits.SENML_UNIT_COUNTER)
            set_value_int(measurements, "pcnt_readings_{}".format(id), readings_cnt, SenmlUnits.SENML_UNIT_COUNTER)
            try:
                set_value_float(
                    measurements,
                    "pcnt_voltage_min_{}".format(id),
                    (pcnt_voltage_min_1 if id == 1 else pcnt_voltage_min_2) / 1000.0,
                    SenmlUnits.SENML_UNIT_VOLT,
                )
            except Exception as e:
                logging.error("Error setting pcnt_voltage_min_{}: {}".format(id, e))
            try:
                set_value_float(
                    measurements,
                    "pcnt_voltage_max_{}".format(id),
                    (pcnt_voltage_max_1 if id == 1 else pcnt_voltage_max_2) / 1000.0,
                    SenmlUnits.SENML_UNIT_VOLT,
                )
            except Exception as e:
                logging.error("Error setting pcnt_voltage_max_{}: {}".format(id, e))
        else:
            set_value_int(measurements, "pcnt_filtered_edges_{}".format(id), filtered_edges_cnt, SenmlUnits.SENML_UNIT_COUNTER)

    calculated_value = 0

    # check if formula is just a number as multiplier
    if type(formula) == int or type(formula) == float:
        formula = "v*{}".format(formula)
    elif type(formula) == str:  # check if formula is a number stored as string
        try:
            float(formula)
            formula = "v*{}".format(formula)
        except:
            pass

    try:
        formula = formula.replace("v", str(pulse_cnt))
        to_execute = "v_transformed=({})".format(formula)
        namespace = {}
        exec(to_execute, namespace)
        calculated_value = namespace["v_transformed"]
        set_value_float(measurements, "pcnt_count_formula_{}".format(id), calculated_value, None, 4)
    except Exception as e:
        logging.exception(e, "formula name:{}, raw_value:{}, code:{}".format(id, pulse_cnt, formula))
        pass

    logging.debug("   ")
    logging.debug("================ pcnt {} =======================".format(id))
    logging.debug(
        "========= pcnt_count: {}, edge_cnt: {}, time_diff_from_prev: {}, calculated_value: {}, {} pulse/sec".format(
            pulse_cnt, edge_cnt, time_diff_from_prev, calculated_value, pulse_cnt / time_diff_from_prev if time_diff_from_prev > 0 else 0
        )
    )
    logging.debug("=============================================")


def pause_background_measurements():
    global _pcnt_active
    _pcnt_active = False


def resume_background_measurements(execution_period_ms=None):
    global _pcnt_active
    _pcnt_active = True
    start_counting_thread(execution_period_ms)


def start_counting_thread(execution_period_ms=None):
    global _pulse_counter_thread_started
    _thread.start_new_thread(pulse_counter_thread, ([_pulse_counter_config, execution_period_ms]))
    _pulse_counter_thread_started = True


def detect_stable_edge(adc_inst):
    cnt = 0
    while cnt < 1000:
        v = adc_inst.read_voltage(1)
        detected_edge = 1 if v > V_HIGH else 0 if v < V_LOW else None
        if detected_edge is not None:
            return detected_edge
        cnt += 1
        utime.sleep_us(50)
    return None


def pulse_counter_thread(config, execution_period_ms=None):
    global pcnt_1_edge_count
    global pcnt_2_edge_count
    global _pcnt_active
    global pcnt_last_run_start_timestamp_ms
    global pcnt_last_run_pause_timestamp_ms
    global pcnt_unstable_readings_1
    global pcnt_unstable_readings_2
    global pcnt_readings_1
    global pcnt_readings_2
    global _thread_lock
    global pcnt_voltage_min_1
    global pcnt_voltage_max_1
    global pcnt_voltage_min_2
    global pcnt_voltage_max_2

    pcnt_method_1 = config[0].get("method") if config and len(config) > 0 else "interrupt"
    pcnt_method_2 = config[1].get("method") if config and len(config) > 1 else "interrupt"

    if pcnt_method_1 != "adc" and pcnt_method_2 != "adc":
        logging.debug("Pulse counter thread not started, both methods are not 'adc'")
        return

    logging.debug("!!!!!!!!!!!!!!!!!!!!!! Starting pulse counter thread!")

    pcnt_1_enabled = config[0].get("enabled") if config and len(config) > 0 else False
    pcnt_1_gpio = config[0].get("gpio") if config and len(config) > 0 else False
    pcnt_1_high_freq = config[0].get("highFreq") if config and len(config) > 0 else False
    pcnt_2_enabled = config[1].get("enabled") if config and len(config) > 1 else False
    pcnt_2_gpio = config[1].get("gpio") if config and len(config) > 1 else False
    pcnt_2_high_freq = config[1].get("highFreq") if config and len(config) > 1 else False

    logging.debug(config)
    logging.debug("pcnt_1_enabled: {}, pcnt_1_gpio: {}, pcnt_1_high_freq: {}".format(pcnt_1_enabled, pcnt_1_gpio, pcnt_1_high_freq))
    logging.debug("pcnt_2_enabled: {}, pcnt_2_gpio: {}, pcnt_2_high_freq: {}".format(pcnt_2_enabled, pcnt_2_gpio, pcnt_2_high_freq))

    from machine import ADC, Pin

    pcnt_1_adc = None
    pcnt_2_adc = None

    if pcnt_1_enabled and pcnt_1_gpio is not None:
        adc = ADC(Pin(pcnt_1_gpio))
        adc.atten(ADC.ATTN_11DB)
        adc_width = ADC.WIDTH_12BIT
        adc.width(adc_width)
        pcnt_1_adc = adc
    if pcnt_2_enabled and pcnt_2_gpio is not None:
        adc = ADC(Pin(pcnt_2_gpio))
        adc.atten(ADC.ATTN_11DB)
        adc_width = ADC.WIDTH_12BIT
        adc.width(adc_width)
        pcnt_2_adc = adc

    with _thread_lock:
        pcnt_last_run_start_timestamp_ms = utime.ticks_ms()

    timeout_timestamp_ms = -1
    if execution_period_ms is not None:
        timeout_timestamp_ms = pcnt_last_run_start_timestamp_ms + execution_period_ms

    pcnt_1_next_edge = 1
    pcnt_1_edge_count = 0
    pcnt_1_previous_input_value = 0
    pcnt_1_sequential_stable_values_count = 0
    pcnt_1_sequential_stable_values_max = 5

    pcnt_2_next_edge = 1
    pcnt_2_edge_count = 0
    pcnt_2_previous_input_value = 0
    pcnt_2_sequential_stable_values_count = 0
    pcnt_2_sequential_stable_values_max = 5

    pcnt_unstable_readings_1 = 0
    pcnt_unstable_readings_2 = 0

    pcnt_readings_1 = 0
    pcnt_readings_2 = 0

    pcnt_1_previous_input_value = detect_stable_edge(pcnt_1_adc) if pcnt_1_adc is not None else 0
    pcnt_1_next_edge = 1 - pcnt_1_previous_input_value
    pcnt_voltage_min_1 = None
    pcnt_voltage_max_1 = None

    pcnt_2_previous_input_value = detect_stable_edge(pcnt_2_adc) if pcnt_2_adc is not None else 0
    pcnt_2_next_edge = 1 - pcnt_2_previous_input_value
    pcnt_voltage_min_2 = None
    pcnt_voltage_max_2 = None

    try:
        print(">>>> Started")
        while _pcnt_active:
            if timeout_timestamp_ms != -1 and utime.ticks_ms() >= timeout_timestamp_ms:
                logging.debug("Exiting thread due to timeout")
                break

            if pcnt_1_enabled and pcnt_1_adc is not None:
                v = pcnt_1_adc.read_voltage(1)

                if pcnt_voltage_min_1 is None or v < pcnt_voltage_min_1:
                    pcnt_voltage_min_1 = v
                if pcnt_voltage_max_1 is None or v > pcnt_voltage_max_1:
                    pcnt_voltage_max_1 = v

                edge_level = 1 if v > V_HIGH else 0 if v < V_LOW else None

                if edge_level is None:
                    edge_level = detect_stable_edge(pcnt_1_adc)

                pcnt_readings_1 += 1

                if edge_level is None or edge_level != pcnt_1_previous_input_value:
                    pcnt_unstable_readings_1 += 1
                    pcnt_1_sequential_stable_values_count = 0
                    pcnt_1_previous_input_value = edge_level

                else:
                    pcnt_1_previous_input_value = edge_level

                    if pcnt_1_sequential_stable_values_count >= pcnt_1_sequential_stable_values_max:
                        if edge_level == pcnt_1_next_edge:
                            with _thread_lock:
                                pcnt_1_edge_count += 1

                            pcnt_1_next_edge = 1 - pcnt_1_next_edge
                        else:
                            # stable level, waiting for change
                            pass
                    else:
                        pcnt_1_sequential_stable_values_count += 1

            if pcnt_2_enabled and pcnt_2_adc is not None:
                v = pcnt_2_adc.read_voltage(1)
                edge_level = 1 if v > V_HIGH else 0 if v < V_LOW else None

                if pcnt_voltage_min_2 is None or v < pcnt_voltage_min_2:
                    pcnt_voltage_min_2 = v
                if pcnt_voltage_max_2 is None or v > pcnt_voltage_max_2:
                    pcnt_voltage_max_2 = v

                if edge_level is None:
                    edge_level = detect_stable_edge(pcnt_2_adc)

                pcnt_readings_2 += 1

                if edge_level is None or edge_level != pcnt_2_previous_input_value:
                    pcnt_unstable_readings_2 += 1
                    pcnt_2_sequential_stable_values_count = 0
                    pcnt_2_previous_input_value = edge_level

                else:
                    pcnt_2_previous_input_value = edge_level

                    if pcnt_2_sequential_stable_values_count >= pcnt_2_sequential_stable_values_max:
                        if edge_level == pcnt_2_next_edge:
                            with _thread_lock:
                                pcnt_2_edge_count += 1

                            pcnt_2_next_edge = 1 - pcnt_2_next_edge
                        else:
                            # stable level, waiting for change
                            pass
                    else:
                        pcnt_2_sequential_stable_values_count += 1

            utime.sleep_us(5)
    except Exception as e:
        logging.exception(e, "pulse_counter_thread exception occurred")

    pcnt_last_run_pause_timestamp_ms = utime.ticks_ms()

    print(">>>> STOPPED")
    logging.debug("Pulse counting thread stopped!")


### Auxiliary functions ###
def execute_formula(measurements, name, raw_value, formula):
    try:
        formula = formula.replace("v", str(raw_value))
        to_execute = "v_transformed=({})".format(formula)
        namespace = {}
        exec(to_execute, namespace)
        print("namespace: " + str(namespace))
        set_value_float(measurements, name + "_formula", namespace["v_transformed"])
    except Exception as e:
        logging.exception(e, "formula name:{}, raw_value:{}, code:{}".format(name, raw_value, formula))
        pass
