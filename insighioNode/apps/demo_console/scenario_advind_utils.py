from utime import sleep_ms
from .dictionary_utils import set_value_float, set_value_int, set_value
from external.kpn_senml.senml_unit import SenmlUnits
from external.kpn_senml.senml_unit import SenmlSecondaryUnits
import logging
from sensors import set_sensor_power_on, set_sensor_power_off

from . import cfg

_sdi12_sensor_switch_list = []


def populateSDI12SensorSwitchList():
    global _sdi12_sensor_switch_list
    _sdi12_sensor_switch_list = [None] * 11

    for i in range(1, 11):
        pwr_on = cfg.get("_UC_IO_PWR_SDI_SNSR_" + str(i) + "_ΟΝ")
        if pwr_on is None:
            pwr_on = cfg.get("_UC_IO_SNSR_GND_SDI_SNSR_" + str(i) + "_ΟΝ")
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
    read_sdi12_sensor(sdi12, address, measurements,location)
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

    # power off SDI12 regulator
    set_sensor_power_off(cfg.get("_UC_IO_SNSR_REG_ON"))


def read_sdi12_sensor(sdi12, address, measurements, location=None):
    manufacturer = None
    model = None
    responseArray = None
    if sdi12.is_active(address):
        manufacturer, model = sdi12.get_sensor_info(address)
        manufacturer = manufacturer.lower()
        model = model.lower()
        logging.debug("manufacturer: {}, model: {}".format(manufacturer, model))
        # set_value(measurements, "sdi12_{}_model".format(address), model)
        # set_value(measurements, "sdi12_{}_manufacturer".format(address), manufacturer)

    if not manufacturer:
        logging.error("read_sdi12_sensor - No sensor found in address: [" + str(address) + "]")
        return

    if manufacturer == "meter" and "at41g2" not in model:
        responseArray = sdi12.get_measurement(address)
        parse_sensor_meter(model, address, responseArray, measurements, location)
    elif manufacturer == "in-situ" and (model == "at500" or model == "at400"):
        responseArray = sdi12.get_measurement(address, "M", 1, True)
        parse_generic_sdi12(address, responseArray, measurements, "sdi12", None, "", location)
    elif manufacturer == "acclima":
        responseArray = sdi12.get_measurement(address)
        parse_sensor_acclima(address, responseArray, measurements, location)
    elif manufacturer == "implexx":
        responseArray = sdi12.get_measurement(address)
        parse_sensor_implexx(address, responseArray, measurements, location)
    elif manufacturer == "ep100g":  # EnviroPro
        responseArrayMoisture = sdi12.get_measurement(address, "C")  # moisture with salinity
        responseArraySalinity = sdi12.get_measurement(address, "C1")  # salinity

        parse_generic_sdi12(address, responseArray, responseArrayMoisture, "ep_vwc", SenmlSecondaryUnits.SENML_SEC_UNIT_PERCENT, "", location)
        parse_generic_sdi12(address, responseArray, responseArraySalinity, "ep_ec", "uS/cm", "", location)  # dS/m

        cfg_is_celsius = cfg.get("_MEAS_TEMP_UNIT_IS_CELSIUS")
        if cfg_is_celsius:
            responseArrayTemperature = sdi12.get_measurement(address, "C2")
            parse_generic_sdi12(address, responseArray, responseArraySalinity, "ep_temp", SenmlUnits.SENML_UNIT_DEGREES_CELSIUS, "", location)
        else:
            responseArrayTemperature = sdi12.get_measurement(address, "C5")
            parse_generic_sdi12(address, responseArray, responseArraySalinity, "ep_temp", SenmlSecondaryUnits.SENML_SEC_UNIT_FAHRENHEIT, "", location)
    elif "li-cor" in manufacturer:
        responseArray = sdi12.get_measurement(address, "M0")
        parse_sensor_licor(address, responseArray, measurements, location)
        responseArray = sdi12._send(address + "XT!")  # trigger next round of measurements
    else:
        set_value(measurements, "sdi12_{}_i".format(address), manufacturer, None)
        responseArrayC = sdi12.get_measurement(address, "C", 2)
        responseArrayM = sdi12.get_measurement(address, "M", 1)
        parse_generic_sdi12(address, responseArrayC, measurements, "sdi12", None, "_c", location)
        parse_generic_sdi12(address, responseArrayM, measurements, "sdi12", None, "_m", location)


def parse_sensor_meter(model ,address, responseArray, measurements, location=None):
    try:
        if not responseArray or len(responseArray) < 3:
            logging.error("parse_sensor_acclima: unrecognized responseArray: {}".format(responseArray))
            return

        location_info = ("_" + str(location)) if location else ""
        variable_prefix = "meter_" + address + location_info

        set_value_float(measurements, variable_prefix + "_count_vwc", responseArray[0], SenmlUnits.SENML_UNIT_COUNTER)
        set_value_float(measurements, variable_prefix + "_temp", responseArray[1], SenmlUnits.SENML_UNIT_DEGREES_CELSIUS)
        set_value_float(measurements, variable_prefix + "_soil_ec", responseArray[2], "uS/cm")

        if model == 'ter12': #apply functions
            from math import pow
            calibratedCountsVWC = float(responseArray[0])
            VWCmineral = 3.879E-4 * calibratedCountsVWC - 0.6956 #mineral soil calibration
            VWCsoilless = 6.771E-10 * pow(calibratedCountsVWC, 3) - 5.105E-6 * pow(calibratedCountsVWC, 2) + 1.302E-2 * calibratedCountsVWC - 10.848 #soilless substrate calibration
            VWCdielectric = pow(2.887E-9 * pow(calibratedCountsVWC, 3) - 2.08E-5 * pow(calibratedCountsVWC, 2) + 5.276E-2 * calibratedCountsVWC - 43.39, 2)

            set_value_float(measurements, variable_prefix + "_vwc_mineral", VWCmineral * 100, SenmlSecondaryUnits.SENML_SEC_UNIT_PERCENT)
            set_value_float(measurements, variable_prefix + "_vwc_soilless", VWCsoilless * 100, SenmlSecondaryUnits.SENML_SEC_UNIT_PERCENT)
            set_value_float(measurements, variable_prefix + "_vwc_dielectric", VWCdielectric, SenmlSecondaryUnits.SENML_SEC_UNIT_PERCENT)
    except Exception as e:
        logging.exception(e, "Error processing meter sdi responseArray: [{}]".format(responseArray))


def parse_sensor_acclima(address, responseArray, measurements, location=None):
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


def parse_sensor_implexx(address, responseArray, measurements, location=None):
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


def parse_sensor_licor(address, responseArray, measurements, location=None):
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


def current_sense_4_20mA(measurements):
    import utime

    for i in range(1, 3):
        measure_4_20_mA_on_port(measurements, i)

    sleep_ms(200)


def measure_4_20_mA_on_port(measurements, port_id):
    from machine import Pin
    import gpio_handler
    from sensors import analog_generic

    port_enabled = cfg.get("_4_20_SNSR_{}_ENABLE".format(port_id))
    port_formula = cfg.get("_4_20_SNSR_{}_FORMULA".format(port_id))

    if port_enabled:
        sensor_on_pin = cfg.get("_UC_IO_SNSR_GND_4_20_SNSR_{}_ON".format(port_id))
        if not sensor_on_pin:
            # in folllowing label, ON is written in greek...
            sensor_on_pin = cfg.get("_UC_IO_SNSR_GND_4_20_SNSR_{}_ΟΝ".format(port_id))

        sensor_out_pin = cfg.get("_CUR_SNSR_OUT_{}".format(port_id))

        _CURRENT_OFFSET_MA = 0.6 # fix for the deviation of values

        try:
            gpio_handler.set_pin_value(cfg.get("_UC_IO_CUR_SNS_ON"), 1)
            gpio_handler.set_pin_value(sensor_on_pin, 1)

            raw_mV = analog_generic.get_reading(sensor_out_pin)
            current_mA = round((raw_mV / (cfg.get("_SHUNT_OHMS") * cfg.get("_INA_GAIN"))) * 100) / 100

            if current_mA > 3: # do apply offset
                current_mA += _CURRENT_OFFSET_MA

                # if current_mA < 4:
                #     current_mA = 4

            logging.debug("ANLG SENSOR @ pin {}: {} mV, Current = {} mA".format(sensor_out_pin, raw_mV, current_mA))
            set_value_float(measurements, "4-20_{}_current".format(port_id), current_mA, SenmlSecondaryUnits.SENML_SEC_UNIT_MILLIAMPERE)

            execute_transformation(measurements, "4-20_{}_current".format(port_id), current_mA, port_formula)

            gpio_handler.set_pin_value(sensor_on_pin, 0)
            gpio_handler.set_pin_value(cfg.get("_UC_IO_CUR_SNS_ON"), 0)
        except Exception as e:
            logging.exception(e, "Error getting current sensor output: ID: {}".format(port_id))


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
