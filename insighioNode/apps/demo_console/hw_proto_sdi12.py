from .dictionary_utils import set_value, set_value_int, _get, set_value_float
from external.kpn_senml.senml_unit import SenmlUnits
from external.kpn_senml.senml_unit import SenmlSecondaryUnits
from external.microsdi12.microsdi12 import SDI12
import logging

_sdi12_config = {}
_sdi12_connection = None
_cfg_is_celsius = True


def initialize_config(config_json, cfg_is_celsius):
    global _sdi12_config
    global _cfg_is_celsius

    import json

    try:
        _sdi12_config = json.loads(config_json)
    except Exception as e:
        logging.exception(e, "Error loading SDI12 config")

    _cfg_is_celsius = cfg_is_celsius

    return _sdi12_config


def get_sdi12_config():
    global _sdi12_config
    if not _sdi12_config:
        logging.error("SDI12 config not initialized")
        return None

    return _sdi12_config


def initialize_sdi12_connection(io_drv_in, io_rcv_out, io_drv_on, io_rcv_on, drv_on_rcv_state=0):
    global _sdi12_connection

    if _sdi12_connection is not None:
        close_sdi12_connection()

    try:
        _sdi12_connection = SDI12(io_drv_in, io_rcv_out, None, 1)
        _sdi12_connection.set_dual_direction_pins(io_drv_on, io_rcv_on, 1, 1, drv_on_rcv_state, 0)
        _sdi12_connection.set_wait_after_uart_write(True)
        _sdi12_connection.wait_after_each_send(500)
    except Exception as e:
        logging.exception(e, "Exception while reading SDI-12 data")
    return _sdi12_connection


def get_sdi12_connection():
    global _sdi12_connection
    if not _sdi12_connection:
        logging.error("SDI12 connection not initialized")
        return None

    return _sdi12_connection


def close_sdi12_connection():
    global _sdi12_connection
    if _sdi12_connection:
        _sdi12_connection.close()
        _sdi12_connection = None
    else:
        logging.error("SDI12 connection not initialized")


def read_sdi12_sensor(sdi12, measurements, sensor, location=1):
    address = str(_get(sensor, "address"))
    command = _get(sensor, "measCmd")
    sub_cmd = _get(sensor, "measSubCmd")

    logging.debug("read_sdi12_sensor - address: {}, command: {}, sub_cmd: {}, location: {}".format(address, command, sub_cmd, location))

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

        parse_sdi12_sensor_response_array(manufacturer, model, address, command_to_execute, responseArray, measurements, location)

        # post-parse actions
        if "li-cor" in manufacturer and command_to_execute == "M0":
            sdi12._send(address + "XT!")  # trigger next round of measurements

    except Exception as e:
        logging.exception(e, "Exception while reading SDI-12 data for address: {}".format(address))
        return


def parse_sdi12_sensor_response_array(manufacturer, model, address, command_to_execute, responseArray, measurements, location=1):
    set_value(measurements, "sdi12_{}_{}_i".format(address, location), manufacturer, None)
    set_value(measurements, "sdi12_{}_{}_m".format(address, location), model, None)

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


def parse_sensor_meter(model, command_to_execute, address, responseArray, measurements, location=None):
    try:
        location_info = ("_" + str(location)) if location else ""
        variable_prefix = "meter_" + address + location_info

        if model == "ter12" and command_to_execute == "M":  # apply functions
            if not responseArray or len(responseArray) < 3:
                logging.error("parse_sensor_meter: unrecognized responseArray: {}".format(responseArray))
                return

            set_value_float(measurements, variable_prefix + "_count_vwc", responseArray[0], SenmlUnits.SENML_UNIT_COUNTER)
            set_value_float(measurements, variable_prefix + "_temp", responseArray[1], SenmlUnits.SENML_UNIT_DEGREES_CELSIUS)
            set_value_float(measurements, variable_prefix + "_soil_ec", responseArray[2], "uS/cm")

            from math import pow

            calibratedCountsVWC = float(responseArray[0])
            VWCmineral = 3.879e-4 * calibratedCountsVWC - 0.6956  # mineral soil calibration
            VWCsoilless = (
                6.771e-10 * pow(calibratedCountsVWC, 3) - 5.105e-6 * pow(calibratedCountsVWC, 2) + 1.302e-2 * calibratedCountsVWC - 10.848
            )  # soilless substrate calibration
            VWCdielectric = pow(
                2.887e-9 * pow(calibratedCountsVWC, 3) - 2.08e-5 * pow(calibratedCountsVWC, 2) + 5.276e-2 * calibratedCountsVWC - 43.39, 2
            )

            set_value_float(measurements, variable_prefix + "_vwc_mineral", VWCmineral * 100, SenmlSecondaryUnits.SENML_SEC_UNIT_PERCENT)
            set_value_float(measurements, variable_prefix + "_vwc_soilless", VWCsoilless * 100, SenmlSecondaryUnits.SENML_SEC_UNIT_PERCENT)
            set_value_float(measurements, variable_prefix + "_vwc_dielectric", VWCdielectric, SenmlSecondaryUnits.SENML_SEC_UNIT_PERCENT)
        elif model == "atm14" and command_to_execute == "M":
            if not responseArray or len(responseArray) < 4:
                logging.error("parse_sensor_meter: unrecognized responseArray: {}".format(responseArray))
                return
            try:
                set_value_float(measurements, variable_prefix + "_vapor_pressure", responseArray[0], SenmlUnits.SENML_UNIT_PASCAL, 2, 1000)
            except Exception as e:
                pass
            set_value_float(measurements, variable_prefix + "_temp", responseArray[1], SenmlUnits.SENML_UNIT_DEGREES_CELSIUS)
            try:
                set_value_float(
                    measurements,
                    variable_prefix + "_relative_humidity",
                    responseArray[2],
                    SenmlSecondaryUnits.SENML_SEC_UNIT_PERCENT,
                    2,
                    100,
                )
            except Exception as e:
                pass
            try:
                set_value_float(
                    measurements, variable_prefix + "_atmospheric_pressure", responseArray[3], SenmlUnits.SENML_UNIT_PASCAL, 2, 1000
                )
            except Exception as e:
                pass
        else:
            parse_generic_sdi12(address, responseArray, measurements, "sdi12", None, "_" + command_to_execute.lower(), location)

    except Exception as e:
        logging.exception(e, "Error processing meter sdi responseArray: [{}]".format(responseArray))


def parse_sensor_acclima(model, command_to_execute, address, responseArray, measurements, location=None):
    try:
        if not responseArray or len(responseArray) < 5:
            logging.error("parse_sensor_acclima: unrecognized responseArray: {}".format(responseArray))
            return

        location_info = ("_" + str(location)) if location else ""
        variable_prefix = "acclima_" + address + location_info

        set_value_float(measurements, variable_prefix + "_vwc", responseArray[0], SenmlSecondaryUnits.SENML_SEC_UNIT_PERCENT)
        set_value_float(measurements, variable_prefix + "_temp", responseArray[1], SenmlUnits.SENML_UNIT_DEGREES_CELSIUS)
        set_value_float(measurements, variable_prefix + "_rel_perm", responseArray[2])
        set_value_float(measurements, variable_prefix + "_soil_ec", responseArray[3], "uS/cm")
        set_value_float(measurements, variable_prefix + "_pore_water_ec", responseArray[4], "uS/cm")
    except Exception as e:
        logging.exception(e, "Error processing acclima sdi responseArray: [{}]".format(responseArray))


def parse_sensor_implexx(model, command_to_execute, address, responseArray, measurements, location=None):
    try:
        if not responseArray or len(responseArray) < 5:
            logging.error("parse_sensor_implexx: unrecognized responseArray: {}".format(responseArray))
            return

        location_info = ("_" + str(location)) if location else ""
        variable_prefix = "implexx_" + address + location_info

        set_value_float(measurements, variable_prefix + "_sap_flow", responseArray[0], SenmlSecondaryUnits.SENML_SEC_UNIT_LITER_PER_HOUR)
        set_value_float(
            measurements, variable_prefix + "_hv_outer", responseArray[1], SenmlSecondaryUnits.SENML_SEC_UNIT_CENTIMETRE_PER_HOUR
        )
        set_value_float(
            measurements, variable_prefix + "_hv_inner", responseArray[2], SenmlSecondaryUnits.SENML_SEC_UNIT_CENTIMETRE_PER_HOUR
        )
        set_value_float(measurements, variable_prefix + "_log_rt_a_outer", responseArray[3], None, 5)
        set_value_float(measurements, variable_prefix + "_log_rt_a_inner", responseArray[4], None, 5)
    except Exception as e:
        logging.exception(e, "Error processing acclima sdi responseArray: [{}]".format(responseArray))


def parse_sensor_licor(model, command_to_execute, address, responseArray, measurements, location=None):
    try:
        if not responseArray or len(responseArray) < 5:
            logging.error("parse_sensor_licor: unrecognized responseArray: {}".format(responseArray))
            return

        location_info = ("_" + str(location)) if location else ""
        variable_prefix = "licor_" + address + location_info

        set_value_float(measurements, variable_prefix + "_et", responseArray[0], SenmlSecondaryUnits.SENML_SEC_UNIT_MILLIMETER, 3)
        set_value_float(measurements, variable_prefix + "_le", responseArray[1], SenmlUnits.SENML_UNIT_WATT_PER_SQUARE_METER, 1)
        set_value_float(measurements, variable_prefix + "_h", responseArray[2], SenmlUnits.SENML_UNIT_WATT_PER_SQUARE_METER, 1)
        set_value_float(measurements, variable_prefix + "_vpd", responseArray[3], SenmlSecondaryUnits.SENML_SEC_UNIT_HECTOPASCAL, 1, 10)
        set_value_float(measurements, variable_prefix + "_pa", responseArray[4], SenmlSecondaryUnits.SENML_SEC_UNIT_HECTOPASCAL, 1, 10)
        # cfg_is_celsius = cfg.get("_MEAS_TEMP_UNIT_IS_CELSIUS")
        if _cfg_is_celsius:
            set_value_float(measurements, variable_prefix + "_ta", responseArray[5], SenmlUnits.SENML_UNIT_DEGREES_CELSIUS, 2)
        else:
            set_value_float(measurements, variable_prefix + "_taf", responseArray[5], None, 2, 9 / 5)
            calculated_value = measurements[variable_prefix + "_taf"]["value"] + 32
            set_value_float(measurements, variable_prefix + "_taf", calculated_value, SenmlSecondaryUnits.SENML_SEC_UNIT_FAHRENHEIT, 2)
        set_value_float(measurements, variable_prefix + "_rh", responseArray[6], SenmlUnits.SENML_UNIT_RELATIVE_HUMIDITY, 2)
        set_value_int(measurements, variable_prefix + "_seq", responseArray[7], None)
        set_value_int(measurements, variable_prefix + "_diag", responseArray[8], None)
    except Exception as e:
        logging.exception(e, "Error processing acclima sdi responseArray: [{}]".format(responseArray))


def parse_generic_sdi12(address, responseArray, measurements, prefix="gen", unit=None, postfix="", location=None):
    try:
        if not responseArray or len(responseArray) == 0:
            logging.error("Unrecognized responseArray: {}".format(responseArray))
            return

        location_info = ("_" + str(location)) if location else ""
        variable_prefix = prefix + "_" + address + location_info + postfix

        for i, val in enumerate(responseArray):
            try:
                set_value_float(measurements, variable_prefix + "_" + str(i), val, unit)
            except Exception as e:
                logging.exception(e, "Error processing generic sdi responseArray: [{}]".format(val))
    except Exception as e:
        logging.exception(e, "Error processing generic sdi responseArray: [{}]".format(responseArray))
