import utime
import sensors
import logging
from machine import Pin, I2C


def get_reading(sda_pin, scl_pin, vcc_pin=None):
    """ Returns temperature/humidity/serial reading, for given I2C SCL/SDA and VCC pins """
    sensors.set_sensor_power_on(vcc_pin)

    # initialization & measurement
    i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin))

    # could be removed
    i2c_scan = i2c.scan()
    logging.debug("I2C: {}".format(i2c_scan))

    temp = None
    hum = None

    try:
        i2c.writeto(0x44, b'\xFD')
        utime.sleep_ms(20)
        rx_bytes = i2c.readfrom(0x44, 6)
        if len(rx_bytes) > 4:
            t_ticks = rx_bytes[0] << 8 | rx_bytes[1]
            rh_ticks = rx_bytes[3] << 8 | rx_bytes[4]
            t_degC = -45 + 175 * t_ticks / 65535
            rh_pRH = -6 + 125 * rh_ticks / 65535
            temp = t_degC
            hum = rh_pRH
    except Exception as e:
        logging.exception(e, "Exception raised in I2C {}")

    # disable sensor and supply to sensor
    try:
        i2c.deinit()
    except Exception as e:
        pass

    sensors.set_sensor_power_off(vcc_pin)

    return(temp, hum)
