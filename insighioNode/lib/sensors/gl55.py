"""
Wrapper for simple GL55 series photoresistor sensor.
    This is a simple analogue sensor, so the real purpose of this library is to provide support for calibration.
    Based on material from https://learn.adafruit.com/photocells
    For hardware connection: One end (either one): VCC through GPIO, Other end: DATA trough GPIO. Also add a 10k (or 1k if you need higher resolution for brightness) pull-down from DATA to GND.
"""

import sensors.analog_generic as analog


def get_reading(data_pin, vcc_pin=None):
    return analog.get_reading(data_pin, vcc_pin)
