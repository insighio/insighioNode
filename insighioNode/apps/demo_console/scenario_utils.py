from utime import sleep_ms
import logging
import gpio_handler
import device_info

from . import cfg

from external.kpn_senml.senml_unit import SenmlUnits, SenmlSecondaryUnits
from .dictionary_utils import set_value, set_value_int, set_value_float
from . import message_buffer


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
    logging.debug("Pausing Measurements")
    shield_name = cfg.get("_SELECTED_SHIELD")
    if shield_name == cfg.get("_CONST_SHIELD_ENVIRO"):
        from . import scenario_enviro_utils

        scenario_enviro_utils.pause_background_measurements()


def resume_background_measurements(execution_period_ms=None):
    logging.debug("Resuming Measurements")
    shield_name = cfg.get("_SELECTED_SHIELD")
    if shield_name == cfg.get("_CONST_SHIELD_ENVIRO"):
        from . import scenario_enviro_utils

        scenario_enviro_utils.resume_background_measurements(execution_period_ms)


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
            set_value(measurements, "mem_alloc", mem_alloc, SenmlUnits.SENML_UNIT_BYTE)
            set_value(measurements, "mem_free", mem_free, SenmlUnits.SENML_UNIT_BYTE)

            try:
                from machine import SoftI2C, Pin

                # initialization & measurement
                i2c = SoftI2C(sda=Pin(cfg.get("_UC_IO_I2C_SDA")), scl=Pin(cfg.get("_UC_IO_I2C_SCL")))
                # get list of i2c devices returned from scan
                i2c_devices = i2c.scan()
                set_value(measurements, "i2c_devices", str(i2c_devices))
            except Exception as e:
                logging.exception(e, "Error getting i2c_devices.")
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
            from . import scenario_accel_utils

            scenario_accel_utils.shield_accel_measurements(measurements)
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
    from . import scenario_digital_adc_utils

    scenario_digital_adc_utils.get_measurements(measurements)


def add_explicit_key_values(measurements):
    try:
        for key in cfg.get("_MEAS_KEYVALUE"):
            set_value(measurements, key, cfg.get("_MEAS_KEYVALUE")[key])
    except:
        pass


def storeMeasurement(measurements, force_store=False, do_timestamp=True):
    if cfg.get("_BATCH_UPLOAD_MESSAGE_BUFFER") is None and not force_store:
        logging.error("Batch upload not activated, ignoring")
        return False

    if do_timestamp:
        message_buffer.timestamp_measurements(measurements)
    return message_buffer.store_measurement(measurements, force_store)


def executePostConnectionOperations():
    pass
