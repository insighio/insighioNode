from . import modem_base
import utime
import logging
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

        return status1 and status2   # self.connected

    def is_connected(self):
        (status, lines) = self.send_at_cmd('AT+CGACT?')
        return status and len(lines) > 0 and "1,1" in lines[0]

    def disconnect(self):
        self.mqtt_disconnect()
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
        command = ""
        if poweron:
            command = 'AT+QGPS=1'
        else:
            command = 'AT+QGPSEND'

        (status, _) = self.send_at_cmd(command)
        return status

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
        from external.micropyGPS.micropyGPS import MicropyGPS
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

    def mqtt_connect(self, server_ip, server_port, username, password):
        (context_activated, _) = self.send_at_cmd('AT+QMTCFG="pdpcid",1')
        if not context_activated:
            return False

        (mqtt_ready, _) = self.send_at_cmd('AT+QMTOPEN=0,"' + server_ip + '",' + str(server_port), 15000, "\\+QMTOPEN:\\s+0,0")

        if mqtt_ready:
            # mqtt_conn, _) = modem_instance.send_at_cmd('AT+QMTCONN=0,"client","a93d2353-c664-4487-b52c-ae3bd73b06c4","ed1d8997-a8b1-46c1-8927-04fb35dd93af"')
            (mqtt_connected, _) = self.send_at_cmd('AT+QMTCONN=0,"{}","{}","{}"'.format(username, username, password), 15000, "\\+QMTCONN:\\s+0,0,0")
            return mqtt_connected
        else:
            logging.error("Mqtt not ready")
        return False

    def mqtt_publish(self, topic, message, num_of_retries=3):
        for i in range(0, 3):
            (mqtt_send_ready, _) = self.send_at_cmd('AT+QMTPUB=0,1,1,0,"' + topic + '"', 15000, '>')
            if mqtt_send_ready:
                (mqtt_send_ok, _) = self.send_at_cmd(message + '\x1a')
                return mqtt_send_ok
                logging.error("Mqtt not ready to send")
            utime.sleep_ms(500)
        return False

    def mqtt_disconnect(self):
        (status, _) = self.send_at_cmd("AT+QMTDISC=0")
        return status
