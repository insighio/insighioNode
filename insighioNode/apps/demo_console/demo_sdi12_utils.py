import utime
from apps.demo_console.dictionary_utils import set_value_float
from external.kpn_senml.senml_unit import SenmlUnits
from external.kpn_senml.senml_unit import SenmlSecondaryUnits
from . import demo_config as cfg
import logging
import device_info
import sensors


def sdi12_board_measurements(measurements):
    if not cfg._SDI12_SENSOR_1_ENABLED and not cfg._SDI12_SENSOR_2_ENABLED:
        return

    # power on SDI12 regulator
    if hasattr(cfg, "_UC_IO_SNSR_REG_ON"):
        sensors.set_sensor_power_on(cfg._UC_IO_SNSR_REG_ON)

    utime.sleep_ms(cfg._SDI12_WARM_UP_TIME_MSEC)

    from external.microsdi12.microsdi12 import SDI12

    sdi12 = None

    try:
        sdi12 = SDI12(cfg._UC_IO_DRV_IN, cfg._UC_IO_RCV_OUT, cfg._UC_IO_DRV_RCV_ON, 1)
        sdi12.set_wait_after_uart_write(not device_info.is_esp32())

        if cfg._SDI12_SENSOR_1_ENABLED:
            read_sdi12_sensor(sdi12, cfg._SDI12_SENSOR_1_ADDRESS, measurements)

        if cfg._SDI12_SENSOR_2_ENABLED:
            read_sdi12_sensor(sdi12, cfg._SDI12_SENSOR_2_ADDRESS, measurements)
    except Exception as e:
        logging.exception(e, "Exception while reading SDI-12 data")
    if sdi12:
        sdi12.close()

    # power off SDI12 regulator
    if hasattr(cfg, "_UC_IO_SNSR_REG_ON"):
        sensors.set_sensor_power_on(cfg._UC_IO_SNSR_REG_ON)


def read_sdi12_sensor(sdi12, address, measurements):
    manufacturer = None
    model = None
    responseArray = None
    if sdi12.is_active(address):
        manufacturer, model = sdi12.get_sensor_info(address)
        manufacturer = manufacturer.lower()

    if not manufacturer:
        logging.error("read_sdi12_sensor - No sensor found in address: [" + str(address) + "]")
        return

    if manufacturer == 'meter':
        responseArray = sdi12.get_measurement(address)
        parse_sensor_meter(address, responseArray, measurements)
    elif manufacturer == 'acclima':
        responseArray = sdi12.get_measurement(address)
        parse_sensor_acclima(address, responseArray, measurements)
    elif manufacturer == 'implexx':
        responseArray = sdi12.get_measurement(address)
        parse_sensor_implexx(address, responseArray, measurements)
    elif manufacturer == 'ep100g':  # EnviroPro
        responseArrayMoisture = sdi12.get_measurement(address, "C")  # moisture with salinity
        responseArraySalinity = sdi12.get_measurement(address, "C1")  # salinity

        parse_generic_sdi12(address, responseArray, responseArrayMoisture, "ep_vwc", SenmlSecondaryUnits.SENML_SEC_UNIT_PERCENT)
        parse_generic_sdi12(address, responseArray, responseArraySalinity, "ep_ec", "uS/cm")  # dS/m

        if cfg._MEAS_TEMP_UNIT_IS_CELSIUS:
            responseArrayTemperature = sdi12.get_measurement(address, "C2")
            parse_generic_sdi12(address, responseArray, responseArraySalinity, "ep_temp", SenmlUnits.SENML_UNIT_DEGREES_CELSIUS)
        else:
            responseArrayTemperature = sdi12.get_measurement(address, "C5")
            parse_generic_sdi12(address, responseArray, responseArraySalinity, "ep_temp", SenmlSecondaryUnits.SENML_SEC_UNIT_FAHRENHEIT)
    else:
        parse_generic_sdi12(address, responseArray, measurements)


def parse_sensor_meter(address, responseArray, measurements):
    try:
        if not responseArray or len(responseArray) < 3:
            logging.error("parse_sensor_acclima: unrecognized responseArray: {}".format(responseArray))
            return

        variable_prefix = "meter_" + address

        set_value_float(measurements, variable_prefix + "_vwc", responseArray[0], SenmlSecondaryUnits.SENML_SEC_UNIT_PERCENT)
        set_value_float(measurements, variable_prefix + "_temp", responseArray[1], SenmlUnits.SENML_UNIT_DEGREES_CELSIUS)
        set_value_float(measurements, variable_prefix + "_soil_ec", responseArray[2], "uS/cm")
    except Exception as e:
        logging.exception(e, "Error processing meter sdi responseArray: [{}]".format(responseArray))


def parse_sensor_acclima(address, responseArray, measurements):
    try:
        if not responseArray or len(responseArray) < 5:
            logging.error("parse_sensor_acclima: unrecognized responseArray: {}".format(responseArray))
            return

        variable_prefix = "acclima_" + address

        set_value_float(measurements, variable_prefix + "_vwc", responseArray[0], SenmlSecondaryUnits.SENML_SEC_UNIT_PERCENT)
        set_value_float(measurements, variable_prefix + "_temp", responseArray[1], SenmlUnits.SENML_UNIT_DEGREES_CELSIUS)
        set_value_float(measurements, variable_prefix + "_rel_perm", responseArray[2])
        set_value_float(measurements, variable_prefix + "_soil_ec", responseArray[3], "uS/cm")
        set_value_float(measurements, variable_prefix + "_pore_water_ec", responseArray[4], "uS/cm")
    except Exception as e:
        logging.exception(e, "Error processing acclima sdi responseArray: [{}]".format(responseArray))


def parse_sensor_implexx(address, responseArray, measurements):
    try:
        if not responseArray or len(responseArray) < 5:
            logging.error("parse_sensor_implexx: unrecognized responseArray: {}".format(responseArray))
            return

        variable_prefix = "implexx_" + address

        set_value_float(measurements, variable_prefix + "_sap_flow", responseArray[0], SenmlSecondaryUnits.SENML_SEC_UNIT_LITER_PER_HOUR)
        set_value_float(measurements, variable_prefix + "_hv_outer", responseArray[1], SenmlSecondaryUnits.SENML_SEC_UNIT_CENTIMETRE_PER_HOUR)
        set_value_float(measurements, variable_prefix + "_hv_inner", responseArray[2], SenmlSecondaryUnits.SENML_SEC_UNIT_CENTIMETRE_PER_HOUR)
        set_value_float(measurements, variable_prefix + "_log_rt_a_outer", responseArray[3], None, 5)
        set_value_float(measurements, variable_prefix + "_log_rt_a_inner", responseArray[4], None, 5)
    except Exception as e:
        logging.exception(e, "Error processing acclima sdi responseArray: [{}]".format(responseArray))


def parse_generic_sdi12(address, responseArray, measurements, prefix="gen", unit=None):
    try:
        if not responseArray or len(responseArray) == 0:
            logging.error("Unrecognized responseArray: {}".format(responseArray))
            return

        variable_prefix = prefix + "_" + address

        for i, val in enumerate(responseArray):
            try:
                set_value_float(measurements, variable_prefix + "_" + str(i), val, unit)
            except Exception as e:
                logging.exception(e, "Error processing generic sdi responseArray: [{}]".format(val))
    except Exception as e:
        logging.exception(e, "Error processing generic sdi responseArray: [{}]".format(responseArray))
