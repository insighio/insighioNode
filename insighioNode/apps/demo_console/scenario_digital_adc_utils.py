import logging
from . import cfg

from external.kpn_senml.senml_unit import SenmlUnits, SenmlSecondaryUnits
from .dictionary_utils import set_value, set_value_int, set_value_float


def shield_measurements(measurements):
    # up to 2 I2C sensors
    meas_key_name = None

    for n in range(1, 3):
        meas_key_name = "_MEAS_I2C_" + str(n)
        i2c_config = cfg.get(meas_key_name)
        if i2c_config and cfg.has("_UC_IO_I2C_SDA") and cfg.has("_UC_IO_I2C_SCL") and i2c_config != cfg.get("_CONST_MEAS_DISABLED"):
            logging.debug("Getting measurement for [{}] from sensor [{}]".format(meas_key_name, i2c_config))
            read_i2c_sensor(cfg.get("_UC_IO_I2C_SDA"), cfg.get("_UC_IO_I2C_SCL"), i2c_config, measurements)

    # up to 3 Digital/Analog sensors
    for n in range(1, 4):
        meas_key_name = "_MEAS_ANALOG_DIGITAL_P" + str(n)
        pin_name = "_UC_IO_ANALOG_DIGITAL_P" + str(n)
        transformation_key = "_MEAS_ANALOG_DIGITAL_P" + str(n) + "_TRANSFORMATION"
        meas_key = cfg.get(meas_key_name)
        pin = cfg.get(pin_name)

        if pin is None and n == 1:  # backward compatibility towards v1.2
            pin = 32

        transformation = cfg.get(transformation_key)
        if meas_key is not None and pin is not None and meas_key != cfg.get("_CONST_MEAS_DISABLED"):
            logging.debug("Getting measurement for [{}] from sensor [{}] @ pin [{}]".format(meas_key_name, meas_key, pin))
            read_analog_digital_sensor(pin, meas_key, measurements, "adp" + str(n), transformation)


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
        (temp, humidity) = temp_hum_sens.get_reading(cfg.get("_UC_IO_I2C_SDA"), cfg.get("_UC_IO_I2C_SCL"))
        set_value_float(
            measurements,
            sensor_name + "_temp",
            temp,
            SenmlUnits.SENML_UNIT_DEGREES_CELSIUS,
        )
        set_value_float(
            measurements,
            sensor_name + "_humidity",
            humidity,
            SenmlUnits.SENML_UNIT_RELATIVE_HUMIDITY,
        )

    elif sensor_name == "scd30":
        from sensors import scd30

        co2, temp, hum = scd30.get_reading(cfg.get("_UC_IO_I2C_SDA"), cfg.get("_UC_IO_I2C_SCL"))
        set_value_float(
            measurements,
            sensor_name + "_co2",
            co2,
            SenmlSecondaryUnits.SENML_SEC_UNIT_PARTS_PER_MILLION,
        )
        set_value_float(
            measurements,
            sensor_name + "_temp",
            temp,
            SenmlUnits.SENML_UNIT_DEGREES_CELSIUS,
        )
        set_value_float(
            measurements,
            sensor_name + "_humidity",
            hum,
            SenmlUnits.SENML_UNIT_RELATIVE_HUMIDITY,
        )

    elif sensor_name == "bme680":
        from sensors import bme680

        (pressure, temperature, humidity, gas) = bme680.get_reading(cfg.get("_UC_IO_I2C_SDA"), cfg.get("_UC_IO_I2C_SCL"))
        set_value_float(
            measurements,
            sensor_name + "_pressure",
            pressure,
            SenmlSecondaryUnits.SENML_SEC_UNIT_HECTOPASCAL,
        )
        set_value_float(
            measurements,
            sensor_name + "_humidity",
            humidity,
            SenmlUnits.SENML_UNIT_RELATIVE_HUMIDITY,
        )
        set_value_float(
            measurements,
            sensor_name + "_temp",
            temperature,
            SenmlUnits.SENML_UNIT_DEGREES_CELSIUS,
        )
        set_value_float(measurements, sensor_name + "_gas", gas, SenmlUnits.SENML_UNIT_OHM)
    elif sensor_name == "sunrise":
        # read senseair sunrise sensor
        from sensors import senseair_sunrise as sens

        (co2, co2_temp) = sens.get_reading(
            cfg.get("_UC_IO_I2C_SDA"),
            cfg.get("_UC_IO_I2C_SCL"),
            cfg.get("_SENSAIR_EN_PIN_NUM"),
            cfg.get("_SENSAIR_nRDY_PIN_NUM"),
        )
        set_value_int(
            measurements,
            sensor_name + "_co2",
            co2,
            SenmlSecondaryUnits.SENML_SEC_UNIT_PARTS_PER_MILLION,
        )
        set_value_float(
            measurements,
            sensor_name + "_temp",
            co2_temp,
            SenmlUnits.SENML_UNIT_DEGREES_CELSIUS,
        )
    elif sensor_name == "scd4x":
        from sensors import scd4x

        scd4x.init(cfg.get("_UC_IO_I2C_SCL"), cfg.get("_UC_IO_I2C_SDA"))
        (co2, temp, rh) = scd4x.get_reading()
        set_value_int(
            measurements,
            sensor_name + "_co2",
            co2,
            SenmlSecondaryUnits.SENML_SEC_UNIT_PARTS_PER_MILLION,
        )
        set_value_float(
            measurements,
            sensor_name + "_temp",
            temp,
            SenmlUnits.SENML_UNIT_DEGREES_CELSIUS,
        )
        set_value_float(
            measurements,
            sensor_name + "_humidity",
            rh,
            SenmlUnits.SENML_UNIT_RELATIVE_HUMIDITY,
        )
    else:
        logging.error("read_i2c_sensor - Sensor not supported: [" + sensor_name + "]")


def read_analog_digital_sensor(data_pin, sensor_name, measurements, position, formula=None):
    logging.info("read_analog_digital_sensor - Reading Sensor [{}] at pin [{}]".format(sensor_name, data_pin))
    sensor_name = sensor_name.split("-")[0].strip()
    if sensor_name == "analog" or sensor_name == "generic analog":  # generic analog is kept for backward compatibility
        from sensors import analog_generic

        volt_analog = analog_generic.get_reading(data_pin)
        meas_name = "adc_" + position + "_volt"
        set_value(
            measurements,
            meas_name,
            volt_analog,
            SenmlSecondaryUnits.SENML_SEC_UNIT_MILLIVOLT,
        )
        default_formula = "v"
        if formula is not None and formula != default_formula:
            execute_formula(measurements, meas_name, volt_analog, formula)

    elif sensor_name == "dht11" or sensor_name == "dht22":
        from sensors import dht

        (dht_temp, dht_hum) = dht.get_reading(data_pin, "DHT11" if sensor_name == "dht11" else "DHT22")
        set_value_float(
            measurements,
            sensor_name + "_" + position + "_temp",
            dht_temp,
            SenmlUnits.SENML_UNIT_DEGREES_CELSIUS,
        )
        set_value_float(
            measurements,
            sensor_name + "_" + position + "_humidity",
            dht_hum,
            SenmlUnits.SENML_UNIT_RELATIVE_HUMIDITY,
        )

    elif sensor_name == "ds18x20":
        from sensors import ds18x20

        temperature = ds18x20.get_reading(data_pin)
        set_value_float(
            measurements,
            sensor_name + "_" + position + "_temp",
            temperature,
            SenmlUnits.SENML_UNIT_DEGREES_CELSIUS,
        )

    else:
        logging.error("read_analog_digital_sensor - Sensor not supported: [" + sensor_name + "]")


def execute_formula(measurements, name, raw_value, formula):
    try:
        formula = formula.replace("v", str(raw_value))
        to_execute = "v_transformed=({})".format(formula)
        namespace = {}
        exec(to_execute, namespace)
        print("namespace: " + str(namespace))
        set_value_float(measurements, name + "_trans", namespace["v_transformed"])
    except Exception as e:
        logging.exception(
            e,
            "formula name:{}, raw_value:{}, code:{}".format(name, raw_value, formula),
        )
        pass
