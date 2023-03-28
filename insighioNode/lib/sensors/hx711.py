import utime
import logging
import sensors
from external.hx711.hx711_spi import HX711
#from external.hx711.hx711_gpio import HX711
from machine import Pin

import device_info

sensor = None

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
        self.is_busy = False
        self.raw_data = [0 for _ in range(10)]

    def init(self):
        self.is_busy = True
        try:
            sensors.set_sensor_power_on(self.vcc_pin)

            pin_OUT = Pin(self.data_pin, Pin.IN, pull=Pin.PULL_DOWN)
            pin_SCK = Pin(self.clock_pin, Pin.OUT)
            spi_sck = Pin(self.spi_pin)
            if device_info.get_hw_module_verison() == device_info._CONST_ESP32S3:
                from machine import SoftSPI
                self.spi = SoftSPI(baudrate=1000000, polarity=0, phase=0, sck=spi_sck, mosi=pin_SCK, miso=pin_OUT)
            else:
                from machine import SPI
                self.spi = SPI(1, baudrate=1000000, polarity=0, phase=0, sck=spi_sck, mosi=pin_SCK, miso=pin_OUT)
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

            self.is_busy = False
            return False

        self.is_busy = False
        return True

    def deinit(self):
        self.is_busy = False
        if self.spi is not None:
            self.spi.deinit()
            self.spi = None

        self.hx = None
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

        if self.is_busy:
            logging.debug("HX711: ignoring call as there is an other request pending")
            return -1

        self.is_busy = True

        try:
            if len(self.raw_data) != times:
                self.raw_data = [0 for _ in range(times)]

            for _ in range(times):
                self.raw_data[_] = self.hx.read()
                #logging.debug("raw: {}".format(self.raw_data[_]))
            self.raw_data.sort()
            self.is_busy = False
            return self.raw_data[times // 2]
        except Exception as e:
            logging.exception(e, "get_reading_raw: exception reading average: ")
            self.is_busy = False
            return -1

    def convert_reading_to_weight(self, weight_raw):
        return round((weight_raw - self.hx.OFFSET) / self.hx.SCALE)

    def _get_reading_raw_idle_value(self):
        number_of_measurements_for_idle = 5
        weigth_diff_threshold_percent = 0.05

        sequential_identical_values = 0
        raw_before_event = 0
        last_raw = -1
        in_unstable_period = False

        raw_idle = -1

        start_time = utime.ticks_ms()
        timeout_ms = 15000 + start_time

        value_buffer = []

        while utime.ticks_ms()  < timeout_ms:
            raw = self.get_reading_raw(10)
            value_buffer.append(raw)

            if last_raw == 0:
                last_raw = -1

            value_diff = abs(raw - last_raw) / last_raw

            logging.debug("detecting idle raw: {}, diff percent from previous: {}".format(raw, value_diff))

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
            utime.sleep_ms(5)

        if raw_idle == -1 and len(value_buffer) > 0:
            logging.debug("fallback due to timeout")
            value_buffer.sort()
            return value_buffer[len(value_buffer) // 2]

        return raw_idle

def get_reading_raw_idle_value(data_pin=None, clock_pin=None, spi_pin=None, vcc_pin=None):
    global sensor

    if sensor is None and data_pin is not None and clock_pin is not None and spi_pin is not None:
        sensor = ScaleSensor(data_pin, clock_pin, spi_pin, None, None, vcc_pin)

        if not sensor.init():
            logging.error("Error initializing scale sensor")
            sensor = None
            return -1

    if sensor is not None:
        return sensor._get_reading_raw_idle_value()

    return -1

def  get_reading(data_pin, clock_pin, spi_pin, offset=None, scale=None, vcc_pin=None, get_raw=False):
    global sensor

    if sensor is None:
        sensor = ScaleSensor(data_pin, clock_pin, spi_pin, offset, scale, vcc_pin)

        if not sensor.init():
            logging.error("Error initializing scale sensor")
            sensor = None
            return -1

    raw = sensor.get_reading_raw(10)

    if get_raw:
        weight = raw
    else:
        weight = sensor.convert_reading_to_weight(raw)

    logging.debug("raw: {}, weight: {}".format(raw, weight))

    return weight

def set_offset(new_offset):
    if sensor is not None:
        sensor.set_offset(new_offset)

def deinit_instance():
    global sensor

    if sensor is not None:
        sensor.deinit()
        sensor = None
