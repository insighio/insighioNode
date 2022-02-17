import utime
import logging
import gpio_handler
import device_info
import sensors
from . import demo_config as cfg
from external.kpn_senml.senml_unit import SenmlUnits
from external.kpn_senml.senml_unit import SenmlSecondaryUnits
from apps.demo_console.dictionary_utils import set_value, set_value_int, set_value_float


def get_config(key):
    return getattr(cfg, key) if hasattr(cfg, key) else None


def device_init():
    if cfg._BOARD_TYPE == cfg._CONST_BOARD_TYPE_ESP_GEN_1:
        bq_charger_setup()
    else:
        if hasattr(cfg, "_UC_IO_LOAD_PWR_SAVE_OFF") and cfg._UC_IO_LOAD_PWR_SAVE_OFF is not None:
            gpio_handler.set_pin_value(cfg._UC_IO_LOAD_PWR_SAVE_OFF, 1)

        if hasattr(cfg, "_UC_IO_SENSOR_PWR_SAVE_OFF") and cfg._UC_IO_SENSOR_PWR_SAVE_OFF is not None:
            gpio_handler.set_pin_value(cfg._UC_IO_SENSOR_PWR_SAVE_OFF, 1)
    if hasattr(cfg, "_NOTIFICATION_LED_ENABLED"):
        device_info.set_led_enabled(cfg._NOTIFICATION_LED_ENABLED)


def bq_charger_setup():
    from machine import I2C, Pin
    p_snsr = Pin(cfg._UC_IO_SENSOR_SWITCH_ON, Pin.OUT)
    try:
        p_snsr.on()
        i2c = I2C(0, scl=Pin(cfg._UC_IO_I2C_SCL), sda=Pin(cfg._UC_IO_I2C_SDA))
        bq_addr = 107
        i2c.writeto_mem(bq_addr, 5, b'\x84')
        i2c.writeto_mem(bq_addr, 0, b'\x22')
    except Exception as e:
        logging.exception(e, "Error initializing BQ charger")

    try:
        p_snsr.off()
    except Exception as e:
        pass


def device_deinit():
    if hasattr(cfg, "_UC_IO_LOAD_PWR_SAVE_OFF") and cfg._UC_IO_LOAD_PWR_SAVE_OFF is not None:
        gpio_handler.set_pin_value(cfg._UC_IO_LOAD_PWR_SAVE_OFF, 0)

    if hasattr(cfg, "_UC_IO_SENSOR_PWR_SAVE_OFF") and cfg._UC_IO_SENSOR_PWR_SAVE_OFF is not None:
        gpio_handler.set_pin_value(cfg._UC_IO_SENSOR_PWR_SAVE_OFF, 0)


def watchdog_reset():
    # first reset internal hardware watchdog
    device_info.wdt_reset()

    # then reset external hardware watchdog
    if hasattr(cfg, "_UC_IO_WATCHDOG_RESET"):
        gpio_handler.timed_pin_pull_up(cfg._UC_IO_WATCHDOG_RESET, 500)


# functions
def get_measurements(cfg):
    measurements = {}

    try:
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
    except Exception as e:
        logging.error("unable to measure board sensors")

    sensors.set_sensor_power_on(cfg._UC_IO_SENSOR_SWITCH_ON)

    # read internal temperature and humidity
    try:
        if cfg._MEAS_BOARD_SENSE_ENABLE:
            if cfg._UC_INTERNAL_TEMP_HUM_SENSOR == cfg._CONST_SENSOR_SI7021:
                from sensors import si7021 as sens
            elif cfg._UC_INTERNAL_TEMP_HUM_SENSOR == cfg._UC_INTERNAL_TEMP_HUM_SENSOR:
                from sensors import sht40 as sens
            (board_temp, board_humidity) = sens.get_reading(cfg._UC_IO_I2C_SDA, cfg._UC_IO_I2C_SCL)
            set_value_float(measurements, "board_temp", board_temp, SenmlUnits.SENML_UNIT_DEGREES_CELSIUS)
            set_value_float(measurements, "board_humidity", board_humidity, SenmlUnits.SENML_UNIT_RELATIVE_HUMIDITY)

        if cfg._BOARD_TYPE == cfg._CONST_BOARD_TYPE_SDI_12 or cfg._BOARD_TYPE == cfg._CONST_BOARD_TYPE_ESP_GEN_SHIELD_SDI12:
            from . import demo_sdi12_utils
            demo_sdi12_utils.sdi12_board_measurements(measurements)
        else:
            default_board_measurements(measurements)
    except Exception as e:
        logging.exception(e, "unable to complete sensor measurements")

    sensors.set_sensor_power_off(cfg._UC_IO_SENSOR_SWITCH_ON)

    return measurements


def read_battery_voltage_and_current():
    # BATT VOLTAGE & CURR measurement
    current = None
    gpio_handler.set_pin_value(cfg._UC_IO_BAT_MEAS_ON, 1)
    if hasattr(cfg, "_UC_IO_CHARGER_OFF"):
        gpio_handler.set_pin_value(cfg._UC_IO_CHARGER_OFF, 1)

    vbatt = gpio_handler.get_input_voltage(cfg._UC_IO_BAT_READ, cfg._BAT_VDIV, cfg._BAT_ATT)

    if hasattr(cfg, "_UC_IO_CHARGER_OFF") and hasattr(cfg, "_UC_IO_CUR_READ"):
        vina_mV = gpio_handler.get_input_voltage(cfg._UC_IO_CUR_READ, voltage_divider=cfg._CUR_VDIV, attn=cfg._CUR_ATT)
        current = (vina_mV - cfg._CUR_VREF_mV) / (cfg._CUR_RSENSE * cfg._CUR_GAIN)
        # changed the order of the following two lines. evaluate if correct.
        gpio_handler.set_pin_value(cfg._UC_IO_CHARGER_OFF, 0)
    gpio_handler.set_pin_value(cfg._UC_IO_BAT_MEAS_ON, 0)
    return (vbatt, current)


def default_board_measurements(measurements):
    if cfg._MEAS_I2C_1 and hasattr(cfg, "_UC_IO_I2C_SDA") and hasattr(cfg, "_UC_IO_I2C_SCL") and cfg._MEAS_I2C_1 != cfg._CONST_MEAS_DISABLED:
        read_i2c_sensor(cfg._UC_IO_I2C_SDA, cfg._UC_IO_I2C_SCL, cfg._MEAS_I2C_1, measurements)

    if cfg._MEAS_I2C_2 and hasattr(cfg, "_UC_IO_I2C_SDA") and hasattr(cfg, "_UC_IO_I2C_SCL") and cfg._MEAS_I2C_2 != cfg._CONST_MEAS_DISABLED:
        read_i2c_sensor(cfg._UC_IO_I2C_SDA, cfg._UC_IO_I2C_SCL, cfg._MEAS_I2C_2, measurements)

    if hasattr(cfg, '_MEAS_ANALOG_P1') and hasattr(cfg, "_UC_IO_ANALOG_P1") and cfg._MEAS_ANALOG_P1 != cfg._CONST_MEAS_DISABLED:
        read_analog_digital_sensor(cfg._UC_IO_ANALOG_P1, cfg._MEAS_ANALOG_P1, measurements, "ap1")

    if hasattr(cfg, '_MEAS_ANALOG_P2') and hasattr(cfg, "_UC_IO_ANALOG_P2") and cfg._MEAS_ANALOG_P2 != cfg._CONST_MEAS_DISABLED:
        read_analog_digital_sensor(cfg._UC_IO_ANALOG_P2, cfg._MEAS_ANALOG_P2, measurements, "ap2")

    if hasattr(cfg, '_MEAS_ANALOG_DIGITAL_P1') and hasattr(cfg, "_UC_IO_ANALOG_DIGITAL_P1") and cfg._MEAS_ANALOG_DIGITAL_P1 != cfg._CONST_MEAS_DISABLED:
        read_analog_digital_sensor(cfg._UC_IO_ANALOG_DIGITAL_P1, cfg._MEAS_ANALOG_DIGITAL_P1, measurements, "adp1", cfg._MEAS_ANALOG_DIGITAL_P1_TRANSFORMATION if hasattr(cfg, "_MEAS_ANALOG_DIGITAL_P1_TRANSFORMATION") else None)

    if hasattr(cfg, '_MEAS_ANALOG_DIGITAL_P2') and hasattr(cfg, "_UC_IO_ANALOG_DIGITAL_P2") and cfg._MEAS_ANALOG_DIGITAL_P2 != cfg._CONST_MEAS_DISABLED:
        read_analog_digital_sensor(cfg._UC_IO_ANALOG_DIGITAL_P2, cfg._MEAS_ANALOG_DIGITAL_P2, measurements, "adp2", cfg._MEAS_ANALOG_DIGITAL_P2_TRANSFORMATION if hasattr(cfg, "_MEAS_ANALOG_DIGITAL_P2_TRANSFORMATION") else None)

    if hasattr(cfg, '_MEAS_SCALE_ENABLED') and cfg._MEAS_SCALE_ENABLED:
        read_scale(measurements)

    if hasattr(cfg, '_MEAS_KEYVALUE') and cfg._MEAS_KEYVALUE:
        add_explicit_key_values(measurements)


def add_explicit_key_values(measurements):
    for key in cfg._MEAS_KEYVALUE:
        set_value(measurements, key, cfg._MEAS_KEYVALUE[key])


def read_scale(measurements):
    from sensors import hx711

    weight = hx711.get_reading(cfg._UC_IO_SCALE_DATA_PIN,
                               cfg._UC_IO_SCALE_CLOCK_PIN,
                               cfg._UC_IO_SCALE_SPI_PIN,
                               cfg._UC_IO_SCALE_OFFSET if hasattr(cfg, '_UC_IO_SCALE_OFFSET') else None,
                               cfg._UC_IO_SCALE_SCALE if hasattr(cfg, '_UC_IO_SCALE_SCALE') else None)

    weight = weight if weight > 0 or weight < -100 else 0
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

    elif sensor_name == "sht20" or sensor_name == "sht40" or sensor_name == "si7021":
        if sensor_name == "sht20":
            from sensors import sht20 as temp_hum_sens
        elif sensor_name == "sht40":
            from sensors import sht40 as temp_hum_sens
        elif sensor_name == "si7021":
            from sensors import si7021 as temp_hum_sens
        (temp, humidity) = temp_hum_sens.get_reading(cfg._UC_IO_I2C_SDA, cfg._UC_IO_I2C_SCL)
        set_value_float(measurements, sensor_name + "_temp", temp, SenmlUnits.SENML_UNIT_DEGREES_CELSIUS)
        set_value_float(measurements, sensor_name + "_humidity", humidity, SenmlUnits.SENML_UNIT_RELATIVE_HUMIDITY)

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
    elif sensor_name == "sunrise":
        # read senseair sunrise sensor
        from sensors import senseair_sunrise as sens
        (co2, co2_temp) = sens.get_reading(cfg._UC_IO_I2C_SDA, cfg._UC_IO_I2C_SCL, cfg._SENSAIR_EN_PIN_NUM, cfg._SENSAIR_nRDY_PIN_NUM)
        set_value_int(measurements, sensor_name + "_co2", co2, SenmlSecondaryUnits.SENML_SEC_UNIT_PARTS_PER_MILLION)
        set_value_float(measurements, sensor_name + "_temp", co2_temp, SenmlUnits.SENML_UNIT_DEGREES_CELSIUS)
    else:
        logging.error("read_i2c_sensor - Sensor not supported: [" + sensor_name + "]")


def read_analog_digital_sensor(data_pin, sensor_name, measurements, position, transformator=None):
    logging.info("read_analog_digital_sensor - Reading Sensor [{}] at pin [{}]".format(sensor_name, data_pin))
    sensor_name = sensor_name.split("-")[0].strip()
    if sensor_name == "analog" or sensor_name == "generic analog":  # generic analog is kept for backward compatibility
        from sensors import analog_generic
        volt_analog = analog_generic.get_reading(data_pin)
        meas_name = "adc_" + position + "_volt"
        set_value(measurements, meas_name, volt_analog, SenmlSecondaryUnits.SENML_SEC_UNIT_MILLIVOLT)
        default_transformator = "v"
        if transformator is not None and transformator != default_transformator:
            execute_transformation(measurements, meas_name, volt_analog, transformator)

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


def execute_transformation(measurements, name, raw_value, transformator):
    try:
        transformator = transformator.replace('v', str(raw_value))
        to_execute = "v_transformed=({})".format(transformator)
        namespace = {}
        exec(to_execute, namespace)
        print("namespace: " + str(namespace))
        set_value(measurements, name + "_trans", namespace['v_transformed'])
    except Exception as e:
        logging.exception(e, "transformator name:{}, raw_value:{}, code:{}".format(name, raw_value, transformator))
        pass
