from . import modem_base
import utime
import logging
from external.micropyGPS.micropyGPS import MicropyGPS
import ure


class ModemBG600(modem_base.Modem):
    def __init__(self, power_on, power_key, modem_tx, modem_rx, gps_tx=None, gps_rx=None):
        super().__init__(power_on, power_key, modem_tx, modem_rx, gps_tx, gps_rx)
        self.connection_status = False

    def set_technology(self, technology):
        if technology == 'NBIoT':
            self.send_at_cmd('AT+QCFG="nwscanmode",3,1')
        elif technology == 'GSM':
            self.send_at_cmd('AT+QCFG="nwscanmode",1,1')
        else:
            self.send_at_cmd('AT+QCFG="nwscanmode",0,1')

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

        (status1, _) = self.send_at_cmd('AT+QICSGP=1,1,"' + self.apn + '","","",0')
        (status2, _) = self.send_at_cmd('AT+QIACT=1')
        (status3, _) = self.send_at_cmd('AT+QMTCFG="pdpcid",1')

        return status1 and status2 and status3  # self.connected

    def is_connected(self):
        (status, lines) = self.send_at_cmd('AT+CGACT?')
        return status and len(lines) > 0 and "1,1" in lines[0]

    def disconnect(self):
        self.send_at_cmd("AT+QMTDISC=0")

        self.send_at_cmd("AT+QIDEACT=1")

        return super().disconnect()

    def get_extended_signal_quality(self):
        rsrp = None
        rsrq = None
        reg = '\\+QCSQ:\\s+"\\w+",(-?\\d+),(-?\\d+),(-?\\d+),(-?\\d+)'
        (status, lines) = self.send_at_cmd('AT+QCSQ')
        if status and len(lines) > 0:
            res = ure.match(reg, lines[0])
            if res:
                rsrp = res.group(2)
                rsrq = res.group(4)

        return (rsrp, rsrq)

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
        gps_fix = False
        logging.debug("Starting query gps")
        my_gps = MicropyGPS()

        start_timestamp = utime.ticks_ms()
        last_valid_gps_lat = None
        last_valid_gps_lon = None
        max_satellites = 0
        hdop = None
        timeout_timestamp = start_timestamp + timeoutms
        try:
            while utime.ticks_ms() < timeout_timestamp:
                (status, lines) = self.send_at_cmd('AT+QGPSGNMEA="GGA"')
                if status and len(lines) > 0:
                    if lines[0].startswith('+QGPSGNMEA:'):
                        lines[0] = lines[0].replace('+QGPSGNMEA: ', '')
                    for line in lines:
                        for char in line:
                            my_gps.update(char)
                        if my_gps.latitude and my_gps.latitude[0] and my_gps.latitude[1] and my_gps.longitude and my_gps.longitude[0] and my_gps.longitude[1]:
                            last_valid_gps_lat = my_gps.latitude
                            last_valid_gps_lon = my_gps.longitude
                            max_satellites = my_gps.satellites_in_use
                            hdop = my_gps.hdop

                        if my_gps.timestamp and my_gps.date:
                            self.gps_timestamp = my_gps.timestamp
                            self.gps_date = my_gps.date

                        logging.debug("{} Lat: {}, Lon: {}, NumSats: {} @ {} - {}".format(my_gps.timestamp, my_gps.latitude, my_gps.longitude, my_gps.satellites_in_use, my_gps.timestamp, my_gps.date))
                        if my_gps.satellites_in_use >= satelite_number_threshold:
                            gps_fix = True
                            logging.debug("satelite_number_threshold: ", str(satelite_number_threshold))
                            return (my_gps.timestamp, my_gps.latitude, my_gps.longitude, my_gps.satellites_in_use, my_gps.hdop)
                utime.sleep_ms(1000)
        except KeyboardInterrupt:
            pass

        return (None, last_valid_gps_lat, last_valid_gps_lon, max_satellites, hdop)
