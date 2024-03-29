from utime import sleep_ms
import device_info

from machine import ADC, Pin

(major_version, minor_version, _, _) = device_info.get_firmware_version()

import logging

_NUM_ADC_READINGS = 500


def get_input_voltage(pin, voltage_divider=1, attn=ADC.ATTN_11DB, measurement_cycles=_NUM_ADC_READINGS):
    """Returns input voltage in a specific pin, for a given voltage divider (default is 1) and attenuator level (default 3, i.e. 0-3.3V)"""
    adc = ADC(Pin(pin))
    adc.atten(attn)
    adc_width = ADC.WIDTH_13BIT if device_info.supports_13bit_adc() else ADC.WIDTH_12BIT
    adc.width(adc_width)

    try:
        if major_version == 1 and minor_version < 18:
            adc.init(attn, adc_width)
        elif major_version == 1 and minor_version >= 18:
            adc.init_mp(atten=attn)
        return adc.read_voltage(_NUM_ADC_READINGS) * voltage_divider
    except Exception as e:
        logging.exception(e, "unable to read: pin: {}".format(pin))
        pass

    logging.debug("fallback ADC without calibration")

    attn_factor = 1
    if attn == ADC.ATTN_11DB:
        attn_factor = 3.548134  # 10**(11/20)
    elif attn == ADC.ATTN_6DB:
        attn_factor = 1.995262  # 10**(6/20)
    elif attn == ADC.ATTN_2_5DB:
        attn_factor = 1.333521  # 10**(2.5/20)

    tmp = 0.0
    running_avg = 0.0
    for i in range(0, measurement_cycles):
        running_avg = (i / (i + 1)) * running_avg + float(adc.read_u16()) / (i + 1)

    return 1000 * running_avg / 65535 * attn_factor * voltage_divider

    # typical voltage_divider levels: 3.054 --> Exp Board 2.0, 2 --> Exp Board 3, 11 --> in-house implementation


def get_vin(pin="P16"):
    """A simple wrapper to take Vin for modules (relevant only when an expansion board is used)"""
    # just fix pin to 'P16' and voltage divider to 3.054 for Expansion Board 2 or 2 for Expansion Board 3
    return get_input_voltage(pin, 2)


def set_pin_value(pin, value):
    """Set pin permanently to value"""
    if pin is None or value is None:
        return
    try:
        tpin = Pin(pin, Pin.OUT)
        tpin.value(value)
        logging.debug("Pin {} value set to: {}".format(pin, value))
    except Exception as e:
        logging.exception(e, "unable to set Pin {} value set to: {}".format(pin, value))


# if voltage is undef 3 Volt and this can be used to terminate the process loop till
# the battery is adequately charged
def check_minimum_voltage_threshold(vthreshold=3000):
    import machine
    import uos

    voltage = None
    _is_esp32s3 = "esp32s3" in uos.uname().machine.lower()
    _UC_IO_BAT_MEAS_ON = 14 if _is_esp32s3 else 27
    _UC_IO_BAT_READ = 3 if _is_esp32s3 else 36

    set_pin_value(_UC_IO_BAT_MEAS_ON, 1)
    voltage = get_input_voltage(_UC_IO_BAT_READ, 2, machine.ADC.ATTN_11DB)
    set_pin_value(_UC_IO_BAT_MEAS_ON, 0)
    if voltage < vthreshold:
        machine.deepsleep(3600000)


def timed_pin_pull_up(pin, durationms=500):
    set_pin_value(pin, 0)
    set_pin_value(pin, 1)
    sleep_ms(durationms)
    set_pin_value(pin, 0)
