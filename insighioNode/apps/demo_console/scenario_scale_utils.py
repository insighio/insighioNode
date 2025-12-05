from utime import sleep_ms
import logging
import sensors

from . import cfg

from external.kpn_senml.senml_unit import SenmlUnits
from .dictionary_utils import set_value_float


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
