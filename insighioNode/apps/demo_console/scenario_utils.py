from utime import sleep_ms, ticks_ms, sleep_us
import logging
import gpio_handler
import device_info
import sensors
import gc

from . import cfg

from external.kpn_senml.senml_unit import SenmlUnits
from external.kpn_senml.senml_unit import SenmlSecondaryUnits
from .dictionary_utils import set_value, set_value_int, set_value_float
from . import message_buffer

_measurement_pause_timestamp_ms = 0

def device_init():
    if (
        device_info.get_hw_module_version() != device_info._CONST_ESP32
        and device_info.get_hw_module_version() != device_info._CONST_ESP32_WROOM
    ):
        device_info.bq_charger_exec(device_info.bq_charger_setup)
    else:
        gpio_handler.set_pin_value(cfg.get("_UC_IO_LOAD_PWR_SAVE_OFF"), 1)
        gpio_handler.set_pin_value(cfg.get("_UC_IO_SENSOR_PWR_SAVE_OFF"), 1)

    if cfg.get("_NOTIFICATION_LED_ENABLED"):
        if cfg.get("_UC_IO_RGB_DIN") and cfg.get("_UC_RGB_VDD"):
            device_info.set_led_enabled(cfg.get("_NOTIFICATION_LED_ENABLED"), cfg.get("_UC_RGB_VDD"), cfg.get("_UC_IO_RGB_DIN"))
        else:
            device_info.set_led_enabled(cfg.get("_NOTIFICATION_LED_ENABLED"))
    else:
        device_info.set_led_enabled(False)


def read_shield_chip_id():
    from machine import Pin, SoftI2C

    chip_id = None
    try:
        i2c = SoftI2C(scl=Pin(cfg.get("_UC_IO_I2C_SCL")), sda=Pin(cfg.get("_UC_IO_I2C_SDA")))
        chip_id = i2c.readfrom(cfg.get("_I2C_CHIP_ID_ADDRESS"), 3)
    except Exception as e:
        pass
    return chip_id


def device_deinit():
    gpio_handler.set_pin_value(cfg.get("_UC_IO_LOAD_PWR_SAVE_OFF"), 0)
    gpio_handler.set_pin_value(cfg.get("_UC_IO_SENSOR_PWR_SAVE_OFF"), 0)


def pause_background_measurements():
    global _measurement_pause_timestamp_ms
    logging.debug("Pausing Measurements")
    shield_name = cfg.get("_SELECTED_SHIELD")
    if shield_name == cfg.get("_CONST_SHIELD_ENVIRO"):
        from . import scenario_enviro_utils
        import utime
        scenario_enviro_utils._pcnt_active = False
        scenario_enviro_utils.pcnt_last_run_pause_timestamp_ms = utime.ticks_ms()
        #_measurement_pause_timestamp_ms = utime.ticks_ms()

def resume_background_measurements():
    global _measurement_pause_timestamp_ms
    logging.debug("Resuming Measurements")
    shield_name = cfg.get("_SELECTED_SHIELD")
    if shield_name == cfg.get("_CONST_SHIELD_ENVIRO"):
        from . import scenario_enviro_utils
        import utime
        scenario_enviro_utils._pcnt_active = True
        scenario_enviro_utils.pcnt_last_run_start_timestamp_ms = utime.ticks_ms()
        #scenario_enviro_utils._pcnt_pause_period_ms += utime.ticks_diff(utime.ticks_ms(), _measurement_pause_timestamp_ms)
        #logging.debug("...paused measurements for: {}".format(scenario_enviro_utils._pcnt_pause_period_ms))
        #_measurement_pause_timestamp_ms = -1

# functions
def get_measurements(cfg_dummy=None):
    measurements = {}

    try:
        if cfg.get("_MEAS_BATTERY_STAT_ENABLE"):
            vbatt = read_battery_voltage()
            set_value_int(
                measurements,
                "vbatt",
                vbatt,
                SenmlSecondaryUnits.SENML_SEC_UNIT_MILLIVOLT,
            )

        if cfg.get("_MEAS_BOARD_STAT_ENABLE"):
            (mem_alloc, mem_free) = device_info.get_heap_memory()
            set_value(measurements, "reset_cause", device_info.get_reset_cause())
            set_value(measurements, "mem_alloc", mem_alloc, SenmlUnits.SENML_UNIT_BYTE)
            set_value(measurements, "mem_free", mem_free, SenmlUnits.SENML_UNIT_BYTE)
            try:
                if cfg.get("_MEAS_TEMP_UNIT_IS_CELSIUS"):
                    set_value_float(
                        measurements,
                        "cpu_temp",
                        device_info.get_cpu_temp(),
                        SenmlUnits.SENML_UNIT_DEGREES_CELSIUS,
                    )
                else:
                    set_value_float(
                        measurements,
                        "cpu_temp",
                        device_info.get_cpu_temp(False),
                        SenmlSecondaryUnits.SENML_SEC_UNIT_FAHRENHEIT,
                    )
            except:
                logging.error("Error getting cpu_temp.")
    except Exception as e:
        logging.exception(e, "unable to measure board sensors")

    # enable sensors
    new_gnd_pin = cfg.get("_UC_IO_SENSOR_GND_ON")
    old_gnd_pin = cfg.get("_UC_IO_SENSOR_SWITCH_ON")

    sensor_pin = new_gnd_pin if new_gnd_pin is not None else old_gnd_pin
    gpio_handler.set_pin_value(sensor_pin, 1)

    # read internal temperature and humidity
    try:
        if cfg.get("_MEAS_BOARD_SENSE_ENABLE"):
            if cfg.get("_UC_INTERNAL_TEMP_HUM_SENSOR") == cfg.get("_CONST_SENSOR_SI7021"):
                from sensors import si7021 as sens
            elif cfg.get("_UC_INTERNAL_TEMP_HUM_SENSOR") == cfg.get("_CONST_SENSOR_SHT40"):
                from sensors import sht40 as sens

            (board_temp, board_humidity) = sens.get_reading(cfg.get("_UC_IO_I2C_SDA"), cfg.get("_UC_IO_I2C_SCL"))
            set_value_float(
                measurements,
                "board_temp",
                board_temp,
                SenmlUnits.SENML_UNIT_DEGREES_CELSIUS,
            )
            set_value_float(
                measurements,
                "board_humidity",
                board_humidity,
                SenmlUnits.SENML_UNIT_RELATIVE_HUMIDITY,
            )


        shield_name = cfg.get("_SELECTED_SHIELD")
        if shield_name is not None and (
            shield_name == cfg.get("_CONST_SHIELD_ADVIND") or shield_name == cfg.get("_CONST_SELECTED_SHIELD_ESP_GEN_SHIELD_SDI12")
        ):
            from . import scenario_advind_utils

            scenario_advind_utils.shield_measurements(measurements)
        elif shield_name == cfg.get("_CONST_SHIELD_ENVIRO"):
            from . import scenario_enviro_utils

            scenario_enviro_utils.shield_measurements(measurements)
        elif shield_name == cfg.get("_CONST_SHIELD_ACCELEROMETER"):
            shield_accel_measurements(measurements)
            delete_pulse_counter_state()
        else:  # if shield_name == cfg.get("_CONST_SHIELD_DIG_ANALOG"):
            default_board_measurements(measurements)
            delete_pulse_counter_state()

        if cfg.get("_MEAS_KEYVALUE"):
            add_explicit_key_values(measurements)

    except Exception as e:
        logging.exception(e, "unable to complete sensor measurements")

    # enable sensors
    gpio_handler.set_pin_value(sensor_pin, 0)

    return measurements


def delete_pulse_counter_state():
    import utils

    TIMESTAMP_FLAG_FILE = "/pcnt_last_read_timestamp"
    utils.deleteFlagFile(TIMESTAMP_FLAG_FILE)


def read_battery_voltage():
    # BATT VOLTAGE
    current = None
    gpio_handler.set_pin_value(cfg.get("_UC_IO_BAT_MEAS_ON"), 1)

    device_info.bq_charger_exec(device_info.bq_charger_set_charging_off)

    sleep_ms(50)

    vbatt = gpio_handler.get_input_voltage(cfg.get("_UC_IO_BAT_READ"), cfg.get("_BAT_VDIV"), cfg.get("_BAT_ATT"))

    device_info.bq_charger_exec(device_info.bq_charger_set_charging_on)
    gpio_handler.set_pin_value(cfg.get("_UC_IO_BAT_MEAS_ON"), 0)
    return vbatt


def default_board_measurements(measurements):
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

    if cfg.get("_SELECTED_SHIELD") == cfg.get("_CONST_SHIELD_SCALE"):
        if cfg.get("_MEAS_SCALE_ENABLED"):
            read_scale(measurements)
        read_scale_shield_temperature(measurements)


def add_explicit_key_values(measurements):
    try:
        for key in cfg.get("_MEAS_KEYVALUE"):
            set_value(measurements, key, cfg.get("_MEAS_KEYVALUE")[key])
    except:
        pass


def read_scale(measurements):
    weight_on_pin = cfg.get("_UC_IO_WEIGHT_ON")

    if weight_on_pin:
        sensors.set_sensor_power_on(weight_on_pin)

    import network

    wlan = network.WLAN(network.AP_IF)
    wlan_is_active = wlan.active()
    if not wlan_is_active:
        wlan.active(True)
        logging.debug("WiFi active: {}".format(wlan.active()))
    else:
        logging.debug("WiFi already active")

    from sensors import hx711

    weight = -1
    is_sensor_debug_on = cfg.get("_MEAS_SCALE_MONITORING_ENABLED")

    if is_sensor_debug_on:
        logging.setLevel(logging.DEBUG)

    while 1:
        weight = hx711.get_reading(
            cfg.get("_UC_IO_SCALE_DATA_PIN"),
            cfg.get("_UC_IO_SCALE_CLOCK_PIN"),
            cfg.get("_UC_IO_SCALE_SPI_PIN"),
            cfg.get("_UC_IO_SCALE_OFFSET"),
            cfg.get("_UC_IO_SCALE_SCALE"),
        )
        if not is_sensor_debug_on:
            break

        logging.debug("Detected weight: {}".format(weight))
        sleep_ms(10)

    if not wlan_is_active:
        wlan.active(False)

    weight = weight if weight > 0 or weight < -100 else 0
    set_value_float(measurements, "scale_weight", weight, SenmlUnits.SENML_UNIT_GRAM)

    if weight_on_pin:
        sensors.set_sensor_power_off(weight_on_pin)
    hx711.deinit_instance()


def read_scale_shield_temperature(measurements):
    from sensors import analog_generic

    if not cfg.has("_UC_IO_TEMP_SENSOR"):
        return None

    try:
        volt_analog = analog_generic.get_reading(cfg.get("_UC_IO_TEMP_SENSOR"))
        if volt_analog is None:
            return None
        else:
            set_value_float(
                measurements,
                "scale_temp",
                round((volt_analog - 400) / 19.5, 2),
                SenmlUnits.SENML_UNIT_DEGREES_CELSIUS,
            )
    except Exception as e:
        logging.exception(e, "unable to read temperature sensor")


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


def storeMeasurement(measurements, force_store=False):
    if cfg.get("_BATCH_UPLOAD_MESSAGE_BUFFER") is None and not force_store:
        logging.error("Batch upload not activated, ignoring")
        return False

    message_buffer.timestamp_measurements(measurements)
    return message_buffer.store_measurement(measurements, force_store)


def shield_accel_measurements(measurements):
    read_accelerometer(measurements, True)


def calculate_baseline(asm330Obj):
    from . import running_stats

    statsX = running_stats.RunningStats()
    statsY = running_stats.RunningStats()
    statsZ = running_stats.RunningStats()

    for i in range(0, 1000):
        (asm330_accX, asm330_accY, asm330_accZ) = asm330Obj.get_reading(True)
        if asm330_accX is None or asm330_accY is None or asm330_accZ is None:
            continue

        statsX.push(asm330_accX)
        statsY.push(asm330_accY)
        statsZ.push(asm330_accZ)

        sleep_us(100)

    return (statsX.mean(), statsY.mean(), statsZ.mean())


def storeAccellerometerMeasurement(measurement, statsX, statsY, statsZ, dev_is_operating, current_total, do_store_measurement=True):
    set_value_float(measurement, "asm330_accX", statsX.mean(), SenmlUnits.SENML_UNIT_ACCELERATION)
    set_value_float(measurement, "asm330_accY", statsY.mean(), SenmlUnits.SENML_UNIT_ACCELERATION)
    set_value_float(measurement, "asm330_accZ", statsZ.mean(), SenmlUnits.SENML_UNIT_ACCELERATION)
    set_value_float(measurement, "dev_is_operating", dev_is_operating)
    set_value_float(measurement, "vibration_total", current_total, SenmlUnits.SENML_UNIT_ACCELERATION)

    if do_store_measurement:
        storeMeasurement(measurement, True)


def read_accelerometer(measurements=None, single_measurement=False):
    logging.info("starting [read_accelerometer] thread")

    try:
        # add support for asm330
        from sensors import asm330

        # only at setup
        # sens.get_sensor_whoami()
        asm330.init(cfg.get("_UC_IO_I2C_SCL"), cfg.get("_UC_IO_I2C_SDA"))
    except Exception as e:
        logging.info("No sensors detected")
        return

    statsX = None
    statsY = None
    statsZ = None
    from math import fabs, pow, sqrt

    from . import running_stats

    statsX = running_stats.RunningStats()
    statsY = running_stats.RunningStats()
    statsZ = running_stats.RunningStats()

    if single_measurement:
        (asm330_accX, asm330_accY, asm330_accZ) = (None, None, None)

        while asm330_accX is None or asm330_accY is None or asm330_accZ is None:
            (asm330_accX, asm330_accY, asm330_accZ) = asm330.get_reading(False)
            sleep_ms(1)

        if asm330_accX is None or asm330_accY is None or asm330_accZ is None:
            return

        statsX.push(asm330_accX)
        statsY.push(asm330_accY)
        statsZ.push(asm330_accZ)
        current_total = sqrt(pow(statsX.mean(), 2) + pow(statsY.mean(), 2) + pow(statsZ.mean(), 2))
        storeAccellerometerMeasurement(measurements, statsX, statsY, statsZ, -1, current_total, False)
        return

    REPORT_PERIOD_MS = 10000
    FORCE_REPORT_PERIOD_MS = 300000

    now = ticks_ms()
    next_report = now + REPORT_PERIOD_MS
    next_force_report = now + FORCE_REPORT_PERIOD_MS

    previous_reported_total = []
    dev_is_operating = -1
    idle_value = 100000  # intentionally big value to drop exclude it in the iteration of min calculation
    (baseX, baseY, baseZ) = calculate_baseline(asm330)

    while 1:

        (asm330_accX, asm330_accY, asm330_accZ) = asm330.get_reading(True)
        if asm330_accX is None or asm330_accY is None or asm330_accZ is None:
            sleep_ms(1)
            continue

        statsX.push(fabs(asm330_accX - baseX))
        statsY.push(fabs(asm330_accY - baseY))
        statsZ.push(fabs(asm330_accZ - baseZ))

        now = ticks_ms()
        if now > next_force_report:
            logging.debug("======== Starting force report!")
            current_total = sqrt(pow(statsX.mean(), 2) + pow(statsY.mean(), 2) + pow(statsZ.mean(), 2))
            measurement = {}

            storeAccellerometerMeasurement(measurement, statsX, statsY, statsZ, dev_is_operating, current_total)

            next_force_report = now + FORCE_REPORT_PERIOD_MS

        if now > next_report:
            logging.debug("======== Starting normal report")
            current_total = sqrt(pow(statsX.mean(), 2) + pow(statsY.mean(), 2) + pow(statsZ.mean(), 2))
            measurement = {}

            if len(previous_reported_total) < 2:
                previous_reported_total.append(current_total)

                storeAccellerometerMeasurement(measurement, statsX, statsY, statsZ, dev_is_operating, current_total)

            elif previous_reported_total[0] != 0:
                previous_reported_total.reverse()
                two_values_ago = previous_reported_total.pop()
                total_diff = (current_total - two_values_ago) / min(two_values_ago, current_total)
                previous_reported_total.append(current_total)

                if fabs(total_diff) > 1:  # big vibration, so report it.
                    dev_is_operating_updated = 1 if total_diff > 0 else 0
                    if dev_is_operating == 1 and dev_is_operating_updated == 0:  # if dropping check if going to idle
                        drop_diff_from_idle = (current_total - idle_value) / min(idle_value, current_total)

                        # if current vibraation has diff over 100% from the min idle, consider it non idle
                        if drop_diff_from_idle > 1:
                            dev_is_operating_updated = 1  # do not consider that dev has dropped to idle.

                    dev_is_operating = dev_is_operating_updated

                    storeAccellerometerMeasurement(measurement, statsX, statsY, statsZ, dev_is_operating, current_total)
                else:
                    logging.debug("Ignoring low intensity vibration: diff: {}".format(total_diff))

            idle_value = min(idle_value, max(current_total, 5))  # set minimum vibration to value 5

            statsX.clear()
            statsY.clear()
            statsZ.clear()

            (baseX, baseY, baseZ) = calculate_baseline(asm330)

            next_report = now + REPORT_PERIOD_MS

        sleep_ms(1)


def executePostConnectionOperations():
    pass


def executeStartAccelerometerReading():
    import _thread

    _thread.start_new_thread(read_accelerometer, ())
