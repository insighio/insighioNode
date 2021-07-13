from . import modem_base
import utime
import ure
from external.micropyGPS.micropyGPS import MicropyGPS
import device_info


class ModemMC60(modem_base.Modem):
    def __init__(self, power_on, power_key, modem_tx, modem_rx, gps_tx=None, gps_rx=None):
        super().__init__(power_on, power_key, modem_tx, modem_rx, gps_tx, gps_rx)

    def set_gps_state(self, poweron=True):
        self.send_at_cmd('AT+QGNSSC=' + ("1" if poweron else "0"))

    # to be overriden by children
    def is_gps_on(self):
        (status, lines) = self.send_at_cmd('AT+QGNSSC?')
        reg = "\\+QGNSSC:\\s+(\\d)"
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
                    if my_gps.latitude and my_gps.latitude[0] and my_gps.latitude[1]:
                        last_valid_gps_lat = my_gps.latitude
                    if my_gps.longitude and my_gps.longitude[0] and my_gps.longitude[1]:
                        last_valid_gps_lon = my_gps.latitude
                    if my_gps.satellites_in_use > max_satellites:
                        max_satellites = my_gps.satellites_in_use

                    print("{} Lat: {}, Lon: {}, NumSats: {}".format(my_gps.timestamp, my_gps.latitude, my_gps.longitude, my_gps.satellites_in_use))
                    if my_gps.satellites_in_use >= satelite_number_threshold:
                        gps_fix = True
                        return (my_gps.timestamp, my_gps.latitude, my_gps.longitude, my_gps.satellites_in_use)
            device_info.wdt_reset()
            utime.sleep_ms(1000)

        return (None, last_valid_gps_lat, last_valid_gps_lon, max_satellites)
