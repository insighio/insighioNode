from utime import sleep_ms
from external.kpn_senml.senml_unit import SenmlUnits
from external.kpn_senml.senml_unit import SenmlSecondaryUnits
import logging
from sensors import set_sensor_power_on, set_sensor_power_off

from .dictionary_utils import set_value

from sdi12_response_parsers import parse_sensor_meter, parse_sensor_acclima, parse_sensor_implexx, parse_sensor_licor, parse_generic_sdi12

from . import cfg

_io_expander = None
_io_expander_addr = None

_sdi12_config = {}
_modbus_config = {}
_adc_config = {}
_pulse_counter_config = {}


def io_expander_init():
    global _io_expander
    global _io_expander_addr
    if _io_expander is None:
        from machine import SoftI2C, Pin

        I2C_SCL = cfg.get("_UC_IO_I2C_SCL")
        I2C_SDA = cfg.get("_UC_IO_I2C_SDA")
        _io_expander = SoftI2C(scl=Pin(I2C_SCL), sda=Pin(I2C_SDA), freq=400000)
        _io_expander_addr = cfg.get("_UC_IO_EXPANDER_ADDR")

    return _io_expander


def io_expander_power_on_sdi12_sensors():
    _io_expander.writeto_mem(_io_expander_addr, 3, b"\xfd")


def io_expander_power_off_sdi12_sensors():
    _io_expander.writeto_mem(_io_expander_addr, 1, b"\xfd")


def enable_regulator():
    # power on SDI12 regulator
    set_sensor_power_on(cfg.get("_UC_IO_SNSR_REG_ON"))


def disable_regulator():
    # power off SDI12 regulator
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


def executeSDI12Measurements(measurements):
    io_expander_power_on_sdi12_sensors()

    if _has(_sdi12_config, "warmupTime"):
        sleep_ms(_get(_sdi12_config, "warmupTime"))

    from external.microsdi12.microsdi12 import SDI12

    sdi12 = None

    if not _has(_sdi12_config, "sensors"):
        logging.error("No sensors found in SDI12 config")
        return

    try:
        sdi12 = SDI12(cfg.get("_UC_IO_DRV_IN"), cfg.get("_UC_IO_RCV_OUT"), None, 1)
        sdi12.set_dual_direction_pins(cfg.get("_UC_IO_DRV_ON"), cfg.get("_UC_IO_RCV_ON"), 1, 1, 0, 1)
        sdi12.set_wait_after_uart_write(True)
        sdi12.wait_after_each_send(500)

        for sensor in _get(_sdi12_config, "sensors"):
            read_sdi12_sensor(sdi12, measurements, sensor)
    except Exception as e:
        logging.exception(e, "Exception while reading SDI-12 data")
    if sdi12:
        sdi12.close()

    io_expander_power_off_sdi12_sensors()


def shield_measurements(measurements):
    io_expander_init()

    initialize_configurations()

    enable_regulator()

    executeSDI12Measurements(measurements)

    # get 4-20mA measurements
    # try:
    #     current_sense_4_20mA(measurements)
    # except Exception as e:
    #     logging.exception(e, "Exception while reading 4_20mA data")

    # power off SDI12 regulator
    disable_regulator()


def read_sdi12_sensor(sdi12, measurements, sensor):
    address = sensor._get("address")
    command = sensor._get("measCmd")
    sub_cmd = sensor._get("measSubCmd")

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


def execute_transformation(measurements, name, raw_value, transformator):
    try:
        transformator = transformator.replace("v", str(raw_value))
        to_execute = "v_transformed=({})".format(transformator)
        namespace = {}
        exec(to_execute, namespace)
        print("namespace: " + str(namespace))
        set_value(measurements, name + "_formula", namespace["v_transformed"])
    except Exception as e:
        logging.exception(e, "transformator name:{}, raw_value:{}, code:{}".format(name, raw_value, transformator))
        pass
