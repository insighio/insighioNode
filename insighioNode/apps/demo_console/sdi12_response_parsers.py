from .dictionary_utils import set_value, set_value_int, set_value_float
from external.kpn_senml.senml_unit import SenmlUnits
from external.kpn_senml.senml_unit import SenmlSecondaryUnits
import logging


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
                set_value_float(
                    measurements, variable_prefix + "_vapor_pressure", float(responseArray[0]) * 1000, SenmlUnits.SENML_UNIT_PASCAL
                )
            except Exception as e:
                pass
            set_value_float(measurements, variable_prefix + "_temp", responseArray[1], SenmlUnits.SENML_UNIT_DEGREES_CELSIUS)
            try:
                set_value_float(
                    measurements,
                    variable_prefix + "_relative_humidity",
                    float(responseArray[2]) * 100,
                    SenmlSecondaryUnits.SENML_SEC_UNIT_PERCENT,
                )
            except Exception as e:
                pass
            try:
                set_value_float(
                    measurements, variable_prefix + "_atmospheric_pressure", float(responseArray[3]) * 1000, SenmlUnits.SENML_UNIT_PASCAL
                )
            except Exception as e:
                pass

        # aD0! a+<solar>+<precipitation>+<strikes>+<strikeDistance>
        # aD1! a+<windSpeed>+<windDirection>+<gustWindSpeed>
        # aD2! a+-<airTemperature>+<vaporPressure>+<atmosphericPressure>+<relativeHumidity>+-<humiditySensorTemperature>
        # aD3! a+-<xOrientation>+-<yOrientation>+<nullValue>
        # aD4! a+-<NorthWindSpeed>+-<EastWindSpeed>+<gustWindSpeed>
        elif (model == "at41g2" or model == "atm41") and command_to_execute == "C":
            if not responseArray or len(responseArray) < 18:
                logging.error("parse_sensor_meter: unrecognized responseArray: {}".format(responseArray))
                return

            set_value_float(measurements, variable_prefix + "_solar", responseArray[0], SenmlUnits.SENML_UNIT_WATT_PER_SQUARE_METER)
            set_value_float(
                measurements, variable_prefix + "_precipitation", responseArray[1], SenmlSecondaryUnits.SENML_SEC_UNIT_MILLIMETER
            )
            set_value_float(measurements, variable_prefix + "_strikes", responseArray[2], SenmlUnits.SENML_UNIT_COUNTER)
            set_value_float(measurements, variable_prefix + "_strike_distance", responseArray[3], SenmlUnits.SENML_UNIT_METER, 3, 1000)
            set_value_float(measurements, variable_prefix + "_wind_speed", responseArray[4], SenmlSecondaryUnits.SENML_UNIT_VELOCITY)
            set_value_float(measurements, variable_prefix + "_wind_direction", responseArray[5], SenmlUnits.SENML_UNIT_DEGREES)
            set_value_float(measurements, variable_prefix + "_gust_wind_speed", responseArray[6], SenmlSecondaryUnits.SENML_UNIT_VELOCITY)
            set_value_float(measurements, variable_prefix + "_air_temperature", responseArray[7], SenmlUnits.SENML_UNIT_DEGREES_CELSIUS)
            set_value_float(measurements, variable_prefix + "_vapor_pressure", responseArray[8], SenmlUnits.SENML_UNIT_PASCAL, 3, 1000)
            set_value_float(
                measurements, variable_prefix + "_atmospheric_pressure", responseArray[9], SenmlUnits.SENML_UNIT_PASCAL, 3, 1000
            )
            set_value_float(
                measurements,
                variable_prefix + "_relative_humidity",
                responseArray[10],
                SenmlSecondaryUnits.SENML_SEC_UNIT_PERCENT,
                1,
            )
            set_value_float(
                measurements, variable_prefix + "_humidity_sensor_temperature", responseArray[11], SenmlUnits.SENML_UNIT_DEGREES_CELSIUS
            )
            set_value_float(measurements, variable_prefix + "_x_orientation", responseArray[12], SenmlUnits.SENML_UNIT_DEGREES)
            set_value_float(measurements, variable_prefix + "_y_orientation", responseArray[13], SenmlUnits.SENML_UNIT_DEGREES)
            set_value_float(measurements, variable_prefix + "_north_wind_speed", responseArray[15], SenmlSecondaryUnits.SENML_UNIT_VELOCITY)
            set_value_float(measurements, variable_prefix + "_east_wind_speed", responseArray[16], SenmlSecondaryUnits.SENML_UNIT_VELOCITY)
            set_value_float(measurements, variable_prefix + "_gust_wind_speed", responseArray[17], SenmlSecondaryUnits.SENML_UNIT_VELOCITY)
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
        cfg_is_celsius = cfg.get("_MEAS_TEMP_UNIT_IS_CELSIUS")
        if cfg_is_celsius:
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
