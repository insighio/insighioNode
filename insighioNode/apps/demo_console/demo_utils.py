import utime
import gpio_handler
import device_info
import sensors
import logging
from . import demo_config as cfg
from external.kpn_senml.senml_unit import SenmlUnits
from external.kpn_senml.senml_unit import SenmlSecondaryUnits


def device_init():
    if cfg._BOARD_TYPE == cfg._CONST_BOARD_TYPE_ESP_GEN_1:
        return

    gpio_handler.set_pin_value(cfg._UC_IO_LOAD_PWR_SAVE_OFF, 1)
    if cfg._BOARD_TYPE == cfg._CONST_BOARD_TYPE_SDI_12:
        gpio_handler.set_pin_value(cfg._UC_IO_SENSOR_PWR_SAVE_OFF, 1)


def device_deinit():
    if cfg._BOARD_TYPE == cfg._CONST_BOARD_TYPE_ESP_GEN_1:
        return

    gpio_handler.set_pin_value(cfg._UC_IO_LOAD_PWR_SAVE_OFF, 0)
    if cfg._BOARD_TYPE == cfg._CONST_BOARD_TYPE_SDI_12:
        gpio_handler.set_pin_value(cfg._UC_IO_SENSOR_PWR_SAVE_OFF, 0)


def watchdog_reset():
    # first reset internal hardware watchdog
    device_info.wdt_reset()

    # then reset external hardware watchdog
    if cfg._BOARD_TYPE != cfg._CONST_BOARD_TYPE_ESP_GEN_1:
        gpio_handler.timed_pin_pull_up(cfg._UC_IO_WATCHDOG_RESET, 500)


def set_value(measurements, key, value, unit=None):
    if value is not None:
        record = {"value": value}
        if unit is not None:
            record["unit"] = unit
        measurements[key] = record


def set_value_int(measurements, key, value, unit=None):
    if value is not None:
        set_value(measurements, key, round(value), unit)


def set_value_float(measurements, key, value, unit=None, precision=2):
    if value is not None:
        if isinstance(value, str):
            value = float(value)
        try:
            set_value(measurements, key, float("%0.*f" % (precision, value)), unit)
        except Exception as e:
            logging.exception(e, "set_value_float error: [{}]".format(value))


# functions
def get_measurements(cfg):
    measurements = {}

    if cfg._MEAS_BATTERY_STAT_ENABLE:
        (vbatt, current) = read_battery_voltage_and_current()
        set_value_int(measurements, "vbatt", vbatt, SenmlSecondaryUnits.SENML_SEC_UNIT_MILLIVOLT)
        set_value_int(measurements, "current", current, SenmlSecondaryUnits.SENML_SEC_UNIT_MILLIAMPERE)

    if cfg._MEAS_BOARD_STAT_ENABLE:
        (mem_alloc, mem_free) = device_info.get_heap_memory()
        set_value(measurements, "reset_cause", device_info.get_reset_cause())
        set_value(measurements, "mem_alloc", mem_alloc, SenmlUnits.SENML_UNIT_BYTE)
        set_value(measurements, "mem_free", mem_free, SenmlUnits.SENML_UNIT_BYTE)
        if cfg._MEAS_TEMP_UNIT_IS_CELSIUS:
            set_value_float(measurements, "cpu_temp", device_info.get_cpu_temp(), SenmlUnits.SENML_UNIT_DEGREES_CELSIUS)
        else:
            set_value_float(measurements, "cpu_temp", device_info.get_cpu_temp(False), SenmlSecondaryUnits.SENML_SEC_UNIT_FAHRENHEIT)

    sensors.set_sensor_power_on(cfg._UC_IO_SENSOR_SWITCH_ON)

    # read internal temperature and humidity
    if cfg._MEAS_BOARD_SENSE_ENABLE:
        if cfg._UC_INTERNAL_TEMP_HUM_SENSOR == cfg._CONST_SENSOR_SI7021:
            from sensors import si7021 as sens
        elif cfg._UC_INTERNAL_TEMP_HUM_SENSOR == cfg._UC_INTERNAL_TEMP_HUM_SENSOR:
            from sensors import sht40 as sens
        (board_temp, board_humidity) = sens.get_reading(cfg._UC_IO_I2C_SDA, cfg._UC_IO_I2C_SCL)
        set_value_float(measurements, "board_temp", board_temp, SenmlUnits.SENML_UNIT_DEGREES_CELSIUS)
        set_value_float(measurements, "board_humidity", board_humidity, SenmlUnits.SENML_UNIT_RELATIVE_HUMIDITY)

    if cfg._BOARD_TYPE == cfg._CONST_BOARD_TYPE_SDI_12:
        sdi12_board_measurements(measurements)
    else:
        default_board_measurements(measurements)

    sensors.set_sensor_power_off(cfg._UC_IO_SENSOR_SWITCH_ON)

    return measurements


def read_battery_voltage_and_current():
    # BATT VOLTAGE & CURR measurement
    current = None
    gpio_handler.set_pin_value(cfg._UC_IO_BAT_MEAS_ON, 1)
    if cfg._BOARD_TYPE != cfg._CONST_BOARD_TYPE_ESP_GEN_1:
        gpio_handler.set_pin_value(cfg._UC_IO_CHARGER_OFF, 1)
    utime.sleep_ms(500)
    vbatt = gpio_handler.get_input_voltage(cfg._UC_IO_BAT_READ, cfg._BAT_VDIV, cfg._BAT_ATT)
    if cfg._BOARD_TYPE != cfg._CONST_BOARD_TYPE_ESP_GEN_1:
        vina_mV = gpio_handler.get_input_voltage(cfg._UC_IO_CUR_READ, voltage_divider=cfg._CUR_VDIV, attn=cfg._CUR_ATT)
        current = (vina_mV - cfg._CUR_VREF_mV) / (cfg._CUR_RSENSE * cfg._CUR_GAIN)
        # changed the order of the following two lines. evaluate if correct.
        gpio_handler.set_pin_value(cfg._UC_IO_CHARGER_OFF, 0)
    gpio_handler.set_pin_value(cfg._UC_IO_BAT_MEAS_ON, 0)
    return (vbatt, current)


def default_board_measurements(measurements):
    if cfg._MEAS_I2C_1 and cfg._MEAS_I2C_1 != cfg._CONST_MEAS_DISABLED:
        read_i2c_sensor(cfg._UC_IO_I2C_SDA, cfg._UC_IO_I2C_SCL, cfg._MEAS_I2C_1, measurements)

    if cfg._MEAS_I2C_2 and cfg._MEAS_I2C_2 != cfg._CONST_MEAS_DISABLED:
        read_i2c_sensor(cfg._UC_IO_I2C_SDA, cfg._UC_IO_I2C_SCL, cfg._MEAS_I2C_2, measurements)

    if hasattr(cfg, '_MEAS_ANALOG_P1') and cfg._MEAS_ANALOG_P1 != cfg._CONST_MEAS_DISABLED:
        read_analog_digital_sensor(cfg._UC_IO_ANALOG_P1, cfg._MEAS_ANALOG_P1, measurements, "ap1")

    if hasattr(cfg, '_MEAS_ANALOG_P2') and cfg._MEAS_ANALOG_P2 != cfg._CONST_MEAS_DISABLED:
        read_analog_digital_sensor(cfg._UC_IO_ANALOG_P2, cfg._MEAS_ANALOG_P2, measurements, "ap2")

    if hasattr(cfg, '_MEAS_ANALOG_DIGITAL_P1') and cfg._MEAS_ANALOG_DIGITAL_P1 != cfg._CONST_MEAS_DISABLED:
        read_analog_digital_sensor(cfg._UC_IO_ANALOG_DIGITAL_P1, cfg._MEAS_ANALOG_DIGITAL_P1, measurements, "adp1")

    if hasattr(cfg, '_MEAS_ANALOG_DIGITAL_P2') and cfg._MEAS_ANALOG_DIGITAL_P2 != cfg._CONST_MEAS_DISABLED:
        read_analog_digital_sensor(cfg._UC_IO_ANALOG_DIGITAL_P2, cfg._MEAS_ANALOG_DIGITAL_P2, measurements, "adp2")

    # temporarly placed here till a wizard is made
    read_scale(cfg._UC_IO_SCALE_CLOCK_PIN, cfg._UC_IO_SCALE_DATA_PIN, measurements)


def read_scale(clock_pin, data_pin, measurements):
    from external.hx711.hx711_gpio import HX711
    from machine import Pin
    pin_OUT = Pin(data_pin, Pin.IN, pull=Pin.PULL_DOWN)
    pin_SCK = Pin(clock_pin, Pin.OUT)
    hx = HX711(pin_SCK, pin_OUT)
    hx.set_gain(128)
    utime.sleep_ms(50)
    times = 15
    logging.debug("scale offset: {}, scale: {}".format(hx.OFFSET, hx.SCALE))

    hx.set_offset(79000)
    hx.set_scale(21.4)
    hx.read_average(times)
    weight = (hx.read_average(times) - hx.OFFSET) / hx.SCALE
    set_value_float(measurements, "scale_weight", weight, SenmlUnits.SENML_UNIT_GRAM)


# <option>tsl2561 - luminosity</option>
# <option>si7021  - temperature / humidity</option>
# <option>scd30   - C02 / temperature / humidity</option>
# <option>bme680  - gap / temperature / humidity</option>
def read_i2c_sensor(i2c_sda_pin, i2c_scl_pin, sensor_name, measurements):
    sensor_name = sensor_name.split("-")[0].strip()

    if sensor_name == "tsl2561":
        from sensors import tsl2561
        light = tsl2561.get_reading(i2c_sda_pin, i2c_scl_pin)
        set_value_int(measurements, sensor_name + "_light", light, SenmlUnits.SENML_UNIT_LUX)

    elif sensor_name == "si7021":
        from sensors import si7021
        (board_temp, board_humidity) = si7021.get_reading(cfg._UC_IO_I2C_SDA, cfg._UC_IO_I2C_SCL)
        set_value_float(measurements, sensor_name + "_temp", board_temp, SenmlUnits.SENML_UNIT_DEGREES_CELSIUS)
        set_value_float(measurements, sensor_name + "_humidity", board_humidity, SenmlUnits.SENML_UNIT_RELATIVE_HUMIDITY)

    elif sensor_name == "scd30":
        from sensors import scd30
        co2, temp, hum = scd30.get_reading(cfg._UC_IO_I2C_SDA, cfg._UC_IO_I2C_SCL)
        set_value_float(measurements, sensor_name + "_co2", co2, SenmlSecondaryUnits.SENML_SEC_UNIT_PARTS_PER_MILLION)
        set_value_float(measurements, sensor_name + "_temp", temp, SenmlUnits.SENML_UNIT_DEGREES_CELSIUS)
        set_value_float(measurements, sensor_name + "_humidity", hum, SenmlUnits.SENML_UNIT_RELATIVE_HUMIDITY)

    elif sensor_name == "bme680":
        from sensors import bme680
        (pressure, temperature, humidity, gas) = bme680.get_reading(cfg._UC_IO_I2C_SDA, cfg._UC_IO_I2C_SCL)
        set_value_float(measurements, sensor_name + "_pressure", pressure, SenmlSecondaryUnits.SENML_SEC_UNIT_HECTOPASCAL)
        set_value_float(measurements, sensor_name + "_humidity", humidity, SenmlUnits.SENML_UNIT_RELATIVE_HUMIDITY)
        set_value_float(measurements, sensor_name + "_temp", temperature, SenmlUnits.SENML_UNIT_DEGREES_CELSIUS)
        set_value_float(measurements, sensor_name + "_gas", gas, SenmlUnits.SENML_UNIT_OHM)
    else:
        logging.error("read_i2c_sensor - Sensor not supported: [" + sensor_name + "]")


def read_analog_digital_sensor(data_pin, sensor_name, measurements, position):
    logging.info("read_analog_digital_sensor - Reading Sensor [{}] at pin [{}]".format(sensor_name, data_pin))
    sensor_name = sensor_name.split("-")[0].strip()
    if sensor_name == "generic analog":
        from sensors import analog_generic
        volt_analog = analog_generic.get_reading(data_pin, cfg._BAT_VDIV)
        set_value(measurements, "adc_" + position + "_volt", volt_analog, SenmlSecondaryUnits.SENML_SEC_UNIT_MILLIVOLT)

    elif sensor_name == "dht11" or sensor_name == "dht22":
        from sensors import dht
        (dht_temp, dht_hum) = dht.get_reading(data_pin, 'DHT11' if sensor_name == "dht11" else 'DHT22')
        set_value_float(measurements, sensor_name + "_" + position + "_temp", dht_temp, SenmlUnits.SENML_UNIT_DEGREES_CELSIUS)
        set_value_float(measurements, sensor_name + "_" + position + "_humidity", dht_hum, SenmlUnits.SENML_UNIT_RELATIVE_HUMIDITY)

    elif sensor_name == "ds18x20":
        from sensors import ds18x20
        temperature = ds18x20.get_reading(data_pin)
        set_value_float(measurements, sensor_name + "_" + position + "_temp", temperature, SenmlUnits.SENML_UNIT_DEGREES_CELSIUS)

    else:
        logging.error("read_analog_digital_sensor - Sensor not supported: [" + sensor_name + "]")


def sdi12_board_measurements(measurements):
    utime.sleep_ms(cfg._SDI12_WARM_UP_TIME_MSEC)

    if cfg._SDI12_SENSOR_1_ENABLED or cfg._SDI12_SENSOR_2_ENABLED:
        from external.microsdi12.microsdi12 import SDI12

        sdi12 = None

        try:
            sdi12 = SDI12(cfg._UC_IO_DRV_IN, cfg._UC_IO_RCV_OUT, cfg._UC_IO_DRV_RCV_ON, 1)

            if cfg._SDI12_SENSOR_1_ENABLED:
                read_sdi12_sensor(sdi12, cfg._SDI12_SENSOR_1_ADDRESS, measurements)

            if cfg._SDI12_SENSOR_2_ENABLED:
                read_sdi12_sensor(sdi12, cfg._SDI12_SENSOR_2_ADDRESS, measurements)
        except Exception as e:
            logging.exception(e, "Exception while reading SDI-12 data")
        finally:
            if sdi12:
                sdi12.close()


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
