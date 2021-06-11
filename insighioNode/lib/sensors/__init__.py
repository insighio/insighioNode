import utime
import gpio_handler


def set_sensor_power_on(vcc_pin):
    if vcc_pin is not None:
        # enable supply to sensor
        gpio_handler.set_pin_value(vcc_pin, 1)
        utime.sleep_ms(500)


def set_sensor_power_off(vcc_pin):
    if vcc_pin is not None:
        utime.sleep_ms(500)
        # disanable supply to sensor
        gpio_handler.set_pin_value(vcc_pin, 0)
