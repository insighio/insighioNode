from utime import sleep_ms

from external.kpn_senml.senml_unit import SenmlSecondaryUnits
import logging
from sensors import set_sensor_power_on, set_sensor_power_off
from device_info import wdt_reset

from .dictionary_utils import set_value, set_value_float
from .sdi12_measurements import detect_timing, identify_sensor, read_measurement, set_no_response_error


from . import cfg

_BOARD_DEBUG_ON = cfg.get("_MEAS_BOARD_STAT_ENABLE")

_sdi12_sensor_switch_list = []


def populateSDI12SensorSwitchList():
    global _sdi12_sensor_switch_list
    _sdi12_sensor_switch_list = [None] * 11

    for i in range(1, 11):
        pwr_on = cfg.get("_UC_IO_PWR_SDI_SNSR_" + str(i) + "_ON")
        if pwr_on is None:
            pwr_on = cfg.get("_UC_IO_SNSR_GND_SDI_SNSR_" + str(i) + "_ON")
        _sdi12_sensor_switch_list[i] = pwr_on


populateSDI12SensorSwitchList()


def powerOnAllSwitchExcept(excludedIndex=None):
    for i in range(1, 11):
        if excludedIndex == i or _sdi12_sensor_switch_list[i] is None:
            continue
        set_sensor_power_on(_sdi12_sensor_switch_list[i])


def powerOffAllSwitchExcept(excludedIndex=None):
    for i in range(1, 11):
        if excludedIndex == i or _sdi12_sensor_switch_list[i] is None:
            continue
        set_sensor_power_off(_sdi12_sensor_switch_list[i])


def executeSDI12Measurement(sdi12, measurements, index):
    enabled = cfg.get("_SDI12_SENSOR_" + str(index) + "_ENABLED")
    address = cfg.get("_SDI12_SENSOR_" + str(index) + "_ADDRESS")
    location = cfg.get("_SDI12_SENSOR_" + str(index) + "_LOCATION")

    if not enabled:
        logging.debug("sdi12 sensor [{}] enabled: {}".format(index, enabled))
        return

    if location is None:
        if index == 1 or index == 2:  # backward compatibility
            location = index
    else:
        try:
            location = int(location)
        except:
            pass

    if _sdi12_sensor_switch_list[location] is not None:
        set_sensor_power_on(_sdi12_sensor_switch_list[location])
    powerOffAllSwitchExcept(location)
    sleep_ms(cfg.get("_SDI12_WARM_UP_TIME_MSEC"))
    try:
        read_sdi12_sensor(sdi12, address, measurements, location)
    except Exception as e:
        set_value(measurements, "sdi12_{}_e".format(address), "{}".format(e), None)
        logging.exception(e, "Exception while reading SDI-12 sensor at address: {}".format(address))
    powerOffAllSwitchExcept()


def shield_measurements(measurements):
    # power on SDI12 regulator
    set_sensor_power_on(cfg.get("_UC_IO_SNSR_REG_ON"))

    # get SDI12 measurements
    sleep_ms(cfg.get("_SDI12_WARM_UP_TIME_MSEC"))

    from external.microsdi12.microsdi12 import SDI12

    sdi12 = None

    try:
        sdi12 = SDI12(cfg.get("_UC_IO_DRV_IN"), cfg.get("_UC_IO_RCV_OUT"), None, 1)
        sdi12.set_dual_direction_pins(cfg.get("_UC_IO_DRV_ON"), cfg.get("_UC_IO_RCV_ON"))
        sdi12.set_wait_after_uart_write(True)
        sdi12.wait_after_each_send(500)
        # sdi12._BREAK_MULTIPLIER = 1.55
        # sdi12._MARK_MULTIPLIER = 1.15

        for i in range(1, 11):
            executeSDI12Measurement(sdi12, measurements, i)
    except Exception as e:
        logging.exception(e, "Exception while reading SDI-12 data")
    if sdi12:
        sdi12.close()

    # get 4-20mA measurements
    try:
        current_sense_4_20mA(measurements)
    except Exception as e:
        logging.exception(e, "Exception while reading 4_20mA data")

    read_pulse_counter(measurements)

    # power off SDI12 regulator
    set_sensor_power_off(cfg.get("_UC_IO_SNSR_REG_ON"))


def read_sdi12_sensor(sdi12, address, measurements, location=None):
    logging.debug("Reading sensor with address: {}".format(address))

    timing_detected, _, timing = detect_timing(sdi12, [str(address)], 0, wdt_reset)
    if timing_detected:
        if _BOARD_DEBUG_ON:
            set_value(measurements, "sdi12_{}_t".format(address), "{}".format(list(timing)), None)
    else:
        logging.error("Could not detect SDI-12 timing for sensor at address: [{}]".format(address))
        return

    is_active, manufacturer, model = identify_sensor(sdi12, address, measurements)
    if not is_active:
        return

    logging.debug("manufacturer: {}, model: {}".format(manufacturer, model))
    response = None

    if manufacturer == "meter" and (model == "ter12" or model == "atm14"):
        response = read_measurement(sdi12, measurements, address, manufacturer, model, "M", location)
    elif manufacturer == "meter" and (model == "at41g2" or model == "atm41"):
        response = read_measurement(sdi12, measurements, address, manufacturer, model, "C", location, measurement_count=2)
    elif manufacturer == "in-situ" and (model == "at500" or model == "at400"):
        response = read_measurement(sdi12, measurements, address, manufacturer, model, "C", location)
    elif manufacturer == "acclima":
        response = read_measurement(sdi12, measurements, address, manufacturer, model, "M", location)
    elif manufacturer == "implexx":
        response = read_measurement(sdi12, measurements, address, manufacturer, model, "M", location)
    elif manufacturer == "ep100g":  # EnviroPro
        response = read_measurement(sdi12, measurements, address, manufacturer, model, "C", location)
        response = read_measurement(sdi12, measurements, address, manufacturer, model, "C1", location) or response

        cfg_is_celsius = cfg.get("_MEAS_TEMP_UNIT_IS_CELSIUS")
        if cfg_is_celsius:
            temperature_response = read_measurement(sdi12, measurements, address, manufacturer, model, "C2", location)
        else:
            temperature_response = read_measurement(sdi12, measurements, address, manufacturer, model, "C5", location)
        response = temperature_response or response
    elif "li-cor" in manufacturer:
        response = read_measurement(sdi12, measurements, address, manufacturer, model, "M0", location)
        sdi12._send(address + "XT!")  # trigger next round of measurements
    elif "rika" in manufacturer or ("kisters_" in manufacturer and model == "hyquan"):
        response = read_measurement(sdi12, measurements, address, manufacturer, model, "M", location)
    else:
        response = read_measurement(sdi12, measurements, address, manufacturer, model, "C", location, measurement_count=2)
        response_m = read_measurement(sdi12, measurements, address, manufacturer, model, "M", location)
        response = response_m or response

    if not response:
        set_no_response_error(measurements, address)


def current_sense_4_20mA(measurements):
    for i in range(1, 3):
        measure_4_20_mA_on_port(measurements, i)

    sleep_ms(200)


def measure_4_20_mA_on_port(measurements, port_id):
    import gpio_handler
    from sensors import analog_generic

    port_enabled = cfg.get("_4_20_SNSR_{}_ENABLE".format(port_id))
    port_formula = cfg.get("_4_20_SNSR_{}_FORMULA".format(port_id))

    if port_enabled:
        sensor_on_pin = cfg.get("_UC_IO_SNSR_GND_4_20_SNSR_{}_ON".format(port_id))
        if not sensor_on_pin:
            # in folllowing label, ON is written in greek...
            sensor_on_pin = cfg.get("_UC_IO_SNSR_GND_4_20_SNSR_{}_ON".format(port_id))

        sensor_out_pin = cfg.get("_CUR_SNSR_OUT_{}".format(port_id))

        _CURRENT_OFFSET_MA = 0.6  # fix for the deviation of values

        try:
            gpio_handler.set_pin_value(cfg.get("_UC_IO_CUR_SNS_ON"), 1)
            gpio_handler.set_pin_value(sensor_on_pin, 1)

            raw_mV = analog_generic.get_reading(sensor_out_pin)
            current_mA = round((raw_mV / (cfg.get("_SHUNT_OHMS") * cfg.get("_INA_GAIN"))) * 100) / 100

            if current_mA > 3:  # do apply offset
                current_mA += _CURRENT_OFFSET_MA

                # if current_mA < 4:
                #     current_mA = 4

            logging.debug("ANLG SENSOR @ pin {}: {} mV, Current = {} mA".format(sensor_out_pin, raw_mV, current_mA))
            # kept for backward compatibility
            set_value_float(measurements, "4-20_{}_current".format(port_id), current_mA, SenmlSecondaryUnits.SENML_SEC_UNIT_MILLIAMPERE)
            set_value_float(measurements, "4_20_{}_current".format(port_id), current_mA, SenmlSecondaryUnits.SENML_SEC_UNIT_MILLIAMPERE)

            # kept for backward compatibility
            execute_formula(measurements, "4-20_{}_current".format(port_id), current_mA, port_formula)
            execute_formula(measurements, "4_20_{}_current".format(port_id), current_mA, port_formula)

            gpio_handler.set_pin_value(sensor_on_pin, 0)
            gpio_handler.set_pin_value(cfg.get("_UC_IO_CUR_SNS_ON"), 0)
        except Exception as e:
            logging.exception(e, "Error getting current sensor output: ID: {}".format(port_id))


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


def read_pulse_counter(measurements):
    pcnt_1_enabled = cfg.get("_PCNT_1_ENABLE")
    if pcnt_1_enabled:
        from . import scenario_pcnt_ulp

        pcnt_cfg = [
            {
                "id": 1,
                "enabled": pcnt_1_enabled,
                "formula": cfg.get("_PCNT_1_FORMULA"),
                "highFreq": cfg.get("_PCNT_1_HIGH_FREQ"),
                "gpio": cfg.get("UC_IO_DGTL_SNSR_READ"),
            },
            {"id": 2, "enabled": False},
        ]

        scenario_pcnt_ulp.execute(measurements, pcnt_cfg)
    else:
        import utils

        TIMESTAMP_FLAG_FILE = "/pcnt_last_read_timestamp"
        utils.deleteFlagFile(TIMESTAMP_FLAG_FILE)
