from . import modem_base
import utime
import logging
from external.micropyGPS.micropyGPS import MicropyGPS
import ure

class ModemBG600(modem_base.Modem):
    def __init__(self, power_on, power_key, modem_tx, modem_rx, gps_tx=None, gps_rx=None):
        super().__init__(power_on, power_key, modem_tx, modem_rx, gps_tx, gps_rx)

    def init(self, ip_version, apn):
        if self.is_alive():
            # set auto-registration
            # self.send_at_cmd("AT+CFUN=0")
            # disable unsolicited report of network registration
            self.send_at_cmd("AT+CREG=0")
            self.send_at_cmd("AT+CFUN=1")

            self.send_at_cmd('AT+QCFG="nwscanmode",1,2')

            self.send_at_cmd('AT+CGDCONT=1,"IP","' + apn + '"')

        #     AT+CGDCONT=1,"PPP","iot.1nce.net"

            self.set_technology() # placeholder

            return True
        return False

    def connect(self, timeoutms=30000):
        for i in range(0, 5):
            (status, lines) = self.send_at_cmd('AT+CGACT=1,1')
            if status:
                break

        if not status:
            return False

        # (status, lines) = self.send_at_cmd('ATD*99***1#', 30000, "CONNECT(\\s*\\w+)?")
        # if not status:
        #     return False

        # from network import PPP
        #
        # logging.debug("PPP: instantiating...")
        # self.ppp = PPP(self.uart)
        # logging.debug("PPP: activating...")
        # self.ppp.active(True)
        # logging.debug("PPP: connecting...")
        # self.ppp.connect()
        #
        # start_timestamp = utime.ticks_ms()
        # timeout_timestamp = start_timestamp + timeoutms
        # while utime.ticks_ms() < timeout_timestamp:
        #     self.connected = self.is_connected()
        #     if self.connected:
        #         break
        #     utime.sleep_ms(100)
        #
        # logging.debug("PPP successsful: " + str(self.connected))

        self.connected = True

        return self.connected

    def is_connected(self):
        return self.connected

    def set_gps_state(self, poweron=True):
        if poweron:
            self.send_at_cmd('AT+QGPS=1')
        else:
            self.send_at_cmd('AT+QGPSEND')

    # to be overriden by children
    def is_gps_on(self):
        (status, lines) = self.send_at_cmd('AT+QGPS?')
        reg = "\\+QGPS:\\s+(\\d)"
        if status and len(lines):
            res = ure.match(reg, lines[0])
            return res is not None and res.group(1) == "1"
        return False

    def get_gps_position(self, timeoutms=300000, satelite_number_threshold=5):
        counter = 0
        gps_fix = False
        print("Starting query gps")
        my_gps = MicropyGPS()

        start_timestamp = utime.ticks_ms()
        last_valid_gps_lat = None
        last_valid_gps_lon = None
        max_satellites = 0
        hdop = None
        timeout_timestamp = start_timestamp + timeoutms
        while utime.ticks_ms() < timeout_timestamp:

            counter += 1
            (status, lines) = self.send_at_cmd('AT+QGPSGNMEA="GGA"')
            if status and len(lines) > 0:
                if lines[0].startswith('+QGPSGNMEA:'):
                    lines[0] = lines[0].replace('+QGPSGNMEA: ', '')
                for line in lines:
                    for char in line:
                        my_gps.update(char)
                    if my_gps.latitude and my_gps.latitude[0] and my_gps.latitude[1] and my_gps.longitude and my_gps.longitude[0] and my_gps.longitude[1]:
                        last_valid_gps_lat = my_gps.latitude
                        last_valid_gps_lon = my_gps.latitude
                        max_satellites = my_gps.satellites_in_use
                        hdop = my_gps.hdop

                    print("{} Lat: {}, Lon: {}, NumSats: {}".format(my_gps.timestamp, my_gps.latitude, my_gps.longitude, my_gps.satellites_in_use))
                    if my_gps.satellites_in_use >= satelite_number_threshold:
                        gps_fix = True
                        return (my_gps.timestamp, my_gps.latitude, my_gps.longitude, my_gps.satellites_in_use, my_gps.hdop)
            device_info.wdt_reset()
            utime.sleep_ms(1000)

        return (None, last_valid_gps_lat, last_valid_gps_lon, max_satellites, hdop)
