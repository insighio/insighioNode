""" Module for getting information from pycom's pins """

import utime
import machine
from machine import Pin

import logging

_NUM_ADC_READINGS = const(500)


def get_input_voltage(pin, voltage_divider=1, attn=machine.ADC.ATTN_11DB, measurement_cycles=_NUM_ADC_READINGS):
    """ Returns input voltage in a specific pin, for a given voltage divider (default is 1) and attenuator level (default 3, i.e. 0-3.3V) """
    adc = machine.ADC()

    adc.vref(1100)
    adc_pin = adc.channel(pin=pin, attn=attn)
    # now take the average over multiple readings
    tmp = 0.0
    for _ in range(0, measurement_cycles):
        tmp += adc_pin.voltage()
    # typical voltage_divider levels: 3.054 --> Exp Board 2.0, 2 --> Exp Board 3, 11 --> in-house implementation

    # should we use round function since the following division returns millivolt?
    return round((tmp / measurement_cycles) * voltage_divider)


def get_vin():
    """ A simple wrapper to take Vin for pycom modules (relevant only when an expansion board is used) """
    # just fix pin to 'P16' and voltage divider to 3.054 for Expansion Board 2 or 2 for Expansion Board 3
    return get_input_voltage('P16', 2)


def set_pin_value(pin, value):
    """ Set pin pernamently to value """
    tpin = Pin(pin, Pin.OUT)
    tpin.value(value)
    logging.debug('Pin {} value set to: {}'.format(pin, value))


# if voltage is undef 3 Volt and this can be used to terminate the process loop till
# the battery is adequately charged
def check_minimum_voltage_threshold():
    set_pin_value('P22', 1)
    voltage = get_input_voltage('P13', voltage_divider=11, attn=0)
    set_pin_value('P22', 0)
    if voltage < 3000:
        import machine
        machine.deepsleep(180000)


def timed_pin_pull_up(pin, durationms=500):
    set_pin_value(pin, 0)
    set_pin_value(pin, 1)
    utime.sleep_ms(durationms)
    set_pin_value(pin, 0)
