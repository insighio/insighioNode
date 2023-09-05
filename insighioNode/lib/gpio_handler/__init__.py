""" Module for getting information from pycom's pins """

import utime
import device_info

from machine import ADC, Pin

import logging

_NUM_ADC_READINGS = const(500)

def get_input_voltage(pin, voltage_divider=1, attn=ADC.ATTN_11DB, measurement_cycles=_NUM_ADC_READINGS):
    """ Returns input voltage in a specific pin, for a given voltage divider (default is 1) and attenuator level (default 3, i.e. 0-3.3V) """
    if device_info.is_esp32():
        adc = ADC(Pin(pin))
        adc.atten(attn)
        adc_width = ADC.WIDTH_13BIT if device_info.supports_13bit_adc() else ADC.WIDTH_12BIT
        adc.width(adc_width)

        adc_initialized=False

        try:
            adc.init_mp(atten=ADC.ATTN_11DB)
            adc_initialized=True
        except Exception as e:
            logging.exception(e, "unable to init: pin: {}".format(pin))

        if not adc_initialized:
            try:
                adc.init(attn, adc_width)
                adc_initialized=True
            except Exception as e:
                logging.exception(e, "unable to init: pin: {}")

        if adc_initialized:
            try:
                return adc.read_voltage(_NUM_ADC_READINGS) * voltage_divider
            except Exception as e:
                logging.exception(e, "unable to read: pin: {}".format(pin))

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
    else:
        adc = ADC()

        adc.vref(1100)
        adc_pin = adc.channel(pin=pin, attn=attn)
        # now take the average over multiple readings
        tmp = 0.0
        for _ in range(0, measurement_cycles):
            tmp += adc_pin.voltage()

        return round((tmp / measurement_cycles) * voltage_divider)
    # typical voltage_divider levels: 3.054 --> Exp Board 2.0, 2 --> Exp Board 3, 11 --> in-house implementation


def get_vin(pin='P16'):
    """ A simple wrapper to take Vin for pycom modules (relevant only when an expansion board is used) """
    # just fix pin to 'P16' and voltage divider to 3.054 for Expansion Board 2 or 2 for Expansion Board 3
    return get_input_voltage(pin, 2)


def set_pin_value(pin, value):
    """ Set pin pernamently to value """
    try:
        tpin = Pin(pin, Pin.OUT)
        tpin.value(value)
        logging.debug('Pin {} value set to: {}'.format(pin, value))
    except Exception as e:
        logging.exception(e, "unable to set Pin {} value set to: {}".format(pin, value))


# if voltage is undef 3 Volt and this can be used to terminate the process loop till
# the battery is adequately charged
def check_minimum_voltage_threshold(pin_enable_battery_meas='P22', pin_battery_voltage='P13'):
    set_pin_value(pin_enable_battery_meas, 1)
    voltage = get_input_voltage(pin_battery_voltage, voltage_divider=2, attn=0)
    set_pin_value(pin_enable_battery_meas, 0)
    if voltage < 3000:
        import machine
        machine.deepsleep(180000)


def timed_pin_pull_up(pin, durationms=500):
    set_pin_value(pin, 0)
    set_pin_value(pin, 1)
    utime.sleep_ms(durationms)
    set_pin_value(pin, 0)
