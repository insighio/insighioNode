import utime
import logging
from machine import Pin, SoftI2C
import gc

scd4x_addr = 0x62
_MAX_USINGED_SHORT = 2**16 - 1
_TEMP_FACTOR = 175 / _MAX_USINGED_SHORT
_RH_FACTOR = 100 / _MAX_USINGED_SHORT

i2c_obj = None


def init(scl_pin, sda_pin):
    global i2c_obj
    i2c_obj = SoftI2C(scl=Pin(scl_pin), sda=Pin(sda_pin))
    _set_scd4x()


def _set_scd4x():
    if not i2c_obj:
        logging.debug("SCD4x not initialized")
        return
    # single shot meas example
    # i2c.writeto(scd4x_addr, b'\x21\x9d')
    # periodic measurement example
    # start meas (only once)
    try:
        i2c_obj.writeto(scd4x_addr, b"\x21\xb1")
    except Exception as e:
        logging.exception(e, "Exception raised in I2C {}")


def get_reading():
    """Returns acc reading"""
    if not i2c_obj:
        logging.debug("SCD4x not initialized")
        return

    co2 = None
    co2_temp = None
    co2_rh = None
    try:
        i2c_obj.writeto(scd4x_addr, b"\xec\x05")
        utime.sleep_ms(1)
        rx_bytes = i2c_obj.readfrom(scd4x_addr, 9)
        co2 = rx_bytes[0] << 8 | rx_bytes[1]
        temp = rx_bytes[3] << 8 | rx_bytes[4]
        humi = rx_bytes[6] << 8 | rx_bytes[7]
        co2_temp = temp * _TEMP_FACTOR - 45
        co2_rh = humi * _RH_FACTOR
    except Exception as e:
        logging.exception(e, "Exception raised in I2C {}")
    return (co2, co2_temp, co2_rh)
