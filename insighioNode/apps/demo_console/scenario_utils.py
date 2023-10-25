import utime
import logging
import gpio_handler
import device_info
import sensors
import gc

try:
    from apps import demo_temp_config as cfg
    logging.info("loaded config: [temp]")
except Exception as e:
    try:
        from . import demo_config as cfg
        logging.info("loaded config: [normal]")
    except Exception as e:
        cfg = type('', (), {})()
        logging.info("loaded config: [fallback]")

from external.kpn_senml.senml_unit import SenmlUnits
from external.kpn_senml.senml_unit import SenmlSecondaryUnits
from .dictionary_utils import set_value, set_value_int, set_value_float
import ubinascii
from . import message_buffer

from machine import Pin
import _thread

_pulse_pin = None
_pulse_counter = 0
_pulse_mutex = _thread.allocate_lock()
_pulse_last_read_timestamp = None

def get_config(key):
    return getattr(cfg, key) if hasattr(cfg, key) else None


def device_init():
    if device_info.get_hw_module_verison() != device_info._CONST_ESP32 and device_info.get_hw_module_verison() != device_info._CONST_ESP32_WROOM:
        device_info.bq_charger_exec(device_info.bq_charger_setup)
    else:
        if get_config("_UC_IO_LOAD_PWR_SAVE_OFF") is not None:
            gpio_handler.set_pin_value(cfg._UC_IO_LOAD_PWR_SAVE_OFF, 1)

        if get_config("_UC_IO_SENSOR_PWR_SAVE_OFF") is not None:
            gpio_handler.set_pin_value(cfg._UC_IO_SENSOR_PWR_SAVE_OFF, 1)

    if hasattr(cfg, "_NOTIFICATION_LED_ENABLED"):
        if hasattr(cfg, "_UC_IO_RGB_DIN") and hasattr(cfg, "_UC_RGB_VDD"):
            device_info.set_led_enabled(cfg._NOTIFICATION_LED_ENABLED, cfg._UC_RGB_VDD, cfg._UC_IO_RGB_DIN)
        else:
            device_info.set_led_enabled(cfg._NOTIFICATION_LED_ENABLED)
    else:
        device_info.set_led_enabled(False)

def read_shield_chip_id():
    from machine import Pin, SoftI2C
    import utime
    chip_id = None
    try:
        i2c=SoftI2C(scl=cfg._UC_IO_I2C_SCL, sda=Pin(cfg._UC_IO_I2C_SDA))
        # # WRITE`EXAMPLE: WRITE in MEMORY ADDRESS '02' the content 'AA'
        # i2c.writeto(eeprom_addr, b'\x02\xAA', True)
        #
        # # READ EXAMPLE : READ 3 BYTES STARTING AT MEMORY ADDRESS '00'
        # i2c.writeto(eeprom_addr, b'\x00', False)
        chip_id = i2c.readfrom(cfg._I2C_CHIP_ID_ADDRESS, 3)
    except Exception as e:
        pass
    return chip_id

def device_deinit():
    if get_config("_UC_IO_LOAD_PWR_SAVE_OFF") is not None:
        gpio_handler.set_pin_value(cfg._UC_IO_LOAD_PWR_SAVE_OFF, 0)

    if get_config("_UC_IO_SENSOR_PWR_SAVE_OFF") is not None:
        gpio_handler.set_pin_value(cfg._UC_IO_SENSOR_PWR_SAVE_OFF, 0)


def watchdog_reset():
    # first reset internal hardware watchdog
    device_info.wdt_reset()

    # then reset external hardware watchdog
    if hasattr(cfg, "_UC_IO_WATCHDOG_RESET"):
        gpio_handler.timed_pin_pull_up(cfg._UC_IO_WATCHDOG_RESET, 500)


# functions
def get_measurements(cfg_dummy=None):
    measurements = {}

    try:
        if  get_config("_MEAS_BATTERY_STAT_ENABLE"):
            vbatt = read_battery_voltage()
            set_value_int(measurements, "vbatt", vbatt, SenmlSecondaryUnits.SENML_SEC_UNIT_MILLIVOLT)

        if get_config("_MEAS_BOARD_STAT_ENABLE"):
            (mem_alloc, mem_free) = device_info.get_heap_memory()
            set_value(measurements, "reset_cause", device_info.get_reset_cause())
            set_value(measurements, "mem_alloc", mem_alloc, SenmlUnits.SENML_UNIT_BYTE)
            set_value(measurements, "mem_free", mem_free, SenmlUnits.SENML_UNIT_BYTE)
            try:
                if get_config("_MEAS_TEMP_UNIT_IS_CELSIUS"):
                    set_value_float(measurements, "cpu_temp", device_info.get_cpu_temp(), SenmlUnits.SENML_UNIT_DEGREES_CELSIUS)
                else:
                    set_value_float(measurements, "cpu_temp", device_info.get_cpu_temp(False), SenmlSecondaryUnits.SENML_SEC_UNIT_FAHRENHEIT)
            except:
                logging.error("Error getting cpu_temp.")
    except Exception as e:
        logging.exception(e, "unable to measure board sensors")

    #enable sensors
    new_gnd_pin = get_config("_UC_IO_SENSOR_GND_ON")
    old_gnd_pin = get_config("_UC_IO_SENSOR_SWITCH_ON")

    sensor_pin = new_gnd_pin if new_gnd_pin is not None else old_gnd_pin
    gpio_handler.set_pin_value(sensor_pin, 1)

    # read internal temperature and humidity
    try:
        if get_config("_MEAS_BOARD_SENSE_ENABLE"):
            if cfg._UC_INTERNAL_TEMP_HUM_SENSOR == cfg._CONST_SENSOR_SI7021:
                from sensors import si7021 as sens
            elif cfg._UC_INTERNAL_TEMP_HUM_SENSOR == cfg._CONST_SENSOR_SHT40:
                from sensors import sht40 as sens

            (board_temp, board_humidity) = sens.get_reading(cfg._UC_IO_I2C_SDA, cfg._UC_IO_I2C_SCL)
            set_value_float(measurements, "board_temp", board_temp, SenmlUnits.SENML_UNIT_DEGREES_CELSIUS)
            set_value_float(measurements, "board_humidity", board_humidity, SenmlUnits.SENML_UNIT_RELATIVE_HUMIDITY)

        shield_name = get_config("_SELECTED_SHIELD")
        if shield_name is not None and (shield_name == get_config("_CONST_SHIELD_ADVIND") or shield_name == get_config("_CONST_SELECTED_SHIELD_ESP_GEN_SHIELD_SDI12")):
            read_pulse_counter(measurements)
            from . import scenario_advind_utils
            scenario_advind_utils.shield_measurements(measurements)
        else: #if shield_name == get_config("_CONST_SHIELD_DIG_ANALOG"):
            default_board_measurements(measurements)

        if get_config("_MEAS_KEYVALUE"):
            add_explicit_key_values(measurements)

    except Exception as e:
        logging.exception(e, "unable to complete sensor measurements")

    #enable sensors
    gpio_handler.set_pin_value(sensor_pin, 0)

    return measurements


def read_battery_voltage():
    # BATT VOLTAGE
    current = None
    gpio_handler.set_pin_value(cfg._UC_IO_BAT_MEAS_ON, 1)

    device_info.bq_charger_exec(device_info.bq_charger_set_charging_off)

    utime.sleep_ms(50)

    vbatt = gpio_handler.get_input_voltage(cfg._UC_IO_BAT_READ, cfg._BAT_VDIV, cfg._BAT_ATT)

    device_info.bq_charger_exec(device_info.bq_charger_set_charging_on)
    gpio_handler.set_pin_value(cfg._UC_IO_BAT_MEAS_ON, 0)
    return vbatt


def default_board_measurements(measurements):
    # up to 2 I2C sensors
    meas_key_name = None

    for n in range(1, 3):
        meas_key_name = "_MEAS_I2C_" + str(n)
        i2c_config = get_config(meas_key_name)
        if i2c_config and hasattr(cfg, "_UC_IO_I2C_SDA") and hasattr(cfg, "_UC_IO_I2C_SCL") and i2c_config != cfg._CONST_MEAS_DISABLED:
            logging.debug("Getting measurement for [{}] from sensor [{}]".format(meas_key_name, i2c_config))
            read_i2c_sensor(cfg._UC_IO_I2C_SDA, cfg._UC_IO_I2C_SCL, i2c_config, measurements)

    # up to 3 Analog sensors
    for n in range(1, 4):
        meas_key_name = "_MEAS_ANALOG_P" + str(n)
        pin_name = "_UC_IO_ANALOG_DIGITAL_P" + str(n)
        meas_key = get_config(meas_key_name)
        pin = get_config(pin_name)

        if pin is None and n == 1:  #backward compatibility towards v1.2
            pin = 32

        if meas_key is not None and pin is not None and meas_key != cfg._CONST_MEAS_DISABLED:
            logging.debug("Getting measurement for [{}] from sensor [{}] @ pin [{}]".format(meas_key_name, meas_key, pin))
            read_analog_digital_sensor(pin, meas_key, measurements, "ap" + str(n))

    # up to 3 Digital/Analog sensors
    for n in range(1, 4):
        meas_key_name = "_MEAS_ANALOG_DIGITAL_P" + str(n)
        pin_name = "_UC_IO_ANALOG_DIGITAL_P" + str(n)
        transformation_key = "_MEAS_ANALOG_DIGITAL_P" + str(n) + "_TRANSFORMATION"
        meas_key = get_config(meas_key_name)
        pin = get_config(pin_name)

        if pin is None and n == 1:  #backward compatibility towards v1.2
            pin = 32

        transformation = get_config(transformation_key)
        if meas_key is not None and pin is not None and meas_key != cfg._CONST_MEAS_DISABLED:
            logging.debug("Getting measurement for [{}] from sensor [{}] @ pin [{}]".format(meas_key_name, meas_key, pin))
            read_analog_digital_sensor(pin, meas_key, measurements, "adp" + str(n), transformation)

    if hasattr(cfg, '_MEAS_SCALE_ENABLED') and cfg._MEAS_SCALE_ENABLED:
        read_scale(measurements)


def add_explicit_key_values(measurements):
    for key in cfg._MEAS_KEYVALUE:
        set_value(measurements, key, cfg._MEAS_KEYVALUE[key])

def _pulse_counter_callback(pin_instance):
    global _pulse_counter
    global _pulse_mutex
    with _pulse_mutex:
        _pulse_counter += 1
        #logging.debug("counter: #"+str(_pulse_counter))

def read_pulse_counter(measurements):
    global _pulse_counter
    global _pulse_mutex
    global _pulse_pin
    global _pulse_last_read_timestamp

    if get_config("_PCNT_1_ENABLE"):
        if _pulse_pin is None:
            _pulse_last_read_timestamp = utime.ticks_ms()
            _pulse_counter = 0
            gpio_handler.set_pin_value(get_config("UC_IO_SNSR_GND_DGTL_SNSR_ΟΝ"), 1)
            trigger_event = Pin.IRQ_RISING if get_config("_PCNT_1_COUNT_ON_RISING") else Pin.IRQ_FALLING
            _pulse_pin = Pin(get_config("UC_IO_DGTL_SNSR_READ"), Pin.IN, Pin.PULL_DOWN)
            _pulse_pin.irq(handler=_pulse_counter_callback, trigger=trigger_event)

        with _pulse_mutex:
            time_diff_from_prev = utime.ticks_ms() - _pulse_last_read_timestamp
            cnt = _pulse_counter
            _pulse_counter = 0
            _pulse_last_read_timestamp = utime.ticks_ms()
            #SENML_UNIT_LITER_PER_SECOND
        set_value_int(measurements, "pcnt_count", cnt)
        set_value_int(measurements, "pcnt_period_ms", time_diff_from_prev, SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND)

        if get_config("_PCNT_1_MULTIPLIER"):
            try:
                set_value_float(measurements, "pcnt_count_processed", cnt * float(get_config("_PCNT_1_MULTIPLIER")))
            except:
                pass
    else:
        if _pulse_pin is not None:
            _pulse_pin.irq(handler=None)
        gpio_handler.set_pin_value(get_config("UC_IO_SNSR_GND_DGTL_SNSR_ΟΝ"), 0)


def read_scale(measurements):
    weight_on_pin = get_config('_UC_IO_WEIGHT_ON')

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
    is_sensor_debug_on = get_config("_MEAS_SCALE_MONITORING_ENABLED")

    if is_sensor_debug_on:
        logging.setLevel(logging.DEBUG)

    while True:
        weight = hx711.get_reading(cfg._UC_IO_SCALE_DATA_PIN,
                                   cfg._UC_IO_SCALE_CLOCK_PIN,
                                   cfg._UC_IO_SCALE_SPI_PIN,
                                   cfg._UC_IO_SCALE_OFFSET if hasattr(cfg, '_UC_IO_SCALE_OFFSET') else None,
                                   cfg._UC_IO_SCALE_SCALE if hasattr(cfg, '_UC_IO_SCALE_SCALE') else None)
        if not is_sensor_debug_on:
            break

        logging.debug("Detected weight: {}".format(weight))
        utime.sleep_ms(10)

    if not wlan_is_active:
        wlan.active(False)

    weight = weight if weight > 0 or weight < -100 else 0
    set_value_float(measurements, "scale_weight", weight, SenmlUnits.SENML_UNIT_GRAM)

    if weight_on_pin:
        sensors.set_sensor_power_off(weight_on_pin)
    hx711.deinit_instance()

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
    elif sensor_name == "scd4x":
        from sensors import scd4x
        scd4x.init(cfg._UC_IO_I2C_SCL, cfg._UC_IO_I2C_SDA)
        (co2, temp, rh) = scd4x.get_reading()
        set_value_int(measurements, sensor_name + "_co2", co2, SenmlSecondaryUnits.SENML_SEC_UNIT_PARTS_PER_MILLION)
        set_value_float(measurements, sensor_name + "_temp", temp, SenmlUnits.SENML_UNIT_DEGREES_CELSIUS)
        set_value_float(measurements, sensor_name + "_humidity", rh, SenmlUnits.SENML_UNIT_RELATIVE_HUMIDITY)
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

def storeMeasurement(measurements, force_store=False):
    if get_config("_BATCH_UPLOAD_MESSAGE_BUFFER") is None and not force_store:
        logging.error("Batch upload not activated, ignoring")
        return False

    message_buffer.timestamp_measurements(measurements)
    return message_buffer.store_measurement(measurements, force_store)

def read_accelerometer():
    logging.info("starting XL thread")

    if get_config("_ALWAYS_ON_CONNECTION") or get_config("_FORCE_ALWAYS_ON_CONNECTION"):
        logging.debug("loading network modules...")
        # connect to network
        if cfg.network == "wifi":
            from . import wifi as network
        elif cfg.network == "cellular":
            from . import cellular as network
    else:
        network = None

    try:
        # add support for asm330
        from sensors import asm330
        # only at setup
        #sens.get_sensor_whoami()
        asm330.init(cfg._UC_IO_I2C_SCL, cfg._UC_IO_I2C_SDA)
    except Exception as e:
        logging.info("No sensors detected")
        return

    while True:
        gc.collect()

        (asm330_accX, asm330_accY, asm330_accZ) = asm330.get_acc_reading()
        if asm330_accX is None or asm330_accY is None or asm330_accZ is None:
            utime.sleep_ms(100)
            continue

        measurement = {}
        set_value_float(measurement, "asm330_accX", asm330_accX, SenmlUnits.SENML_UNIT_ACCELERATION)
        set_value_float(measurement, "asm330_accY", asm330_accY, SenmlUnits.SENML_UNIT_ACCELERATION)
        set_value_float(measurement, "asm330_accZ", asm330_accZ, SenmlUnits.SENML_UNIT_ACCELERATION)

        if network and network.is_connected():
            message = network.create_message(cfg.device_id, measurement)
            message_send_status = network.send_message(cfg, message)

        if not network or not network.is_connected() or not message_send_status:
            storeMeasurement(measurement, True)

        utime.sleep_ms(100)
