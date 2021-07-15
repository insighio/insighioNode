import utime
import logging
import sensors


def get_reading(data_pin, clock_pin, spi_pin, offset=None, scale=None, vcc_pin=None):
    """ Returns temperature/humidity/serial reading, for given I2C SCL/SDA and VCC pins """
    from external.hx711.hx711_spi import HX711
    from machine import Pin, SPI

    sensors.set_sensor_power_on(vcc_pin)

    pin_OUT = Pin(data_pin, Pin.IN, pull=Pin.PULL_DOWN)
    pin_SCK = Pin(clock_pin, Pin.OUT)
    spi_sck = Pin(spi_pin)

    spi = SPI(1, baudrate=1000000, polarity=0,
          phase=0, sck=spi_sck, mosi=pin_SCK, miso=pin_OUT)

    hx = HX711(pin_SCK, pin_OUT, spi)
#    hx.tare()
    hx.set_gain(128)
    utime.sleep_ms(50)
    times = 15

    if offset is not None and scale is not None:
        hx.set_offset(offset)
        hx.set_scale(scale)
    else:
        hx.set_offset(0.0)
        hx.set_scale(1)
    logging.debug("scale offset: {}, scale: {}".format(hx.OFFSET, hx.SCALE))

    weight_raw = hx.read_average(times)
    logging.debug("weight raw: {}".format(weight_raw))
    weight = (weight_raw - hx.OFFSET) / hx.SCALE

    spi.deinit()
    sensors.set_sensor_power_off(vcc_pin)

    logging.debug("weight: {}".format(weight))

    return weight
