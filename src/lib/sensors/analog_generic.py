"""
Generic operation of an analog sensor.
    Reads and returns the voltage.
"""

import utime
import sensors
import gpio_handler
import logging


def get_reading(data_pin, vcc_pin=None):
    sensors.set_sensor_power_on(vcc_pin)

    # get measurement
    vmeas = gpio_handler.get_input_voltage(data_pin, 1)
    logging.debug(str(data_pin) + " voltage reading : {} (mV)".format(vmeas))
    # here we need to add some calibration processing

    sensors.set_sensor_power_off(vcc_pin)

    # return values
    return vmeas
