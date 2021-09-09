"""
    Library and Wrapper for DS18X20 sensor.
    Extended Pycom's Example https://github.com/pycom/pycom-libraries/blob/master/examples/DS18X20/onewire.py
    by adding a simple wrapper function
    OneWire and DS18X20 classes are used as-is from the above github link
    For hardware connection: YELLOW/WHITE: DATA through GPIO, BLACK: GND, RED: VCC through GPIO. Use also a 4.7k PULL-UP for DATA
"""

import utime
import sensors
import machine
try:
    from onewire import OneWire
except:
    from sensors.protocol.onewire import OneWire

try:
    from ds18x20 import DS18X20
except:
    from sensor.ds18x20 import DS18X20

def get_reading(data_pin, vcc_pin=None):
    """ Returns temperature reading, for given VCC and DATA pins """
    sensors.set_sensor_power_on(vcc_pin)

    # initialize DS18X20
    ow = OneWire(machine.Pin(data_pin))
    tempObj = DS18X20(ow)
    # sensor reading
    tempObj.start_conversion()
    utime.sleep(1)
    temp = tempObj.read_temp_async()

    sensors.set_sensor_power_off(vcc_pin)

    # return reading
    return temp
