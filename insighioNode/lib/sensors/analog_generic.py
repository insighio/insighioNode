"""
Generic operation of an analog sensor.
    Reads and returns the voltage.
"""

import utime
import sensors
import gpio_handler
import logging


def get_reading(data_pin, voltage_divider=1, vcc_pin=None):
    sensors.set_sensor_power_on(vcc_pin)

    # get measurement
    vmeas = None
    try:
        vmeas = gpio_handler.get_input_voltage(data_pin, voltage_divider)
        logging.debug("Pin: [{}] voltage reading : {} (mV)".format(str(data_pin), vmeas))
    except Exception as e:
        logging.exception(e, "Pin: [{}]".format(str(data_pin)))
    # here we need to add some calibration processing

    sensors.set_sensor_power_off(vcc_pin)

    # return values
    return vmeas
