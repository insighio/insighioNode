from utime import sleep_ms
from external.kpn_senml.senml_unit import SenmlUnits
from external.kpn_senml.senml_unit import SenmlSecondaryUnits
import logging
from sensors import set_sensor_power_on, set_sensor_power_off

from .dictionary_utils import set_value, set_value_float, _get, _has

from .sdi12_response_parsers import parse_sensor_meter, parse_sensor_acclima, parse_sensor_implexx, parse_sensor_licor, parse_generic_sdi12

from . import cfg

_i2c = None
_io_expander_addr = None

_ads_addr = None
_ads_rate = None

_sdi12_config = {}
_modbus_config = {}
_adc_config = {}
_pulse_counter_config = {}

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


def io_expander_init():
    global _io_expander_addr
    _io_expander_addr = cfg.get("_UC_IO_EXPANDER_ADDR")

    initialized = _initialize_i2c()
    if not initialized:
        return False

    # set all output pins to LOW
    power_off_all_sensors()

    # set all ports as output except P3 which is input
    # and has UC_IO_XTNDR_ADC_ALERT_RDY
    _i2c.writeto_mem(_io_expander_addr, 3, b"\xf8")

    return True


def ads_init():
    global _ads_addr
    global _ads_rate
    _ads_addr = cfg.get("_UC_IO_ADS_ADDR")
    _ads_rate = cfg.get("_ADS_RATE")
    return _initialize_i2c()


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

    execute_sdi12_measurements(measurements)

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

    io_expander_power_on_sdi12_sensors()

    logging.info("Starting SDI12 measurements")

    config = _get(_sdi12_config, "config")
    if not config:
        logging.error("No config found in SDI12 config")
        return

    if _has(config, "warmupTimeMs"):
        t = _get(config, "warmupTimeMs")
        logging.debug("SDI12 warmup time: {}".format(t))
        sleep_ms(t)

    from external.microsdi12.microsdi12 import SDI12

    sdi12 = None

    try:
        sdi12 = SDI12(cfg.get("_UC_IO_DRV_IN"), cfg.get("_UC_IO_RCV_OUT"), None, 1)
        sdi12.set_dual_direction_pins(cfg.get("_UC_IO_DRV_ON"), cfg.get("_UC_IO_RCV_ON"), 1, 1, 1, 0)
        sdi12.set_wait_after_uart_write(True)
        sdi12.wait_after_each_send(500)

        for sensor in sensor_list:
            read_sdi12_sensor(sdi12, measurements, sensor)
    except Exception as e:
        logging.exception(e, "Exception while reading SDI-12 data")

    if sdi12:
        sdi12.close()

    io_expander_power_off_sdi12_sensors()


def read_sdi12_sensor(sdi12, measurements, sensor):
    address = str(_get(sensor, "address"))
    command = _get(sensor, "measCmd")
    sub_cmd = _get(sensor, "measSubCmd")

    logging.debug("read_sdi12_sensor - address: {}, command: {}, sub_cmd: {}".format(address, command, sub_cmd))

    try:
        if not sdi12.is_active(address):
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
            logging.error("read_sdi12_sensor - No response from sensor in address: [" + str(address) + "]")
            return

        parse_sdi12_sensor_response_array(manufacturer, model, address, command_to_execute, responseArray, measurements)

        # post-parse actions
        if "li-cor" in manufacturer and command_to_execute == "M0":
            sdi12._send(address + "XT!")  # trigger next round of measurements

    except Exception as e:
        logging.exception(e, "Exception while reading SDI-12 data for address: {}".format(address))
        return


def parse_sdi12_sensor_response_array(manufacturer, model, address, command_to_execute, responseArray, measurements):
    location = "1"
    set_value(measurements, "sdi12_{}_i".format(address), manufacturer, None)
    set_value(measurements, "sdi12_{}_m".format(address), model, None)

    if manufacturer == "meter" and "at41g2" not in model and command_to_execute == "M":
        parse_sensor_meter(model, address, responseArray, measurements, location)
    elif manufacturer == "in-situ" and (model == "at500" or model == "at400") and command_to_execute == "M":
        parse_generic_sdi12(address, responseArray, measurements, "sdi12", None, "", location)
    elif manufacturer == "acclima" and command_to_execute == "M":
        parse_sensor_acclima(address, responseArray, measurements, location)
    elif manufacturer == "implexx" and command_to_execute == "M":
        parse_sensor_implexx(address, responseArray, measurements, location)
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
        parse_sensor_licor(address, responseArray, measurements, location)
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

    # need to set the SHDN pin to HIGH for not shutdown
    pin_SHDN = Pin(cfg.get("_UC_IO_MODBUS_DRV_ON"), Pin.OUT)
    pin_SHDN.value(1)

    io_expander_power_on_modbus()

    modbus = None

    try:
        from external.umodbus.serial import Serial as ModbusRTUMaster

        rtu_pins = (cfg.get("_UC_IO_MODBUS_DRV_IN"), cfg.get("_UC_IO_MODBUS_RCV_OUT"))  # (TX, RX)

        config_parity = _get(connectionSettings, "parity")
        if not config_parity:
            config_parity = None

        modbus = ModbusRTUMaster(
            pins=rtu_pins,  # given as tuple (TX, RX)
            baudrate=_get(connectionSettings, "baudRate"),  # optional, default 9600
            data_bits=_get(connectionSettings, "dataBits"),  # optional, default 8
            stop_bits=_get(connectionSettings, "stopBits"),  # optional, default 1``
            parity=config_parity,  # optional, default None
            # ctrl_pin=12,          # optional, control DE/RE
            # uart_id= 1              # optional, default 1, see port specific documentation
        )

        for sensor in sensor_list:
            read_modbus_sensor(modbus, measurements, sensor)
    except Exception as e:
        logging.exception(e, "Exception while reading MODBUS data")

    io_expander_power_off_modbus()


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

        number_of_registers = _modbus_reg_quantity_per_format.get(format)
        if number_of_registers is None:
            logging.error("Unsupported MODBUS format: {}".format(format))
            number_of_registers = 1

        if type == 3:
            logging.debug("[read_modbus_sensor]-[read_holding_registers]: id: {}, register_addr: {}".format(slave_address, register))
            response = modbus.read_holding_registers(slave_address, register, number_of_registers)
            logging.debug("  <= {}".format(response))

        elif type == 4:
            logging.debug("[read_modbus_sensor]-[read_input_registers]: id: {}, register_addr: {}".format(slave_address, register))
            response = modbus.read_input_registers(slave_address, register, number_of_registers)
            logging.debug("  <= {}".format(response))
        else:
            logging.error("Unsupported MODBUS type: {}".format(type))
            return

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

    struct_format = _modbus_struct_format_options.get(format)

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
        if sensor.get("enabled") == 1:
            has_enabled_sensor = True
            break

    if not has_enabled_sensor:
        logging.error("No enabled sensors found in ADS config")
        return

    ads_init()

    io_expander_power_on_ads_sensors()

    try:
        for sensor in _adc_config:
            read_adc_sensor(measurements, sensor)
    except Exception as e:
        logging.exception(e, "Exception while reading ADS data")

    io_expander_power_off_adc_sensors()


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
        execute_transformation(measurements, meas_name, volt_analog, formula)


#### Pulse Counter functions #####


# [{"id":1,"enabled":false,"formula":"v","highFreq":false,"enable":true},{"id":2,"enabled":false,"formula":"v","highFreq":false}]
def execute_pulse_counter_measurements(measurements):
    logging.info("Starting Pulse Counter measurements")
    pass


### Auxiliary functions ###
def execute_transformation(measurements, name, raw_value, transformator):
    try:
        transformator = transformator.replace("v", str(raw_value))
        to_execute = "v_transformed=({})".format(transformator)
        namespace = {}
        exec(to_execute, namespace)
        print("namespace: " + str(namespace))
        set_value(measurements, name + "_formula", namespace["v_transformed"])
    except Exception as e:
        logging.exception(e, "formula name:{}, raw_value:{}, code:{}".format(name, raw_value, transformator))
        pass
