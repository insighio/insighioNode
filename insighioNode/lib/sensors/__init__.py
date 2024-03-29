from utime import sleep_ms
import gpio_handler


def set_sensor_power_on(vcc_pin):
    if vcc_pin is not None:
        # enable supply to sensor
        gpio_handler.set_pin_value(vcc_pin, 1)
        sleep_ms(100)


def set_sensor_power_off(vcc_pin):
    if vcc_pin is not None:
        # disable supply to sensor
        gpio_handler.set_pin_value(vcc_pin, 0)
