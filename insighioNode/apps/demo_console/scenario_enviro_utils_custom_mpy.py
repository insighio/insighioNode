from . import scenario_enviro_utils as _scenario_enviro_utils


def _read_pcnt_adc(adc_inst):
    return adc_inst.read_voltage(1)


_scenario_enviro_utils.configure_pcnt_adc_backend(
    read_adc=_read_pcnt_adc,
    high_mask=0x800,
    low_mask=0x400,
    voltage_max=3300,
    raw_to_millivolts_divisor=1,
)

from .scenario_enviro_utils import *
