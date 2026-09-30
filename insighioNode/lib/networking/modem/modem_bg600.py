from . import modem_base
from utime import sleep_ms, ticks_ms, ticks_diff, ticks_add
import logging
import ure
from device_info import wdt_reset, get_device_id
from external.micropyGPS.micropyGPS import MicropyGPS
import math


class ModemBG600(modem_base.Modem):
    def __init__(self, power_on, power_key, modem_tx, modem_rx):
        super().__init__(power_on, power_key, modem_tx, modem_rx)
        self.connection_status = False
        self.data_over_ppp = True
        self._last_prioritization_is_gnss = None
        self._mqtt_client_id = 1
        self._ssl_pdp_context_id = 1
        self._ssl_context_id = 1
        self._ssl_client_id = 6
        self._ssl_socket_host = None
        self._ssl_socket_port = None
        self._ssl_context_configured = False

    # even though this function is correct for BG600, it is normally called
    # while waiting for the modem to power on, where at that time we are not aware
    # of the modem's model. So it can not be used as generic
    # Left for future referece
    def wait_for_modem_power_on(self, command=None):
        status, _ = self.send_at_cmd("", 10000, "APP RDY")
        return status

    def init(self, ip_version, apn, technology, mcc_mnc=None):
        status = super().init(ip_version, apn, technology, mcc_mnc)

        self.send_at_cmd('AT+QSSLCFG="session",1,1')
        return status

    def reset_to_factory(self):
        import utime

        self.send_at_cmd("AT+CFUN=0")
        utime.sleep_ms(5000)
        self.send_at_cmd('AT+QNVFD="/nv/item_files/modem/geran/grr/acq_db"')
        self.send_at_cmd('AT+QNVFD="/nv/reg_files/modem/lte/rrc/csp/acq_db"')
        self.send_at_cmd('AT+QNVFD="/nv/reg_files/modem/nb1/rrc/csp/acq_db"')
        self.send_at_cmd('AT+CRSM=214,28542,0,0,11,"FFFFFFFFFFFFFFFFFFFFFF"')
        self.send_at_cmd('AT+CRSM=214,28531,0,0,14,"FFFFFFFFFFFFFFFFFFFFFFFFFFFF"')
        self.send_at_cmd('AT+CRSM=214,28643,0,0,18,"FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"')
        self.send_at_cmd('AT+CRSM=214,28539,0,0,12,"FFFFFFFFFFFFFFFFFFFFFFFF"')
        self.send_at_cmd("AT&F")
        self.send_at_cmd("ATZ")
        self.send_at_cmd("AT+CFUN=1")
        utime.sleep_ms(5000)

    def set_technology(self, technology):
        technology = technology.lower()
        nwscanseq_expected = "030102"
        nwscanmode_expected = "0"
        iotmode = "2"
        if technology == "nbiot":
            nwscanseq_expected = "030102"
            nwscanmode_expected = "0"
            iotmode = "1"
        elif technology == "lte-m":
            nwscanseq_expected = "020301"
            nwscanmode_expected = "0"
            iotmode = "0"
        elif technology == "gsm":
            nwscanseq_expected = "010302"
            nwscanmode_expected = "0"
            iotmode = "2"

        try:
            logging.debug("Reading current configuration")
            nwscanseq_status, nwscanseq_lines = self.send_at_cmd('AT+QCFG="nwscanseq"')
            nwscanseq_match = self._match_regex(r'\s*\+QCFG:\s*"nwscanseq",(\w+)', nwscanseq_lines)

            nwscanmode_status, nwscanmode_lines = self.send_at_cmd('AT+QCFG="nwscanmode"')
            nwscanmode_match = self._match_regex(r'\s*\+QCFG:\s*"nwscanmode",(\w+)', nwscanmode_lines)

            iotopmode_status, iotopmode_lines = self.send_at_cmd('AT+QCFG="iotopmode"')
            iotopmode_match = self._match_regex(r'\s*\+QCFG:\s*"iotopmode",{}'.format(iotmode), iotopmode_lines)

            band_status, band_lines = self.send_at_cmd('AT+QCFG="band"')
            band_match = self._match_regex(r'\s*\+QCFG:\s*"band",0xf,0x80084,0x80084', band_lines)

            simeffect_status, simeffect_lines = self.send_at_cmd('AT+QCFG="simeffect"')
            simeffect_match = self._match_regex(r'\s*\+QCFG:\s*"simeffect",1', simeffect_lines)

            self.send_at_cmd('AT+QCFG="servicedomain",2,1')

            if (
                nwscanseq_match is None
                or nwscanseq_match.group(1) != nwscanseq_expected
                or nwscanmode_match is None
                or nwscanmode_match.group(1) != nwscanmode_expected
                or iotopmode_match is None
                or band_match is None
                or simeffect_match is None
            ):
                logging.debug("Writing configuration")
                self.send_at_cmd("AT+CFUN=0")
                self.send_at_cmd('AT+QCFG="nwscanseq",{}'.format(nwscanseq_expected))
                self.send_at_cmd('AT+QCFG="nwscanmode",{}'.format(nwscanmode_expected))
                self.send_at_cmd('AT+QCFG="iotopmode",{}'.format(iotmode))
                self.send_at_cmd('AT+QCFG="servicedomain",2,1')
                self.send_at_cmd('AT+QCFG="band",F,80084,80084')  # Europe setting -> network application note v3, page 32
                self.send_at_cmd('AT+QCFG="simeffect",1')
                self.send_at_cmd("AT+CFUN=1,1", 15000, "APP RDY")
                self.send_at_cmd("ATE0")
                sleep_ms(1000)

        except Exception as e:
            logging.excetion(e, "error changing device network scan settings")

    def get_sim_card_ids(self):
        self.sim_imsi, self.sim_iccid = super().get_sim_card_ids()

        status, lines = self.send_at_cmd("AT+QCCID")
        if status:
            match_res = self._match_regex(r"\+QCCID:\s+(\d+)", lines)
            if match_res is not None:
                self.sim_iccid = match_res.group(1)

        return (self.sim_imsi, self.sim_iccid)

    def wait_for_modem_power_off(self):
        self.send_at_cmd("", 5000, "(NORMAL\s*)?POWER(ED)?\s*DOWN")

    def prioritizeWWAN(self):
        if self._last_prioritization_is_gnss is None or self._last_prioritization_is_gnss == True:
            self.reset_uart()
            self.send_at_cmd('AT+QGPSCFG="priority",1,0')
            self._last_prioritization_is_gnss = False
            sleep_ms(100)

    def prioritizeGNSS(self):
        if self._last_prioritization_is_gnss is None or self._last_prioritization_is_gnss == False:
            self.reset_uart()
            self.send_at_cmd('AT+QGPSCFG="priority",0,0')
            self._last_prioritization_is_gnss = True
            sleep_ms(100)

    def connect(self, timeoutms=30000):
        for i in range(0, 5):
            status, lines = self.send_at_cmd("AT+CGACT=1,1")
            if status:
                break

        if not status:
            return False

        status1, _ = self.send_at_cmd('AT+QICSGP=1,1,"' + self.apn + '","","",0')
        status2, _ = self.send_at_cmd("AT+QIACT=1")

        return status1 and status2

    def force_time_update(self):
        self.send_at_cmd('AT+QNTP=1,"pool.ntp.org"', 125000, "\+QNTP")

    def is_connected(self):
        status, lines = self.send_at_cmd("AT+CGACT?")
        return status and len(lines) > 0 and "1,1" in lines[0]

    def power_off(self):
        if self._ssl_socket_host is not None:
            self.ssl_socket_close()
        res, lines = self.send_at_cmd("AT+QPOWD", 15000, r"\s*POWERED DOWN\s*")

        from machine import Pin

        p0 = Pin(self.modem_power_on, Pin.OUT)
        p0.off()
        return res

    def disconnect(self):
        if self._ssl_socket_host is not None:
            self.ssl_socket_close()
        res, lines = self.send_at_cmd("AT+QIDEACT=1")
        return res

    def update_ntp_date_time(self):
        status, lines = self.send_at_cmd('AT+QNTP=1,"pool.ntp.org"', 125000)

        reg = r"\+QNTP:\s*(\d+),.*"
        if status and len(lines) > 0:
            res = ure.match(reg, lines[0])
            if res and res.group(1) == "0":
                return True
        return False

    def get_extended_signal_quality(self):
        rsrp = None
        rsrq = None
        reg = '\\+QCSQ:\\s+"\\w+",(-?\\d+),(-?\\d+),(-?\\d+),(-?\\d+)'
        status, lines = self.send_at_cmd("AT+QCSQ")
        if status and len(lines) > 0:
            res = ure.match(reg, lines[0])
            if res:
                try:
                    rsrp = int(res.group(2))
                except:
                    rsrp = -141  # to be checked for nbiot
                try:
                    rsrq = int(res.group(4))
                except:
                    rsrq = -20  # to be checked for nbiot

        return (rsrp, rsrq)

    def set_gps_state(self, poweron=True):
        command = ""
        if poweron:
            command = "AT+QGPS=1"
            self.send_at_cmd('AT+QGPSCFG="gnssconfig",5')
        else:
            command = "AT+QGPSEND"

        status, _ = self.send_at_cmd(command)
        return status

    # to be overriden by children
    def is_gps_on(self):
        status, lines = self.send_at_cmd("AT+QGPS?")
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

        start_timestamp = ticks_ms()
        last_valid_gps_lat = None
        last_valid_gps_lon = None
        max_satellites = 0
        hdop = None
        hdop_thresh = 2
        timeout_timestamp = ticks_add(start_timestamp, timeoutms)
        try:
            while ticks_diff(ticks_ms(), timeout_timestamp) < 0:
                status, lines = self.send_at_cmd('AT+QGPSGNMEA="GGA"')
                if status and len(lines) > 0:
                    if lines[0].startswith("+QGPSGNMEA:"):
                        lines[0] = lines[0].replace("+QGPSGNMEA: ", "")
                    for line in lines:
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
                sleep_ms(1000)
        except KeyboardInterrupt:
            logging.debug("modem_bg600: gps explicitly interupted")

        return (None, last_valid_gps_lat, last_valid_gps_lon, max_satellites, hdop)

    def deactivate_context(self):
        self.send_at_cmd("AT+QIDEACT=1")

    def mqtt_connect(
        self, server_ip, server_port, username, password, keepalive=120, device_id=get_device_id()[0], explicit_client_id=None
    ):
        context_activated, _ = self.send_at_cmd('AT+QMTCFG="pdpcid",1')
        if not context_activated:
            return False

        # setup keepalive
        self.send_at_cmd('AT+QMTCFG="keepalive",1,' + str(keepalive))

        max_retries = 3
        retry = 0
        mqtt_ready = False

        temp_client_id = explicit_client_id if explicit_client_id else self._mqtt_client_id
        if not temp_client_id:
            self._mqtt_client_id = 1
            temp_client_id = self._mqtt_client_id

        while retry < max_retries and not mqtt_ready:
            retry += 1
            mqtt_result, lines = self.send_at_cmd(
                "AT+QMTOPEN=" + str(temp_client_id) + ',"' + server_ip + '",' + str(server_port),
                60000,
                r"\+QMTOPEN:\s*{},\d".format(str(temp_client_id)),
            )

            reg_match = self._match_regex(r"\+QMTOPEN:\s*" + str(temp_client_id) + ",(-?\d)", lines)
            if reg_match and reg_match.group(1) == "0":  # successfull connection
                mqtt_ready = True
                break
            elif reg_match and reg_match.group(1) == "2":  # already opened
                self.mqtt_disconnect()
                # temp_client_id += 1
                sleep_ms(1000)

            # +QIURC: "pdpdeact",1
            elif self._match_regex(r'\+QIURC:\s*"pdpdeact",1', lines):  # check for pdpdeact message
                self.deactivate_context()

            sleep_ms(500)

        if mqtt_ready:
            retry = 0
            while retry < max_retries:
                retry += 1
                mqtt_connected, _ = self.send_at_cmd(
                    'AT+QMTCONN={},"{}","{}","{}"'.format(temp_client_id, "{}_{}".format(device_id, temp_client_id), username, password),
                    15000,
                    r"\+QMTCONN:\s+{},0,0".format(temp_client_id),
                )
                if mqtt_connected:
                    break
                sleep_ms(500)
            return mqtt_connected
        else:
            logging.error("Mqtt not ready")
        return False

    def mqtt_is_connected(self, explicit_client_id=None):
        temp_client_id = explicit_client_id if explicit_client_id else self._mqtt_client_id
        if not temp_client_id:
            self._mqtt_client_id = 1
            temp_client_id = self._mqtt_client_id

        mqtt_ready, _ = self.send_at_cmd("AT+QMTOPEN?", 1000, r"\+QMTOPEN:\s+{}.*".format(temp_client_id))
        mqtt_connected, _ = self.send_at_cmd("AT+QMTCONN?", 1000, r"\+QMTCONN:\s+{},3".format(temp_client_id))
        return mqtt_ready and mqtt_connected

    def mqtt_publish(self, topic, message, num_of_retries=3, retain=False, qos=1, explicit_client_id=None):
        temp_client_id = explicit_client_id if explicit_client_id else self._mqtt_client_id
        if not temp_client_id:
            self._mqtt_client_id = 1
            temp_client_id = self._mqtt_client_id

        mqtt_send_ready = False
        mqtt_send_ok = False

        message_sent = False
        general_retry_num = 0
        import random

        logging.debug("mqtt_publish: qos: {}".format(qos))
        message_id = (int(random.random() * 65530) + 1) if qos else 0
        # deactivate our retries because BG600 has default retransmission mechanism
        # default: 3 retries with 5 seconds interval = 15 seconds total
        num_of_retries = 1
        while not message_sent and general_retry_num < num_of_retries:
            for i in range(0, num_of_retries):
                mqtt_send_ready, _ = self.send_at_cmd(
                    'AT+QMTPUB={},{},{},{},"{}"'.format(temp_client_id, message_id, 1 if qos else 0, 1 if retain else 0, topic),
                    15000,
                    ">.*",
                )
                if mqtt_send_ready:
                    break
                logging.error("Mqtt not ready to send")
                sleep_ms(500)

            if mqtt_send_ready:
                for i in range(0, 2):
                    mqtt_send_ok, lines = self.send_at_cmd(message + "\x1a", 15000, r"\+QMTPUB:\s*\d+,\d+,[012]")

                    for line in lines:
                        if "{},{},0".format(temp_client_id, message_id) in line or "{},{},1".format(temp_client_id, message_id) in line:
                            message_sent = True

                    if mqtt_send_ok:
                        break
                    logging.error("Mqtt publish failed")
                    sleep_ms(500)
            if message_sent:
                break

            general_retry_num += 1
        return mqtt_send_ready and mqtt_send_ok and message_sent

    def mqtt_get_message(self, topic, timeout_ms=5000, explicit_client_id=None):
        temp_client_id = explicit_client_id if explicit_client_id else self._mqtt_client_id
        if not temp_client_id:
            self._mqtt_client_id = 1
            temp_client_id = self._mqtt_client_id

        import random

        # channels/f1937d78-6745-4b6b-98c3-62e2201c21ab/messages/5de93307-344f-48f2-a66d-1d2f7e359504/#
        # reg = r"\+QMTRECV:\s*\d+,\d+,\"([a-z\-0-9\/]+)\",\"(.*)\"" -> can not be used as it causes: RuntimeError: maximum recursion depth exceeded
        reg = r"\+QMTRECV:.*"
        # subscribe and receive message if any
        message_id = int(random.random() * 65530) + 1
        status_subscribed, lines = self.send_at_cmd('AT+QMTSUB={},{},"{}",1'.format(temp_client_id, message_id, topic), timeout_ms, reg)
        # unsubscribe
        status_unsubscribed, _ = self.send_at_cmd('AT+QMTUNS={},{},"{}"'.format(temp_client_id, message_id, topic), 30000, r"\+QMTUNS:.*")

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
        res["message"] = message[0 : (last_quote_index - message_quote_index - 1)]
        return res

    def mqtt_disconnect(self, explicit_client_id=None):
        temp_client_id = explicit_client_id if explicit_client_id else self._mqtt_client_id
        if not temp_client_id:
            self._mqtt_client_id = 1
            temp_client_id = self._mqtt_client_id

        statusNetworkClose = False

        statusMqttDisconnect, _ = self.send_at_cmd(
            "AT+QMTDISC={}".format(temp_client_id), 20000, r"\++QMTDISC:\s*{},0".format(temp_client_id)
        )

        # if server does not report that the socket is closed, we close it for this side
        if not statusMqttDisconnect:
            statusNetworkClose, _ = self.send_at_cmd("AT+QMTCLOSE={}".format(temp_client_id), 30000, r"\+QMTCLOSE:.*")

        return statusMqttDisconnect or statusNetworkClose

    def get_next_bytes_from_file(self, file_handle, num_of_bytes, timeout_ms=2000):
        # clear incoming message buffer
        while self.uart.any():
            self.uart.readline()

        status = None
        buffer = None
        responseLines = []
        is_echo_on = True
        start_timestamp = ticks_ms()
        timeout_timestamp = ticks_add(start_timestamp, timeout_ms)
        success_regex = "^([\\w\\s\\+]+)?OK$"
        error_regex = "^((\\w+\\s+)?(ERROR|FAIL)$)|(\\+CM[ES] ERROR)"

        # send command
        command = "AT+QFREAD={},{}".format(file_handle, num_of_bytes)
        write_success = self.uart.write(command + "\r\n")
        if not write_success:
            return buffer

        while 1:
            wdt_reset()

            remaining_bytes = self.uart.any()
            if ticks_diff(ticks_ms(), timeout_timestamp) >= 0:
                if status is None:
                    status = False
                break

            # if OK or ERROR has already been read though there are still
            # data on the UART, keep reading
            if status is not None and remaining_bytes == 0:
                break

            line = self.uart.readline()

            try:
                line = line if line is None else line.decode("utf8").strip()
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

            sleep_ms(50)

        if status is None:
            status = False

        return buffer if status else None

    def get_file_size(self, source):
        # read file size
        file_found, lines = self.send_at_cmd('AT+QFLST="' + source + '"')
        reg = r'\+QFLST: ".*",(\d+)'
        res = ure.match(reg, lines[0])
        return int(res.group(1)) if res else None

    def open_file_read_only(self, source):
        # If the file exists, it is opened directly and is read only. If the file does not exist, an error is returned.
        file_open_status, lines = self.send_at_cmd('AT+QFOPEN="' + source + '",2')
        reg = r"\+QFOPEN:\s+(\d+)"
        res = ure.match(reg, lines[0])
        return res.group(1) if res else None

    def get_file(self, source, destination, timeoutms=250000):
        file_size = self.get_file_size(source)
        if not file_size:
            return False

        logging.debug("about to read file: {} of size: {} into: {}".format(source, file_size, destination))
        file_handle = self.open_file_read_only(source)
        logging.debug("File opened with handle: " + file_handle)

        data_read = 0
        CHUNKSIZE = 256
        # CHUNKSIZE = 384 good
        # CHUNKSIZE = 448
        # CHUNKSIZE = 470 no

        fw = open(destination, "wb")
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
            sleep_ms(10)
        fw.close()
        file_close_status, _ = self.send_at_cmd("AT+QFCLOSE=" + file_handle)
        return data_read == file_size

    def delete_file(self, destination):
        status, _ = self.send_at_cmd('AT+QFDEL="' + destination + '"')
        return status

    # --- persistent SSL socket -------------------------------------------------
    # A single SSL socket is kept open towards the console so that the TLS
    # handshake (~10s over NBIoT) is paid only once for all HTTP requests.

    def _ssl_configure_context(self):
        if self._ssl_context_configured:
            return

        ctx = self._ssl_context_id
        self.send_at_cmd('AT+QSSLCFG="sslversion",{},4'.format(ctx))  # all TLS versions
        self.send_at_cmd('AT+QSSLCFG="ciphersuite",{},0xFFFF'.format(ctx))  # support all cipher suites
        self.send_at_cmd('AT+QSSLCFG="seclevel",{},0'.format(ctx))  # no certificate authentication
        self.send_at_cmd('AT+QSSLCFG="sni",{},1'.format(ctx))
        self.send_at_cmd('AT+QSSLCFG="session",{},1'.format(ctx))  # allow session resumption
        self.send_at_cmd('AT+QSSLCFG="ignorelocaltime",{},1'.format(ctx))
        self.send_at_cmd('AT+QSSLCFG="negotiatetime",{},300'.format(ctx))
        self._ssl_context_configured = True

    def ssl_socket_is_connected(self):
        status, lines = self.send_at_cmd("AT+QSSLSTATE={}".format(self._ssl_client_id), 5000)
        if not status:
            return False
        # +QSSLSTATE: <clientID>,"SSLClient","<host>",<port>,<lport>,<socket_state>,...
        match = self._match_regex(r'\+QSSLSTATE:\s*{},"[^"]*","[^"]*",\d+,\d+,(\d+)'.format(self._ssl_client_id), lines)
        return match is not None and match.group(1) == "2"

    def ssl_socket_connect(self, host, port=443, timeout_ms=150000):
        if self._ssl_socket_host == host and self._ssl_socket_port == port and self.ssl_socket_is_connected():
            return True

        self.ssl_socket_close()
        self._ssl_configure_context()

        status, lines = self.send_at_cmd(
            'AT+QSSLOPEN={},{},{},"{}",{},0'.format(self._ssl_pdp_context_id, self._ssl_context_id, self._ssl_client_id, host, port),
            timeout_ms,
            r"\+QSSLOPEN:\s*{},\d+".format(self._ssl_client_id),
        )

        match = self._match_regex(r"\+QSSLOPEN:\s*{},(\d+)".format(self._ssl_client_id), lines)
        if not status or match is None or match.group(1) != "0":
            logging.error("SSL socket open to {}:{} failed: {}".format(host, port, lines))
            self.ssl_socket_close()
            return False

        self._ssl_socket_host = host
        self._ssl_socket_port = port
        logging.info("SSL socket open to {}:{}".format(host, port))
        return True

    def ssl_socket_close(self):
        self._ssl_socket_host = None
        self._ssl_socket_port = None
        status, _ = self.send_at_cmd("AT+QSSLCLOSE={},10".format(self._ssl_client_id), 15000)
        return status

    def _wait_for_uart_response(self, regex, timeout_ms):
        timeout_timestamp = ticks_add(ticks_ms(), timeout_ms)
        while ticks_diff(ticks_ms(), timeout_timestamp) < 0:
            wdt_reset()
            line = self.uart.readline()
            if line is None:
                sleep_ms(5)
                continue
            text = line.decode("utf8", "ignore").strip()
            if not text:
                continue
            logging.debug("  " + text)
            if ure.search(regex, text) is not None:
                return True
            if ure.search(r"(ERROR|FAIL)", text) is not None:
                return False
        return False

    def _ssl_send_raw(self, payload):
        if isinstance(payload, str):
            payload = payload.encode("utf8")

        ready, _ = self.send_at_cmd("AT+QSSLSEND={},{}".format(self._ssl_client_id, len(payload)), 10000, ">")
        if not ready:
            logging.error("SSL socket not ready to send")
            return False

        # raw write: the modem consumes exactly <len> bytes, no line terminator must follow
        self.uart.write(payload)
        return self._wait_for_uart_response(r"SEND OK", 30000)

    def _ssl_recv_raw(self, max_bytes=1500, timeout_ms=10000):
        """Reads up to max_bytes from the SSL socket buffer. Returns bytes (possibly empty) or None on error."""
        while self.uart.any():
            self.uart.read()

        command = "AT+QSSLRECV={},{}".format(self._ssl_client_id, max_bytes)
        logging.debug("> " + command)
        if not self.uart.write(command + "\r\n"):
            return None

        timeout_timestamp = ticks_add(ticks_ms(), timeout_ms)
        length = None
        while length is None and ticks_diff(ticks_ms(), timeout_timestamp) < 0:
            wdt_reset()
            line = self.uart.readline()
            if line is None:
                sleep_ms(5)
                continue
            text = line.decode("utf8", "ignore").strip()
            if not text:
                continue
            match = ure.search(r"\+QSSLRECV:\s*(\d+)", text)
            if match is not None:
                length = int(match.group(1))
            elif ure.search(r"(ERROR|FAIL)", text) is not None:
                logging.error("SSL socket read error: " + text)
                return None

        if length is None:
            return None

        data = b""
        while len(data) < length and ticks_diff(ticks_ms(), timeout_timestamp) < 0:
            wdt_reset()
            chunk = self.uart.read(length - len(data))
            if chunk:
                data += chunk
            else:
                sleep_ms(5)

        self._wait_for_uart_response(r"^OK", 5000)

        return data if len(data) == length else None

    def _ssl_dechunk(self, body):
        result = b""
        while True:
            index = body.find(b"\r\n")
            if index < 0:
                break
            try:
                size = int(body[:index].split(b";")[0].decode("utf8", "ignore"), 16)
            except Exception:
                break
            if size == 0:
                break
            result += body[index + 2 : index + 2 + size]
            body = body[index + 4 + size :]
        return result

    def _ssl_read_http_response(self, timeout_ms):
        """Returns (status_code, body_string) or (None, None) on failure."""
        raw = b""
        header_end = -1
        content_length = None
        chunked = False
        timeout_timestamp = ticks_add(ticks_ms(), timeout_ms)

        while ticks_diff(ticks_ms(), timeout_timestamp) < 0:
            chunk = self._ssl_recv_raw()
            if chunk is None:
                return (None, None)

            if not chunk:
                sleep_ms(200)
                continue

            raw += chunk

            if header_end < 0:
                header_end = raw.find(b"\r\n\r\n")
                if header_end < 0:
                    continue
                for line in raw[:header_end].decode("utf8", "ignore").split("\r\n"):
                    lowercase_line = line.lower()
                    if lowercase_line.startswith("content-length:"):
                        try:
                            content_length = int(line.split(":", 1)[1].strip())
                        except Exception:
                            content_length = None
                    elif lowercase_line.startswith("transfer-encoding:") and "chunked" in lowercase_line:
                        chunked = True

            body = raw[header_end + 4 :]
            if chunked:
                if not body.endswith(b"0\r\n\r\n"):
                    continue
                body = self._ssl_dechunk(body)
            elif content_length is not None:
                if len(body) < content_length:
                    continue
                body = body[:content_length]

            status_code = None
            status_match = ure.search(r"HTTP/1\.[01]\s+(\d+)", raw[:header_end].decode("utf8", "ignore"))
            if status_match:
                status_code = int(status_match.group(1))

            return (status_code, body.decode("utf8", "ignore"))

        logging.error("SSL socket: timed out waiting for HTTP response")
        return (None, None)

    def _ssl_http_request(self, method, url_base, url_request_route, auth_token, body=None, timeout_ms=60000):
        """Executes an HTTP request over the shared SSL socket. Returns (status_code, body_string)."""
        if body is None:
            body_str = ""
        elif isinstance(body, dict) or isinstance(body, list):
            import json

            body_str = json.dumps(body)
        else:
            body_str = str(body)

        request = (
            method + " " + url_request_route + " HTTP/1.1\r\n"
            "Host: " + url_base + "\r\n"
            "Authorization: " + auth_token + "\r\n"
            "Content-Type: application/json\r\n"
            "Connection: keep-alive\r\n"
            "Content-Length: " + str(len(body_str)) + "\r\n"
            "\r\n" + body_str
        )

        logging.debug("{} https://{}{} ({} body bytes)".format(method, url_base, url_request_route, len(body_str)))

        # the server may have dropped the idle socket, so allow one reconnect attempt
        for attempt in range(0, 2):
            if not self.ssl_socket_connect(url_base):
                return (None, None)

            if not self._ssl_send_raw(request):
                logging.error("SSL socket send failed, attempt {}".format(attempt + 1))
                self.ssl_socket_close()
                continue

            status_code, response_body = self._ssl_read_http_response(timeout_ms)
            if status_code is not None:
                logging.debug("response {}: {}".format(status_code, response_body))
                return (status_code, response_body)

            self.ssl_socket_close()

        return (None, None)

    def http_context_connect(self, timeoutms=30000):
        # for i in range(0, 5):
        #     (status, lines) = self.send_at_cmd("AT+CGACT=3,1")
        #     if status:
        #         break

        # if not status:
        #     return False

        status1, _ = self.send_at_cmd('AT+QICSGP=3,1,"' + self.apn + '"')
        status2, _ = self.send_at_cmd("AT+QIACT=3")

        return status1 and status2

    def http_context_is_connected(self):
        status, lines = self.send_at_cmd("AT+CGACT?")
        return status and len(lines) > 0 and "3,1" in lines[0]

    def http_context_disconnect(self):
        res, lines = self.send_at_cmd("AT+QIDEACT=3")
        return res

    def http_get_file(self, url, destination_file, timeout_ms=250000):
        file_downloaded = False
        file_size = -1

        context_ready, _ = self.send_at_cmd('AT+QHTTPCFG="contextid",1')  # 3')

        if not context_ready:
            return (file_downloaded, file_size)

        # http_context_connected = self.http_context_connect()
        # if not http_context_connected:
        #     logging.debug("http context not connected")
        #     return (file_downloaded, file_size)

        self.send_at_cmd('AT+QHTTPCFG="requestheader",0')
        self.send_at_cmd('AT+QHTTPCFG="responseheader",0')
        url_ready, _ = self.send_at_cmd("AT+QHTTPURL=" + str(len(url)) + ",80", 8000, "CONNECT")
        if not url_ready:
            self.http_context_disconnect()
            return (file_downloaded, file_size)

        url_setup, _ = self.send_at_cmd(url, 80)
        if not url_setup:
            self.http_context_disconnect()
            return (file_downloaded, file_size)

        get_requested, lines = self.send_at_cmd("AT+QHTTPGET=80", timeout_ms, r"\+QHTTPGET:.*")
        line_maches = self._match_regex(r"\+QHTTPGET:\s*(\d+),(\d+),(\d+)", lines)
        file_size = -1
        if line_maches:
            file_size = int(line_maches.group(3))

        if not get_requested or not line_maches or file_size < 0:
            self.http_context_disconnect()
            return (file_downloaded, file_size)

        file_downloaded, lines = self.send_at_cmd('AT+QHTTPREADFILE="' + destination_file + '"', timeout_ms, r"\+QHTTPREADFILE:\s*")

        # need to handle => read all lines and search for 0 code.
        # [DEBUG:115569]   +QMTSTAT: 1,1
        # [DEBUG:115585]   +QHTTPREADFILE: Http socket close
        # [DEBUG:115597]   +QIURC: "pdpdeact",1
        # self.http_context_disconnect()

        return (file_downloaded, file_size)

    # url_base = "console.insigh.io"
    # url_request_route = /mf-rproxy/channels/list
    def http_get_with_auth_header(self, url_base, url_request_route, auth_token, timeout_ms=60000):
        """Performs an authenticated GET over the shared SSL socket and returns the response body, or None on failure."""
        status_code, body = self._ssl_http_request("GET", url_base, url_request_route, auth_token, None, timeout_ms)
        if status_code is None or status_code >= 300:
            return None
        return body

    def _http_aux_with_body_and_auth_header(self, method, url_base, url_request_route, auth_token, post_body, timeout_ms=60000):
        status_code, _ = self._ssl_http_request(method, url_base, url_request_route, auth_token, post_body, timeout_ms)
        return status_code is not None and status_code < 300

    def http_post_with_auth_header(self, url_base, url_request_route, auth_token, post_body, timeout_ms=60000):
        return self._http_aux_with_body_and_auth_header("POST", url_base, url_request_route, auth_token, post_body, timeout_ms=timeout_ms)

    def http_put_with_auth_header(self, url_base, url_request_route, auth_token, post_body, timeout_ms=60000):
        return self._http_aux_with_body_and_auth_header("PUT", url_base, url_request_route, auth_token, post_body, timeout_ms=timeout_ms)

    def coap_connect(self, server_ip, server_port):
        context_activated, _ = self.send_at_cmd('AT+QCOAPCFG="pdpcid",2,1')
        if not context_activated:
            return False

        # Configure retransmission settings for CoAP client 0. (The ACK
        # timeout is 4 seconds and the maximum retransmission count is 5.)
        self.send_at_cmd('AT+QCOAPCFG="trans",2,4,5')

        max_retries = 3
        retry = 0
        while retry < max_retries:
            retry += 1
            coap_is_opening, lines = self.send_at_cmd(
                'AT+QCOAPOPEN=2,"' + server_ip + '",' + str(server_port), 15000, r"\+QCOAPOPEN:\s+2.*"
            )
            if coap_is_opening:
                break
            sleep_ms(1000)

        while retry < max_retries:
            retry += 1
            coap_opened = self.coap_is_connected()
            if coap_opened:
                return True
            sleep_ms(1000)

        return False

    def coap_is_connected(self):
        coap_ready, lines = self.send_at_cmd("AT+QCOAPOPEN?")

        if not coap_ready:
            return False

        regex = r"\+QCOAPOPEN:\s+2.*,3"
        for line in lines:
            match_res = ure.search(regex, line)
            if match_res is not None:
                return True

        return False

    def coap_setup_options(self, host, data_uri, token):
        # self.send_at_cmd('AT+QCOAPOPTION=2,1,0')
        # self.send_at_cmd('AT+QCOAPOPTION=2,1,1')
        # self.send_at_cmd('AT+QCOAPOPTION=2,1,2')
        # self.send_at_cmd('AT+QCOAPOPTION=2,1,3')

        # self.send_at_cmd('AT+QCOAPOPTION=2,0,0,3,"{}"'.format(host)) # set Uri-Host
        self.send_at_cmd('AT+QCOAPOPTION=2,0,0,11,"{}"'.format(data_uri))  # set Uri-Host
        self.send_at_cmd("AT+QCOAPOPTION=2,0,1,12,50")  # set JSON
        self.send_at_cmd('AT+QCOAPOPTION=2,0,2,15,"authorization={}"'.format(token))  # set authorization token

    def coap_publish(self, uri, payload, num_of_retries=3, confirmable=False):
        coap_send_ready = False
        coap_send_ok = False

        message_sent = False
        general_retry_num = 0
        import random

        confirmable_id = "0" if confirmable else "1"

        message_id = int(random.random() * 65530) + 1

        self.send_at_cmd('AT+QCOAPHEADER=2,{},0,6,"{}"'.format(message_id, get_device_id()[0]), 15000)

        send_success_regex = r"\+QCOAPACK:\s*2,\d+,\d+,0"

        while not message_sent and general_retry_num < num_of_retries:
            for i in range(0, num_of_retries):
                coap_send_ready, _ = self.send_at_cmd("AT+QCOAPSEND=2,{},2,7".format(confirmable_id), 15000, ">.*")
                if coap_send_ready:
                    break
                logging.error("CoAP not ready to send")
                sleep_ms(500)

            if coap_send_ready:
                for i in range(0, 2):
                    coap_send_ok, lines = self.send_at_cmd(payload + "\x1a", 15000, r"\+QCOAPACK:\s*\d+,\d+,\d+,\d+")

                    for line in lines:
                        if ure.search(send_success_regex, line) is not None:
                            message_sent = True
                            break

                    if coap_send_ok:
                        break
                    logging.error("CoAP publish failed")
                    sleep_ms(500)
            if message_sent:
                break

            general_retry_num += 1
        return coap_send_ready and coap_send_ok and message_sent

    def coap_disconnect(self):
        status, _ = self.send_at_cmd("AT+QCOAPCLOSE=2", 20000, r"\+QCOAPCLOSE:.*")
        return status
