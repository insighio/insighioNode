"""
Current based SGX-7OX O2 sensor.
"""

import gpio_handler
from machine import ADC
import logging

_UC_IO_CUR_SNSR_OUT = 4
INA_GAIN = 20
SHUNT_OHMS = 100
_REF_CONC = 20.9
_REF_CONC_CURR_VAL_uA = 201

_MULTIPLIER_1 = SHUNT_OHMS * INA_GAIN
_MULTIPLIER_2 = 1000 / (_REF_CONC_CURR_VAL_uA / _REF_CONC)

def get_reading():
    current_mA = None
    o2_conc = None

    raw_mV = gpio_handler.get_input_voltage(_UC_IO_CUR_SNSR_OUT, voltage_divider=1, attn=ADC.ATTN_0DB, measurement_cycles=500)
    current_mA = raw_mV  / _MULTIPLIER_1
    o2_conc = current_mA * _MULTIPLIER_2

    # logging.info("ANLG SENSOR @ pin {}: {} mV, Current = {} mA, O2 Conc = {}".format(_UC_IO_CUR_SNSR_OUT, raw_mV, current_mA, o2_conc))
    return (current_mA, o2_conc)
