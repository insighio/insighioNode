import utime
import sensors
import logging
from machine import Pin, SoftI2C
import ubinascii
import gc
import ustruct

asm330_addr = 0x6A
_CTRL1_XL = 0x10  # Accelerometer control register
_CTRL2_G = 0x11  # Gyroscope control register
_OUTZ_H_A = 0x2D  # Linear acceleration sensor Z-axis output register HIGH
_OUTZ_L_A = 0x2C  # Linear acceleration sensor Z-axis output register LOW
_OUTY_H_A = 0x2B  # Linear acceleration sensor Y-axis output register HIGH
_OUTY_L_A = 0x2A  # Linear acceleration sensor Y-axis output register LOW
_OUTX_H_A = 0x29  # Linear acceleration sensor X-axis output register HIGH
_OUTX_L_A = 0x28  # Linear acceleration sensor X-axis output register LOW
_STANDARD_GRAVITY = 9.80665

_FACTOR = (2.0 / 32768) * _STANDARD_GRAVITY

i2c_obj = None


def get_sensor_whoami():
    """Returns reading"""
    if not i2c_obj:
        logging.debug("XL not initialized")
        return
    try:
        # WHO AM I -->  this should return 6B
        val = i2c_obj.readfrom_mem(asm330_addr, 0x0F, 1)
        logging.debug("Data {}, Output: {}".format(val, ubinascii.hexlify(val)))
    except Exception as e:
        logging.exception(e, "Exception raised in I2C {}")
    return None


def init(scl_pin, sda_pin):
    global i2c_obj
    i2c_obj = SoftI2C(scl=Pin(scl_pin), sda=Pin(sda_pin))
    _set_asm()


def _set_asm(odr_xl=0, fs_xl=0, lpf_xl_en=0):
    """Accelerometer ODR selection (CTRL1_XL)"""
    if not i2c_obj:
        logging.debug("XL not initialized")
        return

    if odr_xl > 10:
        logging.debug("Invalid XL ODR Setting (acceptable values: 0 .. 10)")
    else:
        try:
            i2c_obj.writeto_mem(asm330_addr, _CTRL1_XL, b"\x10")
        except Exception as e:
            logging.exception(e, "Exception raised in I2C {}")


def get_reading():
    """Returns acc reading"""
    if not i2c_obj:
        logging.debug("XL not initialized")
        return

    ACC_X = None
    ACC_Y = None
    ACC_Z = None
    try:
        # LINEAR ACCELERATION X,Y,Z
        data = i2c_obj.readfrom_mem(asm330_addr, _OUTX_L_A, 6)
        ACC_X = ustruct.unpack_from("<h", data, 0)[0] * _FACTOR
        ACC_Y = ustruct.unpack_from("<h", data, 2)[0] * _FACTOR
        ACC_Z = ustruct.unpack_from("<h", data, 4)[0] * _FACTOR
    except Exception as e:
        logging.exception(e, "Exception raised in I2C {}")
    return (ACC_X, ACC_Y, ACC_Z)
