import utime
import sensors
import logging
from machine import Pin, SoftI2C
import ubinascii
import gc

asm330_addr = 0x6A
_CTRL1_XL = 0x10 # Accelerometer control register
_CTRL2_G  = 0x11 # Gyroscope control register
_OUTX_H_A = 0x29 # Linear acceleration sensor X-axis output register HIGH
_OUTX_L_A = 0x28 # Linear acceleration sensor X-axis output register LOW
_OUTY_H_A = 0x2B # Linear acceleration sensor Y-axis output register HIGH
_OUTY_L_A = 0x2A # Linear acceleration sensor Y-axis output register LOW
_OUTZ_H_A = 0x2D # Linear acceleration sensor Z-axis output register HIGH
_OUTZ_L_A = 0x2C # Linear acceleration sensor Z-axis output register LOW
_STANDARD_GRAVITY = 9.80665

i2c_obj=None


def _to_int(val, nbits):
    i = int(val, 16)
    if i >= 2 ** (nbits - 1):
        i -= 2 ** nbits
    return i

def get_sensor_whoami():
    """ Returns reading """
    #sensors.set_sensor_power_on(vcc_pin)
    if not i2c_obj:
        logging.debug("XL not initialized")
        return
    try:
        # WHO AM I -->  this should return 6B
        val = i2c_obj.readfrom_mem(asm330_addr, 0x0F, 1)
        logging.debug("Data {}, Output: {}".format(val, ubinascii.hexlify(val)))
    except Exception as e:
        logging.exception(e, "Exception raised in I2C {}")

    #sensors.set_sensor_power_off(vcc_pin)

    return None

def init(scl_pin, sda_pin):
    global i2c_obj
    i2c_obj=SoftI2C(scl=Pin(scl_pin),sda=Pin(sda_pin))
    _set_asm()

def _set_asm(odr_xl=0, fs_xl=0, lpf_xl_en=0):
    """ Accelerometer ODR selection (CTRL1_XL)"""
    if not i2c_obj:
        logging.debug("XL not initialized")
        return

    if odr_xl > 10:
        logging.debug("Invalid XL ODR Setting (acceptable values: 0 .. 10)")
    else:
        try:
            i2c_obj.writeto_mem(asm330_addr, _CTRL1_XL, b'\x10')
        except Exception as e:
            logging.exception(e, "Exception raised in I2C {}")

def get_acc_reading():
    """ Returns acc reading """
    if not i2c_obj:
        logging.debug("XL not initialized")
        return
    #sensors.set_sensor_power_on(vcc_pin)
    ACC_X = None
    ACC_Y = None
    ACC_Z = None
    try:
        #while(True):
        # LINEAR ACCELERATION X,Y,Z
        ACC_X = _to_int(ubinascii.hexlify(i2c_obj.readfrom_mem(asm330_addr, _OUTX_H_A, 1) + i2c_obj.readfrom_mem(asm330_addr, _OUTX_L_A, 1)), 16)*(2.0/32768)*_STANDARD_GRAVITY
        ACC_Y = _to_int(ubinascii.hexlify(i2c_obj.readfrom_mem(asm330_addr, _OUTY_H_A, 1) + i2c_obj.readfrom_mem(asm330_addr, _OUTY_L_A, 1)), 16)*(2.0/32768)*_STANDARD_GRAVITY
        ACC_Z = _to_int(ubinascii.hexlify(i2c_obj.readfrom_mem(asm330_addr, _OUTZ_H_A, 1) + i2c_obj.readfrom_mem(asm330_addr, _OUTZ_L_A, 1)), 16)*(2.0/32768)*_STANDARD_GRAVITY
        logging.debug("[ACC-X] {} | [ACC-Y] {} | [ACC-Z] {}".format(ACC_X,ACC_Y,ACC_Z))
        #utime.sleep_ms(1000)
    except Exception as e:
        logging.exception(e, "Exception raised in I2C {}")
    #sensors.set_sensor_power_off(vcc_pin)
    return (ACC_X, ACC_Y, ACC_Z)
