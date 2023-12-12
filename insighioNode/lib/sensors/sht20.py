import utime
import sensors
import logging
from machine import Pin, I2C


def get_reading(sda_pin, scl_pin, vcc_pin=None):
    """Returns temperature/humidity/serial reading, for given I2C SCL/SDA and VCC pins"""
    sensors.set_sensor_power_on(vcc_pin)

    # initialization & measurement
    i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin))

    hum = None
    temp = None

    try:
        i2c.writeto(0x40, b"\xf3")
        utime.sleep_ms(100)
        rx_bytes = i2c.readfrom(0x40, 2)
        if len(rx_bytes) == 2:
            temp = -46.86 + 175.72 * ((rx_bytes[0] << 8 | rx_bytes[1]) / 65535)
    except Exception as e:
        logging.exception(e, "Exception raised in I2C reading temperature")

    try:
        i2c.writeto(0x40, b"\xf5")
        utime.sleep_ms(40)
        rx_bytes = i2c.readfrom(0x40, 2)
        if len(rx_bytes) == 2:
            hum = -6 + 125 * ((rx_bytes[0] << 8 | rx_bytes[1]) / 65535)
    except Exception as e:
        logging.exception(e, "Exception raised in I2C reading humidity")

    # disable sensor and supply to sensor
    try:
        i2c.deinit()
    except Exception as e:
        pass

    sensors.set_sensor_power_off(vcc_pin)

    return (temp, hum)
