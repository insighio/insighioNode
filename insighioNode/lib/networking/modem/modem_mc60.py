from . import modem_base
import utime
import ure
import logging


class ModemMC60(modem_base.Modem):
    def __init__(self, power_on, power_key, modem_tx, modem_rx):
        super().__init__(power_on, power_key, modem_tx, modem_rx)

    def set_gps_state(self, poweron=True):
        self.send_at_cmd('AT+QGNSSC=' + ("1" if poweron else "0"))

    def get_extended_signal_quality(self):
        return (None, None)

    # to be overriden by children
    def is_gps_on(self):
        (status, lines) = self.send_at_cmd('AT+QGNSSC?')
        reg = "\\+QGNSSC:\\s+(\\d)"
        if status and len(lines):
            res = ure.match(reg, lines[0])
            return res is not None and res.group(1) == "1"
        return False

    def get_gps_position(self, timeoutms=300000, satellite_number_threshold=5):
        from external.micropyGPS.micropyGPS import MicropyGPS
        import math
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
            (status, lines) = self.send_at_cmd('AT+QGNSSRD="NMEA/GGA"')
            if status and len(lines) > 0:
                if lines[0].startswith('+QGNSSRD:'):
                    lines[0] = lines[0].replace('+QGNSSRD:', '')
                for line in lines:
                    for char in line:
                        my_gps.update(char)
                    if my_gps.latitude and my_gps.latitude[0] and my_gps.latitude[1] and my_gps.longitude and my_gps.longitude[0] and my_gps.longitude[1]:
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

                    logging.debug("{} {} Lat: {}, Lon: {}, NumSats: {}, hdop: {}".format(my_gps.date, my_gps.timestamp, my_gps.latitude, my_gps.longitude, my_gps.satellites_in_use, my_gps.hdop))
                    if my_gps.satellites_in_use >= satellite_number_threshold:
                        gps_fix = True
                        return (self.gps_timestamp, my_gps.latitude, my_gps.longitude, my_gps.satellites_in_use, my_gps.hdop)
            utime.sleep_ms(1000)

        return (None, last_valid_gps_lat, last_valid_gps_lon, max_satellites, hdop)
