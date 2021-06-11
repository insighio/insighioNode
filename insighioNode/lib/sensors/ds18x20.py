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
from sensors.protocol.onewire import OneWire

class DS18X20(object):
    def __init__(self, onewire):
        self.ow = onewire
        self.roms = [rom for rom in self.ow.scan() if rom[0] == 0x10 or rom[0] == 0x28]
        self.fp = True
        try:
            1/1
        except TypeError:
            self.fp = False  # floatingpoint not supported

    def isbusy(self):
        """
        Checks wether one of the DS18x20 devices on the bus is busy
        performing a temperature convertion
        """
        return not self.ow.read_bit()

    def start_conversion(self, rom=None):
        """
        Start the temp conversion on one DS18x20 device.
        Pass the 8-byte bytes object with the ROM of the specific device you want to read.
        If only one DS18x20 device is attached to the bus you may omit the rom parameter.
        """
        if (rom==None) and (len(self.roms)>0):
            rom=self.roms[0]
        if rom!=None:
            rom = rom or self.roms[0]
            ow = self.ow
            ow.reset()
            ow.select_rom(rom)
            ow.write_byte(0x44)  # Convert Temp

    def read_temp_async(self, rom=None):
        """
        Read the temperature of one DS18x20 device if the convertion is complete,
        otherwise return None.
        """
        if self.isbusy():
            return None
        if (rom==None) and (len(self.roms)>0):
            rom=self.roms[0]
        if rom==None:
            return None
        else:
            ow = self.ow
            ow.reset()
            ow.select_rom(rom)
            ow.write_byte(0xbe)  # Read scratch
            data = ow.read_bytes(9)
            return self.convert_temp(rom[0], data)

    def convert_temp(self, rom0, data):
        """
        Convert the raw temperature data into degrees celsius and return as a fixed point with 2 decimal places.
        """
        temp_lsb = data[0]
        temp_msb = data[1]
        if rom0 == 0x10:
            if temp_msb != 0:
                # convert negative number
                temp_read = temp_lsb >> 1 | 0x80  # truncate bit 0 by shifting, fill high bit with 1.
                temp_read = -((~temp_read + 1) & 0xff) # now convert from two's complement
            else:
                temp_read = temp_lsb >> 1  # truncate bit 0 by shifting
            count_remain = data[6]
            count_per_c = data[7]
            if self.fp:
                return temp_read - 25 + (count_per_c - count_remain) / count_per_c
            else:
                return 100 * temp_read - 25 + (count_per_c - count_remain) // count_per_c
        elif rom0 == 0x28:
            temp = None
            if self.fp:
                temp = (temp_msb << 8 | temp_lsb) / 16
            else:
                temp = (temp_msb << 8 | temp_lsb) * 100 // 16
            if (temp_msb & 0xf8) == 0xf8: # for negative temperature
                temp -= 0x1000
            return temp
        else:
            assert False

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
