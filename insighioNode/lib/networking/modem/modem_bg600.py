from . import modem_base
import utime
import logging
import ure
import device_info
from external.micropyGPS.micropyGPS import MicropyGPS
import math

class ModemBG600(modem_base.Modem):
    def __init__(self, power_on, power_key, modem_tx, modem_rx):
        super().__init__(power_on, power_key, modem_tx, modem_rx)
        self.connection_status = False
        self.data_over_ppp = True
        self._last_prioritization_is_gnss = None

    # even though this function is correct for BG600, it is normally called
    # while waiting for the modem to power on, where at that time we are not aware
    # of the modem's model. So it can not be used as generic
    # Left for future referece
    def wait_for_modem_power_on(self):
        (status, _) = self.send_at_cmd("", 10000, "APP RDY")
        return status

    def init(self, ip_version, apn, technology):
        status = super().init(ip_version, apn, technology)
        return status

    def set_technology(self, technology):
        technology = technology.lower()
        if technology == 'nbiot':
            self.send_at_cmd('AT+QCFG="nwscanseq",0301,0')
            self.send_at_cmd('AT+QCFG="nwscanmode",3,0')
        elif technology == 'lte-m':
            self.send_at_cmd('AT+QCFG="nwscanseq",0201,0')
            self.send_at_cmd('AT+QCFG="nwscanmode",3,0')
        elif technology == 'gsm':
            self.send_at_cmd('AT+QCFG="nwscanseq",01,1')
            self.send_at_cmd('AT+QCFG="nwscanmode",1,1')
        else:
            self.send_at_cmd('AT+QCFG="nwscanseq",00,0')
            self.send_at_cmd('AT+QCFG="nwscanmode",0,0')
        self.send_at_cmd('AT+CFUN=1,1', 15000, "APP RDY")
        self.send_at_cmd('ATE0')
        utime.sleep_ms(1000)

    def prioritizeWWAN(self):
        if self._last_prioritization_is_gnss is None or self._last_prioritization_is_gnss == True:
            self.send_at_cmd('AT+QGPSCFG="priority",1,0')
            self._last_prioritization_is_gnss = False
            utime.sleep_ms(500)

    def prioritizeGNSS(self):
        if self._last_prioritization_is_gnss is None or self._last_prioritization_is_gnss == False:
            self.send_at_cmd('AT+QGPSCFG="priority",0,0')
            self._last_prioritization_is_gnss = True
            utime.sleep_ms(500)

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
            self.send_at_cmd('AT+QGPSCFG="gnssconfig",5')
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

    def get_gps_position(self, timeoutms=300000, satellite_number_threshold=5):
        gps_fix = False
        logging.info("Starting query gps. Timeout: {}, Min satellite num: {}".format(timeoutms, satellite_number_threshold))
        my_gps = MicropyGPS()

        self.prioritizeGNSS()

        start_timestamp = utime.ticks_ms()
        last_valid_gps_lat = None
        last_valid_gps_lon = None
        max_satellites = 0
        hdop = None
        hdop_thresh = 2
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
                            self.gps_timestamp = my_gps.date.copy()
                            self.gps_timestamp += [0]
                            self.gps_timestamp += my_gps.timestamp
                            self.gps_timestamp += [0]
                            # round seconds
                            self.gps_timestamp[6] = math.floor(self.gps_timestamp[6])

                        logging.debug("{} {} Lat: {}, Lon: {}, NumSats: {}, hdop: {}".format(my_gps.date, my_gps.timestamp, my_gps.latitude, my_gps.longitude, my_gps.satellites_in_use, my_gps.hdop))
                        if my_gps.satellites_in_use >= satellite_number_threshold or (my_gps.hdop > 0 and my_gps.hdop <= hdop_thresh):
                            gps_fix = True
                            return (self.gps_timestamp, my_gps.latitude, my_gps.longitude, my_gps.satellites_in_use, my_gps.hdop)
                utime.sleep_ms(1000)
        except KeyboardInterrupt:
            logging.debug("modem_bg600: gps explicitly interupted")

        return (None, last_valid_gps_lat, last_valid_gps_lon, max_satellites, hdop)

    def mqtt_connect(self, server_ip, server_port, username, password, keepalive=120):
        (context_activated, _) = self.send_at_cmd('AT+QMTCFG="pdpcid",1')
        if not context_activated:
            return False

        #setup keepalive
        self.send_at_cmd('AT+QMTCFG="keepalive",1,' + str(keepalive))

        max_retries = 3
        retry = 0
        while retry < max_retries:
            retry += 1
            (mqtt_ready, lines) = self.send_at_cmd('AT+QMTOPEN=1,"' + server_ip + '",' + str(server_port), 15000, r"\+QMTOPEN:\s+1,\d")
            if mqtt_ready:
                # if MQTT already connected
                if len(lines) > 0 and lines[-1].endswith ("0,2"):
                    return True
                break
            utime.sleep_ms(1000)

        if mqtt_ready:
            retry = 0
            while retry < max_retries:
                retry += 1
                (mqtt_connected, _) = self.send_at_cmd('AT+QMTCONN=1,"{}","{}","{}"'.format(username, username, password), 15000, "\\+QMTCONN:\\s+1,0,0")
                if mqtt_connected:
                    break
                utime.sleep_ms(1000)
            return mqtt_connected
        else:
            logging.error("Mqtt not ready")
        return False

    def mqtt_is_connected(self):
         (mqtt_ready, _) = self.send_at_cmd('AT+QMTOPEN?', 2000, r"\+QMTOPEN:\s+1.*")
         (mqtt_connected, _) = self.send_at_cmd('AT+QMTCONN?', 2000, r"\+QMTCONN:\s+1.*")
         return mqtt_ready and mqtt_connected

    def mqtt_publish(self, topic, message, num_of_retries=3, retain=False, qos=1):
        mqtt_send_ready = False
        mqtt_send_ok = False

        message_sent = False
        general_retry_num = 0
        import random
        logging.debug("mqtt_publish: qos: {}".format(qos))
        message_id = (int(random.random() * 65530) + 1) if qos else 0
        while not message_sent and general_retry_num < num_of_retries:
            for i in range(0, num_of_retries):
                (mqtt_send_ready, _) = self.send_at_cmd('AT+QMTPUB=1,{},{},{},"{}"'.format(message_id , 1 if qos else 0, 1 if retain else 0, topic), 15000, '>.*')
                if mqtt_send_ready:
                    break
                logging.error("Mqtt not ready to send")
                utime.sleep_ms(500)

            if mqtt_send_ready:
                for i in range(0, num_of_retries):
                    (mqtt_send_ok, lines) = self.send_at_cmd(message + '\x1a', 30000, r"\+QMTPUB:\s*\d+,\d+,[012]")

                    for line in lines:
                        if "1,{},0".format(message_id) in line or "1,{},1".format(message_id) in line:
                            message_sent = True

                    if mqtt_send_ok :
                        break
                    logging.error("Mqtt publish failed")
                    utime.sleep_ms(500)
            if message_sent:
                break

            general_retry_num += 1
        return mqtt_send_ready and mqtt_send_ok and message_sent

    def mqtt_get_message(self, topic, timeout_ms=5000):
        import random
        #channels/f1937d78-6745-4b6b-98c3-62e2201c21ab/messages/5de93307-344f-48f2-a66d-1d2f7e359504/#
        #reg = r"\+QMTRECV:\s*\d+,\d+,\"([a-z\-0-9\/]+)\",\"(.*)\"" -> can not be used as it causes: RuntimeError: maximum recursion depth exceeded
        reg = r"\+QMTRECV:.*"
        # subscribe and receive message if any
        message_id = int(random.random() * 65530) + 1
        (status_subscribed, lines) = self.send_at_cmd('AT+QMTSUB=1,{},"{}",1'.format(message_id, topic), timeout_ms, reg)
        # unsubscribe
        (status_unsubscribed, _) = self.send_at_cmd('AT+QMTUNS=1,{},"{}"'.format(message_id, topic), 30000, r"\+QMTUNS:.*")

        selected_line = None
        for line in lines:
            line = line.strip()
            # search for the line that contains the info of the received message
            if line.startswith("+QMTRECV:"):
                selected_line = line
                break

        if selected_line:
            return self.extract_topic_message_without_regex(selected_line)

        return None

    def extract_topic_message_without_regex(self, line):
        topic = ""
        message = ""
        topic_reached = False
        topic_parsed = False
        message_reached = False

        i = -1
        last_quote_index = len(line)
        message_quote_index = 0
        for c in list(line):
            i += 1
            if c == '"':
                if not topic_reached:
                    topic_reached = True
                    continue
                elif topic_reached and not topic_parsed:
                    topic_parsed = True
                    continue
                elif topic_parsed and not message_reached:
                    message_reached = True
                    message_quote_index = i
                    continue
                else:
                    last_quote_index = i

            if topic_reached and not topic_parsed:
                topic += c
            elif message_reached:
                message += c

        res = dict()
        res["topic"] = topic
        res["message"] = message[0:(last_quote_index - message_quote_index - 1)]
        return res

    def mqtt_disconnect(self):
        (statusMqttDisconnect, _) = self.send_at_cmd("AT+QMTDISC=1", 20000, r"\+QMTDISC:.*")
        (statusNetworkClose, _) = self.send_at_cmd("AT+QMTCLOSE=1", 20000, r"\+QMTCLOSE:.*")

        return statusMqttDisconnect and statusNetworkClose

    def get_next_bytes_from_file(self, file_handle, num_of_bytes, timeout_ms=2000):
        # clear incoming message buffer
        while self.uart.any():
            self.uart.readline()

        status = None
        buffer = None
        responseLines = []
        is_echo_on = True
        start_timestamp = utime.ticks_ms()
        timeout_timestamp = start_timestamp + timeout_ms
        success_regex = "^([\\w\\s\\+]+)?OK$"
        error_regex = "^((\\w+\\s+)?(ERROR|FAIL)$)|(\\+CM[ES] ERROR)"

        # send command
        command = "AT+QFREAD={},{}".format(file_handle, num_of_bytes)
        write_success = self.uart.write(command + '\r\n')
        if not write_success:
            return buffer

        while True:
            device_info.wdt_reset()

            remaining_bytes = self.uart.any()
            if(utime.ticks_ms() >= timeout_timestamp):
                if status is None:
                    status = False
                break

            # if OK or ERROR has already been read though there are still
            # data on the UART, keep reading
            if status is not None and remaining_bytes == 0:
                break

            line = self.uart.readline()

            try:
                line = line if line is None else line.decode('utf8').strip()
            except Exception as e:
                logging.error("! " + str(line))
                line = ""

            if line == command:
                is_echo_on = False
            elif line == "CONNECT " + str(num_of_bytes):
                data_read = 0
                buffer = self.uart.read(num_of_bytes)
            else:
                responseLines.append(line)
                if ure.search(success_regex, line) is not None:
                    status = True
                elif ure.search(error_regex, line) is not None:
                    status = False

            utime.sleep_ms(50)

        if status is None:
            status = False

        return buffer if status else None

    def get_file_size(self, source):
        # read file size
        (file_found, lines) = self.send_at_cmd('AT+QFLST="' + source + '"')
        reg = r'\+QFLST: ".*",(\d+)'
        res = ure.match(reg, lines[0])
        return int(res.group(1)) if res else None

    def open_file_read_only(self, source):
        # If the file exists, it is opened directly and is read only. If the file does not exist, an error is returned.
        (file_open_status, lines) = self.send_at_cmd('AT+QFOPEN="' + source + '",2')
        reg = r'\+QFOPEN:\s+(\d+)'
        res = ure.match(reg, lines[0])
        return res.group(1) if res else None

    def get_file(self, source, destination, timeoutms=150000):
        file_size = self.get_file_size(source)
        if not file_size:
            return False

        logging.debug("about to read file: {} of size: {} into: {}".format(source, file_size, destination))
        file_handle = self.open_file_read_only(source)
        logging.debug("File opened with handle: " + file_handle)

        data_read = 0
        CHUNKSIZE = 256

        fw = open(destination, 'wb')
        logging.debug("reading file contents")
        while data_read < file_size:
            data_remaining = file_size - data_read
            byte_length_to_request = CHUNKSIZE if data_remaining >= CHUNKSIZE else data_remaining
            logging.debug("  {}/{}: requesting: {}".format(data_read, file_size, byte_length_to_request))
            buffer = self.get_next_bytes_from_file(file_handle, byte_length_to_request)
            if not buffer:
                logging.error("error reading file from modem")
                fw.close()
                return False
            fw.write(buffer)
            data_read += byte_length_to_request
            utime.sleep_ms(10)
        fw.close()
        (file_close_status, _) = self.send_at_cmd('AT+QFCLOSE=' + file_handle)
        return data_read == file_size

    def delete_file(self, destination):
        (status, _) = self.send_at_cmd('AT+QFDEL="' + destination + '"')
        return status

    def http_get_file(self, url, destination_file, timeout_ms=250000):
        (context_ready, _) = self.send_at_cmd('AT+QHTTPCFG="contextid",1')
        self.send_at_cmd('AT+QHTTPCFG="requestheader",0')
        self.send_at_cmd('AT+QHTTPCFG="responseheader",0')
        (url_ready, _) = self.send_at_cmd('AT+QHTTPURL=' + str(len(url)) + ',80', 8000, "CONNECT")
        if not url_ready:
            return False

        (url_setup, _) = self.send_at_cmd(url, 80)
        if not url_setup:
            return False

        (get_requested, _) = self.send_at_cmd('AT+QHTTPGET=80', 80000, r"\+QHTTPGET:.*")

        if not get_requested:
            return False

        (file_downloaded, _) = self.send_at_cmd('AT+QHTTPREADFILE="' + destination_file + '"', timeout_ms, r"\+QHTTPREADFILE:.*")

        return file_downloaded

    # url_base = "console.insigh.io"
    # url_request_route = /mf-rproxy/channels/list
    def http_get_with_auth_header(self, url_base, url_request_route, auth_token, destination_file, timeout_ms=60000):
        (context_ready, _) = self.send_at_cmd('AT+QHTTPCFG="contextid",1')
        # enable executing http request with custom headers
        self.send_at_cmd('AT+QHTTPCFG="requestheader",1')
        self.send_at_cmd('AT+QHTTPCFG="responseheader",0')
        url = 'https://' + url_base  #"http://console.insigh.io/mf-rproxy/channels/list"
        requestHeader = (
            "GET " + url_request_route + " HTTP/1.1\r\n"
            "Host: " + url_base + "\r\n"
            "User-Agent: curl/7.74.0\r\n"
            "Accept: */*\r\n"
            "Content-Type: application/json\r\n"
            "Authorization: " + auth_token + "\r\n"
            "\r\n")

        (url_ready, _) = self.send_at_cmd('AT+QHTTPURL=' + str(len(url)) + ',80', 8000, "CONNECT")
        if not url_ready:
            return None

        (url_setup, _) = self.send_at_cmd(url, 80)
        if not url_setup:
            return None

        (url_req_ready, _) = self.send_at_cmd('AT+QHTTPGET=80,' + str(len(requestHeader)), 8000, "CONNECT")
        if not url_req_ready:
            return None

        (url_req_body_ready, _) = self.send_at_cmd(requestHeader, timeout_ms, r"\+QHTTPGET:.*")
        if not url_req_body_ready:
            return None

        response = None
        # (url_resp_received, lines) = self.send_at_cmd('AT+QHTTPREAD=120')
        # if url_resp_received and len(lines) > 1:
        #     response = lines[1]
        (file_downloaded, _) = self.send_at_cmd('AT+QHTTPREADFILE="' + destination_file + '"', timeout_ms, r"\+QHTTPREADFILE:.*")
        return file_downloaded
