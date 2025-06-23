from utime import sleep_ms

from external.kpn_senml.senml_unit import SenmlUnits
from external.kpn_senml.senml_unit import SenmlSecondaryUnits
import logging
from sensors import set_sensor_power_on, set_sensor_power_off

from ..dictionary_utils import set_value, set_value_float, _get, _has

from . import hw_proto_sdi12


from .. import cfg

_sdi12_supported_board_locations = [1, 2]
_sdi12_board_location_last_power_on = 0


def get_board_location_pin(board_location):
    if board_location is None or board_location < 1 or board_location > 2:
        board_location = 1

    pwr_on_pin = cfg.get("_UC_IO_PWR_SDI_SNSR_" + str(board_location) + "_ON", "shield-sensor")
    if pwr_on_pin is None:
        pwr_on_pin = cfg.get("_UC_IO_SNSR_GND_SDI_SNSR_" + str(board_location) + "_ON", "shield-sensor")
    return pwr_on_pin


def powerOnBoardLocation(board_location, warmup_time):
    global _sdi12_board_location_last_power_on
    has_found = False
    for loc in _sdi12_supported_board_locations:
        pwr_on_pin = get_board_location_pin(loc)
        if pwr_on_pin is None:
            continue

        if loc == board_location:
            has_found = True
            if loc != _sdi12_board_location_last_power_on:
                set_sensor_power_on(pwr_on_pin)
                _sdi12_board_location_last_power_on = loc
                sleep_ms(warmup_time)
        else:
            set_sensor_power_off(pwr_on_pin)

    if not has_found:
        _sdi12_board_location_last_power_on = 0


def powerOffAllBoardLocations():
    for loc in _sdi12_supported_board_locations:
        pwr_on_pin = get_board_location_pin(loc)
        if pwr_on_pin is None:
            continue
        set_sensor_power_off(pwr_on_pin)


def execute_sdi12_measurements(measurements):
    _sdi12_config = hw_proto_sdi12.initialize_config(cfg.get("meas-sdi12"), cfg.get("meas-temp-unit"))

    sensor_list = _get(_sdi12_config, "sensors")

    if not sensor_list or len(sensor_list) == 0:
        logging.error("No sensors found in SDI12 config")
        return

    logging.info("Starting SDI12 measurements")

    config = _get(_sdi12_config, "config")
    if not config:
        logging.error("No config found in SDI12 config")
        return

    sdi12 = hw_proto_sdi12.initialize_sdi12_connection(
        cfg.get("_UC_IO_DRV_IN", "shield-sensor"),
        cfg.get("_UC_IO_RCV_OUT", "shield-sensor"),
        cfg.get("_UC_IO_DRV_ON", "shield-sensor"),
        cfg.get("_UC_IO_RCV_ON", "shield-sensor"),
        0,
    )

    if not sdi12:
        logging.error("Failed to initialize SDI12")
        return

    # sort sensor list by board_location
    sensor_list.sort(key=lambda x: x.get("board_location", 0))

    warmup_time_ms = 1000
    if _has(config, "warmupTimeMs"):
        try:
            warmup_time_ms = int(_get(config, "warmupTimeMs"))
        except:
            pass
        logging.debug("SDI12 warmup time: {}".format(warmup_time_ms))

    for sensor in sensor_list:
        loc = sensor.get("boardLocation")
        powerOnBoardLocation(loc, warmup_time_ms)
        hw_proto_sdi12.read_sdi12_sensor(sdi12, measurements, sensor, _sdi12_board_location_last_power_on)

    powerOffAllBoardLocations()
    hw_proto_sdi12.close_sdi12_connection()


def shield_measurements(measurements):
    # power on SDI12 regulator
    set_sensor_power_on(cfg.get("_UC_IO_SNSR_REG_ON", "shield-sensor"))

    execute_sdi12_measurements(measurements)

    # get 4-20mA measurements
    try:
        current_sense_4_20mA(measurements)
    except Exception as e:
        logging.exception(e, "Exception while reading 4_20mA data")

    read_pulse_counter(measurements)

    # power off SDI12 regulator
    set_sensor_power_off(cfg.get("_UC_IO_SNSR_REG_ON", "shield-sensor"))


# def read_sdi12_sensor(sdi12, address, measurements, location=None):
#     manufacturer = None
#     model = None
#     responseArray = None
#     if sdi12.is_active(address):
#         manufacturer, model = sdi12.get_sensor_info(address)
#         manufacturer = manufacturer.lower()
#         model = model.lower()
#         logging.debug("manufacturer: {}, model: {}".format(manufacturer, model))
#         set_value(measurements, "sdi12_{}_{}_model".format(address, location), model)
#         set_value(measurements, "sdi12_{}_{}_manufacturer".format(address, location), manufacturer)

#     if not manufacturer:
#         logging.error("read_sdi12_sensor - No sensor found in address: [" + str(address) + "]")
#         return

#     if manufacturer == "meter":
#         responseArray = sdi12.get_measurement(address)
#         parse_sensor_meter(model, "M", address, responseArray, measurements, location)
#     elif manufacturer == "in-situ" and (model == "at500" or model == "at400"):
#         responseArray = sdi12.get_measurement(address, "C", 1, True)
#         parse_generic_sdi12(address, responseArray, measurements, "sdi12", None, "", location)
#     elif manufacturer == "acclima":
#         responseArray = sdi12.get_measurement(address)
#         parse_sensor_acclima(model, "M", address, responseArray, measurements, location)
#     elif manufacturer == "implexx":
#         responseArray = sdi12.get_measurement(address)
#         parse_sensor_implexx(model, "M", address, responseArray, measurements, location)
#     elif manufacturer == "ep100g":  # EnviroPro
#         responseArrayMoisture = sdi12.get_measurement(address, "C")  # moisture with salinity
#         responseArraySalinity = sdi12.get_measurement(address, "C1")  # salinity

#         parse_generic_sdi12(
#             address, responseArrayMoisture, measurements, "ep_vwc", SenmlSecondaryUnits.SENML_SEC_UNIT_PERCENT, "", location
#         )
#         parse_generic_sdi12(address, responseArraySalinity, measurements, "ep_ec", "uS/cm", "", location)  # dS/m

#         cfg_is_celsius = cfg.get("meas-temp-unit")
#         if cfg_is_celsius:
#             responseArrayTemperature = sdi12.get_measurement(address, "C2")
#             parse_generic_sdi12(
#                 address, responseArrayTemperature, measurements, "ep_temp", SenmlUnits.SENML_UNIT_DEGREES_CELSIUS, "", location
#             )
#         else:
#             responseArrayTemperature = sdi12.get_measurement(address, "C5")
#             parse_generic_sdi12(
#                 address, responseArrayTemperature, measurements, "ep_temp", SenmlSecondaryUnits.SENML_SEC_UNIT_FAHRENHEIT, "", location
#             )
#     elif "li-cor" in manufacturer:
#         responseArray = sdi12.get_measurement(address, "M0")
#         parse_sensor_licor(model, "M0", address, responseArray, measurements, location)
#         responseArray = sdi12._send(address + "XT!")  # trigger next round of measurements
#     else:
#         set_value(measurements, "sdi12_{}_i".format(address), manufacturer, None)
#         responseArrayC = sdi12.get_measurement(address, "C", 2)
#         responseArrayM = sdi12.get_measurement(address, "M", 1)
#         parse_generic_sdi12(address, responseArrayC, measurements, "sdi12", None, "_c", location)
#         parse_generic_sdi12(address, responseArrayM, measurements, "sdi12", None, "_m", location)


def current_sense_4_20mA(measurements):
    for i in range(1, 3):
        measure_4_20_mA_on_port(measurements, i)

    sleep_ms(200)


def measure_4_20_mA_on_port(measurements, port_id):
    import gpio_handler
    from sensors import analog_generic

    port_enabled = cfg.get("_4_20_SNSR_{}_ENABLE".format(port_id), "shield-sensor")
    port_formula = cfg.get("_4_20_SNSR_{}_FORMULA".format(port_id), "shield-sensor")

    if port_enabled:
        sensor_on_pin = cfg.get("_UC_IO_SNSR_GND_4_20_SNSR_{}_ON".format(port_id), "shield-sensor")
        if not sensor_on_pin:
            # in folllowing label, ON is written in greek...
            sensor_on_pin = cfg.get("_UC_IO_SNSR_GND_4_20_SNSR_{}_ON".format(port_id), "shield-sensor")

        sensor_out_pin = cfg.get("_CUR_SNSR_OUT_{}".format(port_id), "shield-sensor")

        _CURRENT_OFFSET_MA = 0.6  # fix for the deviation of values

        try:
            gpio_handler.set_pin_value(cfg.get("_UC_IO_CUR_SNS_ON"), 1)
            gpio_handler.set_pin_value(sensor_on_pin, 1)

            raw_mV = analog_generic.get_reading(sensor_out_pin)
            current_mA = round((raw_mV / (cfg.get("_SHUNT_OHMS", "shield-sensor") * cfg.get("_INA_GAIN", "shield-sensor"))) * 100) / 100

            if current_mA > 3:  # do apply offset
                current_mA += _CURRENT_OFFSET_MA

                # if current_mA < 4:
                #     current_mA = 4

            logging.debug("ANLG SENSOR @ pin {}: {} mV, Current = {} mA".format(sensor_out_pin, raw_mV, current_mA))
            set_value_float(measurements, "4-20_{}_current".format(port_id), current_mA, SenmlSecondaryUnits.SENML_SEC_UNIT_MILLIAMPERE)

            execute_formula(measurements, "4-20_{}_current".format(port_id), current_mA, port_formula)

            gpio_handler.set_pin_value(sensor_on_pin, 0)
            gpio_handler.set_pin_value(cfg.get("_UC_IO_CUR_SNS_ON", "shield-sensor"), 0)
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
    pcnt_1_enabled = cfg.get("meas-pcnt-1-enable")
    if pcnt_1_enabled:
        from . import hw_pcnt_ulp

        pcnt_cfg = [
            {
                "id": 1,
                "enabled": pcnt_1_enabled,
                "formula": cfg.get("meas-pcnt-1-formula"),
                "highFreq": cfg.get("meas-pcnt-1-high-freq"),
                "gpio": cfg.get("UC_IO_DGTL_SNSR_READ", "shield-sensor"),
            },
            {"id": 2, "enabled": False},
        ]

        hw_pcnt_ulp.execute(measurements, pcnt_cfg)
    else:
        import utils

        TIMESTAMP_FLAG_FILE = "/pcnt_last_read_timestamp"
        utils.deleteFlagFile(TIMESTAMP_FLAG_FILE)
