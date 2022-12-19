import utime
import logging
import sensors
from external.hx711.hx711_spi import HX711
from machine import Pin, SPI

class ScaleSensor:
    def __init__(self, data_pin, clock_pin, spi_pin, offset=None, scale=None, vcc_pin=None):
        self.data_pin = data_pin
        self.clock_pin = clock_pin
        self.spi_pin = spi_pin
        self.offset = offset
        self.scale = scale
        self.vcc_pin = vcc_pin
        self.hx = None
        self.spi = None

    def init(self):
        try:
            sensors.set_sensor_power_on(self.vcc_pin)

            pin_OUT = Pin(self.data_pin, Pin.IN, pull=Pin.PULL_DOWN)
            pin_SCK = Pin(self.clock_pin, Pin.OUT)
            spi_sck = Pin(self.spi_pin)
            self.spi = SPI(1, baudrate=1000000, polarity=0,
                  phase=0, sck=spi_sck, mosi=pin_SCK, miso=pin_OUT)

            self.hx = HX711(pin_SCK, pin_OUT, self.spi)
        #    hx.tare()
            self.hx.set_gain(128)
            utime.sleep_ms(50)

            if self.offset is not None and self.scale:
                self.hx.set_offset(self.offset)
                self.hx.set_scale(self.scale)
            else:
                self.hx.set_offset(0.0)
                self.hx.set_scale(1)
            logging.debug("scale offset: {}, scale: {}".format(self.hx.OFFSET, self.hx.SCALE))
        except Exception as e:
            logging.exception(e, "failed to initialize scale")
            return False
        return True

    def deinit(self):
        if self.spi is not None:
            self.spi.deinit()
            self.spi = None
        sensors.set_sensor_power_off(self.vcc_pin)

    def set_offset(self, offset):
        if self.hx is None:
            logging.debug("get_reading_raw: self.hx is None")
            return False

        try:
            self.offset = offset
            self.hx.set_offset(offset)
            return True
        except Exception as e:
            logging.exception(e, "set_offset: exception setting offset: ")
            return False

    def get_offset(self):
        if self.hx is None:
            logging.debug("get_reading_raw: self.hx is None")
            return 0
        return self.hx.OFFSET

    def get_scale(self):
        if self.hx is None:
            logging.debug("get_reading_raw: self.hx is None")
            return 1
        return self.scale

    def get_reading_raw(self, times):
        if self.hx is None:
            logging.debug("get_reading_raw: self.hx is None")
            return 0

        try:
            return self.hx.read_average(times)
        except Exception as e:
            logging.exception(e, "get_reading_raw: exception reading average: ")
            return -1

    def convert_reading_to_weight(self, weight_raw):
        return (weight_raw - self.hx.OFFSET) / self.hx.SCALE

    def _get_reading_raw_idle_value(self):
        number_of_measurements_for_idle = 5
        weigth_diff_threshold_percent = 0.01

        sequential_identical_values = 0
        raw_before_event = 0
        last_raw = -1
        in_unstable_period = False

        raw_idle = -1

        while True:
            raw = self.get_reading_raw(10)

            if last_raw == 0:
                last_raw = -1

            value_diff = abs(raw - last_raw) / last_raw

            logging.debug("detecting idle raw weight: {}, diff percent from previous: {}".format(raw, value_diff))

            if value_diff > weigth_diff_threshold_percent:
                sequential_identical_values = 0
                if not in_unstable_period:
                    raw_before_event = last_raw
                    in_unstable_period = True
            # else ignore bouncing value
            else:
                sequential_identical_values += 1

            # execute if event detected
            if sequential_identical_values == number_of_measurements_for_idle:
                in_unstable_period = False
                raw_idle = raw
                break

            last_raw = raw
            utime.sleep_ms(10)

        return raw_idle


def  get_reading(data_pin, clock_pin, spi_pin, offset=None, scale=None, vcc_pin=None, get_raw=False):
    sensor = ScaleSensor(data_pin, clock_pin, spi_pin, offset, scale, vcc_pin)

    if not sensor.init():
        logging.error("Error initializing scale sensor")
        return -1
    raw = sensor.get_reading_raw(10)

    if get_raw:
        weight = raw
    else:
        weight = sensor.convert_reading_to_weight(raw)

    sensor.deinit()

    logging.debug("weight: {}".format(weight))

    return weight

def get_reading_raw_idle_value(data_pin, clock_pin, spi_pin, vcc_pin=None):
    sensor = ScaleSensor(data_pin, clock_pin, spi_pin, None, None, vcc_pin)

    if not sensor.init():
        logging.error("Error initializing scale sensor")
        return -1

    raw_idle = sensor._get_reading_raw_idle_value()

    sensor.deinit()

    return raw_idle
