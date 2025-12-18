from . import modem_base
from utime import sleep_ms, ticks_ms, ticks_diff, ticks_add
import logging
from device_info import wdt_reset
from external.micropyGPS.micropyGPS import MicropyGPS
import math

from machine import SoftI2C, Pin
from gpio_handler import set_pin_value


class ModemGPSL76L(modem_base.Modem):
    def __init__(self, power_on, power_reset, i2c_scl, i2c_sda, gps_i2c_addr):
        super().__init__(power_on, power_reset, modem_tx=None, modem_rx=None)
        self.gps_i2c_addr = gps_i2c_addr
        self.i2c_obj = SoftI2C(Pin(i2c_scl), Pin(i2c_sda))

    def reset_uart(self):
        pass

    def has_data_over_ppp(self):
        pass

    def is_alive(self):
        # todo
        pass

    def print_status(self):
        pass

    def get_model(self):
        # todo?
        pass

    def power_on(self):
        logging.debug("Powering on GPS modem...")
        set_pin_value(self.modem_power_on, 1)
        sleep_ms(800)

    def wait_for_modem_power_on(self, command=None):
        modem_ok = False
        for i in range(0, 10):
            devs = self.i2c_obj.scan()
            modem_ok = self.gps_i2c_addr in devs
            logging.info("i2c devices: {}, GPS found: {}".format(devs, modem_ok))
            if modem_ok:
                break
            utime.sleep_ms(500)

        return modem_ok

    def power_off(self):
        logging.debug("Powering off GPS modem...")
        set_pin_value(self.modem_power_on, 0)
        sleep_ms(800)

    def wait_for_modem_power_off(self):
        pass

    def set_operator_selection(self, technology):
        pass

    def init(self, ip_version=None, apn=None, technology=None, mcc_mnc=None):
        self.i2c_obj.writeto_mem(self.gps_i2c_addr, 0, b"$PMTK353,1,0,1,0,0*2B")  # enable GPS and Galileo
        sleep_ms(10)
        self.i2c_obj.readfrom_mem(self.gps_i2c_addr, 0, 255)

    def set_technology(self, technology):
        pass

    def prioritizeWWAN(self):
        pass

    def prioritizeGNSS(self):
        pass

    def get_network_date_time(self):
        return (2000, 0, 0, 0, 0, 0, 0, 0)

    def wait_for_registration(self, timeoutms=30000):
        return True

    def attach(self, do_attach=True):
        return False

    def detach(self):
        return False

    def is_attached(self):
        return False

    def has_sim(self):
        return False

    def connect(self, timeoutms=30000):
        return False

    def is_connected(self):
        return False

    def disconnect(self):
        return False

    def force_time_update(self):
        pass

    def get_rssi(self):
        return -1

    def get_extended_signal_quality(self):
        return (-1, -1)

    def get_lac_n_cell_id(self):
        return (-1, -1)

    def get_registered_mcc_mnc(self):
        return (-1, -1)

    # to be overriden by children
    def set_gps_state(self, poweron=True):
        logging.debug("base modem.set_gps_state is empty")
        pass

    # to be overriden by children
    def is_gps_on(self):
        logging.debug("base modem.is_gps_on is empty")
        return False

    # to be overriden by children
    def get_gps_position(self, timeoutms=300000, satellite_number_threshold=4):
        gps_fix = False
        logging.info("Starting query gps. Timeout: {}, Min satellite num: {}".format(timeoutms, satellite_number_threshold))
        my_gps = MicropyGPS()

        self.prioritizeGNSS()

        start_timestamp = ticks_ms()
        last_valid_gps_lat = None
        last_valid_gps_lon = None
        max_satellites = 0
        hdop = None
        hdop_thresh = 2
        timeout_timestamp = ticks_add(start_timestamp, timeoutms)
        try:
            while ticks_diff(ticks_ms(), timeout_timestamp) < 0:
                self.i2c_obj.writeto_mem(self.gps_i2c_addr, 0, b"\x00")
                sleep_ms(10)
                lines = self.i2c_obj.readfrom_mem(self.gps_i2c_addr, 0, 255).decode().split("\n")
                for line in lines:
                    if not line.startswith("$GPGGA"):
                        continue

                    for char in line:
                        my_gps.update(char)
                    if (
                        my_gps.latitude
                        and my_gps.latitude[0]
                        and my_gps.latitude[1]
                        and my_gps.longitude
                        and my_gps.longitude[0]
                        and my_gps.longitude[1]
                    ):
                        last_valid_gps_lat = my_gps.latitude
                        last_valid_gps_lon = my_gps.longitude
                        max_satellites = my_gps.satellites_in_use
                        hdop = my_gps.hdop

                    if my_gps.timestamp and my_gps.date:
                        self.gps_timestamp = my_gps.date.copy()
                        self.gps_timestamp += [0]
                        self.gps_timestamp += my_gps.timestamp
                        self.gps_timestamp += [0]
                        # round seconds
                        self.gps_timestamp[6] = math.floor(self.gps_timestamp[6])

                    logging.debug(
                        "{} {} Lat: {}, Lon: {}, NumSats: {}, hdop: {}".format(
                            my_gps.date, my_gps.timestamp, my_gps.latitude, my_gps.longitude, my_gps.satellites_in_use, my_gps.hdop
                        )
                    )
                    if my_gps.satellites_in_use >= satellite_number_threshold or (my_gps.hdop > 0 and my_gps.hdop <= hdop_thresh):
                        gps_fix = True
                        return (self.gps_timestamp, my_gps.latitude, my_gps.longitude, my_gps.satellites_in_use, my_gps.hdop)

                wdt_reset()
                sleep_ms(500)
        except KeyboardInterrupt:
            logging.debug("modem_bg600: gps explicitly interupted")

        return (self.gps_timestamp, last_valid_gps_lat, last_valid_gps_lon, max_satellites, hdop)

    def send_at_cmd(self, command, timeoutms, success_condition):
        return (False, None)
