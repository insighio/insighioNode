from utime import ticks_ms, sleep_ms, ticks_diff, ticks_add
from machine import Pin, UART
import ure
import logging
from device_info import wdt_reset
import utils

# TODO: check if some regexes need to be precompiled: ure.compile('\d+mplam,pla')


class Modem:
    def __init__(self, power_on=None, power_key=None, modem_tx=None, modem_rx=None):
        self.connected = False
        self.ppp = None
        self.uart = None
        self.modem_power_on = None
        self.modem_power_key = None
        self.apn = None
        self.gps_timestamp = None
        self.gps_date = None
        self.data_over_ppp = True
        self.modem_tx = modem_tx
        self.modem_rx = modem_rx

        if modem_tx is not None and modem_rx is not None:
            self.reset_uart()

        self.modem_power_on = power_on
        self.modem_power_key = power_key

    def reset_uart(self):
        if self.uart is not None:
            self.uart.deinit()

        self.uart = UART(1, 115200, tx=self.modem_tx, rx=self.modem_rx)
        self.uart.init(115200, bits=8, parity=None, stop=1, tx=self.modem_tx, rx=self.modem_rx, timeout=500, timeout_char=100)

    def has_data_over_ppp(self):
        return self.data_over_ppp

    def is_alive(self):
        (status, response) = self.send_at_cmd("AT", 1000)
        return status

    def print_status(self):
        self.send_at_cmd("AT+CFUN?")
        self.send_at_cmd("AT+CMEE=2")
        self.send_at_cmd("AT+CPIN?")
        self.send_at_cmd("AT+QDSIM?")
        self.send_at_cmd("AT+QSIMVOL?")
        self.send_at_cmd("AT+QSIMDET?")

    def get_model(self):
        (status, lines) = self.send_at_cmd("ATI")
        if not status or len(lines) < 2:
            return None

        new_line = "\n"
        return new_line.join(lines).lower()

    def power_on(self):
        # network registration
        Pin(self.modem_power_on, Pin.OUT).on()
        # modem boot
        p0 = Pin(self.modem_power_key, Pin.OUT)
        logging.debug("Output Pin {} {}".format(self.modem_power_key, p0.value()))
        p0.on()
        sleep_ms(1200)
        p0.off()
        logging.debug("Output Pin {} {}".format(self.modem_power_key, p0.value()))
        logging.info("Waiting for the modem to finish power on")
        status = self.wait_for_modem_power_on()
        logging.info("Modem ready: " + str(status))

        if status:
            self.send_at_cmd("at+cmee=2")

    def wait_for_modem_power_on(self, command="AT"):
        retries = 0
        while retries < 10:
            (status, response) = self.send_at_cmd(command, 500)
            if status:
                return True
            retries += 1
        return False

    def power_off(self):
        p0 = Pin(self.modem_power_key, Pin.OUT)
        p0.on()
        logging.debug("Output Pin {} {}".format(self.modem_power_key, p0.value()))
        sleep_ms(800)
        p0.off()
        p0 = Pin(self.modem_power_on, Pin.OUT)
        p0.off()
        logging.debug("Output Pin {} {}".format(self.modem_power_on, p0.value()))

    def wait_for_modem_power_off(self):
        pass

    def set_operator_selection(self, technology):
        (status, lines) = self.send_at_cmd("AT+COPS?")
        lines = "\n".join(lines)

        expected_configuration = "0"  # operator automatic selection
        command = "AT+COPS=0"

        if technology.lower() == "nbiot":
            expected_configuration = "1"  # operator locking
            command = "AT+COPS=4,2,20201"

        operator_regex = r"\+COPS:\s*(\d).*"
        match = ure.search(operator_regex, lines)
        if match and match.group(1) == expected_configuration:
            logging.debug("Operator selection already configured")
            return

        self.send_at_cmd(command, 180000)

    def init(self, ip_version, apn, technology):
        if not self.is_alive():
            return False

        has_sim_check = False
        for i in range(0, 5):
            has_sim_check = self.has_sim()
            if has_sim_check:
                break
            else:
                sleep_ms(500)

        if not has_sim_check:
            return False

        self.apn = apn
        self.send_at_cmd("AT+CFUN=1")
        self.send_at_cmd('AT+CGDCONT=1,"' + ip_version + '","' + apn + '"')

        self.set_technology(technology)
        self.set_operator_selection(technology)

        # disable command echo
        self.send_at_cmd("ATE0")
        # set auto-registration
        self.send_at_cmd("AT+COPS=3,2")  # set network name as numeric value
        self.send_at_cmd("AT+CREG=2")  # enable LAC, CI reporting
        self.send_at_cmd("AT+CTZU=1")  # automatic time update

        return True

    def set_technology(self, technology):
        pass

    def prioritizeWWAN(self):
        pass

    def prioritizeGNSS(self):
        pass

    def get_network_date_time(self):
        start_timestamp = ticks_ms()
        timeout_timestamp = ticks_add(start_timestamp, 10000)
        regex = "(\\d+)\\/(\\d+)\\/(\\d+),(\\d+):\\s*(\\d+):(\\d+)([+-]\\d+)"
        while ticks_diff(ticks_ms(), timeout_timestamp) < 0:
            (status, lines) = self.send_at_cmd("AT+CCLK?")
            if status and len(lines) > 0:
                reg_res = ure.search(regex, lines[0])
                if reg_res:
                    logging.debug("Setting cellular RTC")
                    try:
                        year = int(reg_res.group(1))
                        if year < 100:
                            year += 2000

                        if year >= 2023:
                            timezone_quarter_minute_offset = float(reg_res.group(7))
                            # keep timezone info for timestamping in UTC and set time in local time zone
                            # for proper timing when executing specific time in day
                            result = (
                                year,
                                int(reg_res.group(2)),
                                int(reg_res.group(3)),
                                0,  # day of week
                                int(reg_res.group(4)),
                                int(reg_res.group(5)),
                                int(reg_res.group(6)),
                                0,
                            )  # usec
                            utils.saveKeyValueInteger("tz_sec_offset", int(timezone_quarter_minute_offset * 15 * 60))
                            return result
                    except Exception as e:
                        logging.exception(e, "Error reading network time: ", e)
                        pass
                logging.debug("Network time not ready yet")
            sleep_ms(250)
        return (2000, 0, 0, 0, 0, 0, 0, 0)

    def wait_for_registration(self, timeoutms=30000):
        status = False

        start_timestamp = ticks_ms()
        timeout_timestamp = ticks_add(start_timestamp, timeoutms)
        regex_creg = "\\+CREG:\\s+\\d,(\\d)"
        _STATE_CHECK_CREG_INITIALIZATION = 0
        _STATE_CHECK_CREG = 1
        _STATE_CHECK_COPS = 2
        current_state = _STATE_CHECK_CREG_INITIALIZATION
        while ticks_diff(ticks_ms(), timeout_timestamp) < 0:
            if current_state == _STATE_CHECK_CREG or current_state == _STATE_CHECK_CREG_INITIALIZATION:
                (status, lines) = self.send_at_cmd("AT+CREG?")
                if status:
                    regex_match = self._match_regex(regex_creg, lines)
                    if regex_match:
                        group_val = regex_match.group(1)
                        # 0: not registered, not trying to register
                        # 1: registered
                        # 2: not registered, trying to register
                        # 3: registration denied
                        # 4: Unknown
                        # 5: registed, roaming
                        if group_val == "1" or group_val == "5":
                            return True
                        elif group_val == "3":
                            return False
                        elif group_val == "2":
                            current_state = _STATE_CHECK_CREG
                        elif group_val == "0" and current_state == _STATE_CHECK_CREG:
                            current_state = _STATE_CHECK_COPS
                            self.send_at_cmd("AT+COPS=3,2")
            elif current_state == _STATE_CHECK_COPS:
                (mcc, mnc) = self.get_registered_mcc_mnc()
                if mcc is not None and mnc is not None:
                    return True
            sleep_ms(100)

        if current_state != _STATE_CHECK_COPS:
            (mcc, mnc) = self.get_registered_mcc_mnc()
            return mcc is not None and mnc is not None

        return False

    def attach(self, do_attach=True):
        (status, _) = self.send_at_cmd("at+cgatt={}".format("1" if do_attach else "0"), 144000)
        return status

    def detach(self):
        return self.attach(False)

    def is_attached(self):
        (status, lines) = self.send_at_cmd("at+cgatt?")
        return status and len(lines) > 0 and "+CGATT: 1" in lines[0]

    def has_sim(self):
        (status, lines) = self.send_at_cmd("at+cimi")
        return status

    def connect(self, timeoutms=30000):
        (status, lines) = self.send_at_cmd('AT+CGDATA="PPP",1', 30000, "CONNECT")
        if not status:
            return False

        from network import PPP

        self.ppp = PPP(self.uart)
        self.ppp.active(True)
        self.ppp.connect()

        start_timestamp = ticks_ms()
        timeout_timestamp = ticks_add(start_timestamp, timeoutms)
        while ticks_diff(ticks_ms(), timeout_timestamp) < 0:
            self.connected = self.is_connected()
            if self.connected:
                break
            sleep_ms(100)

        return self.connected

    def is_connected(self):
        if self.ppp:
            return self.ppp.isconnected()
        else:
            return False

    def disconnect(self):
        if self.ppp:
            self.ppp.active(False)

        self.connected = False
        (status_act, _) = self.send_at_cmd("AT+CGACT=0,1", 150000)
        status_att = self.detach()
        return status_att and status_act

    def force_time_update(self):
        pass

    def get_rssi(self):
        if self.ppp is None:
            regex_rssi = r"\+CSQ:\s*(\d+),\d+"
            self.rssi = -141
            (status, lines) = self.send_at_cmd("AT+CSQ")
            if status and len(lines) > 0:
                for line in lines:
                    match_res = ure.search(regex_rssi, line)
                    if match_res is not None:
                        try:
                            rssi_tmp = int(match_res.group(1))
                            if rssi_tmp >= 0 and rssi_tmp <= 31:
                                self.rssi = -113 + rssi_tmp * 2
                        except:
                            pass
                        break
        return self.rssi

    def get_extended_signal_quality(self):
        if self.ppp is None:
            self.rsrp = -141
            self.rsrq = -40
            (status, lines) = self.send_at_cmd("AT+CESQ")
            if status and len(lines) > 0:
                cesq_data = lines[0].split(",")
                rsrq_tmp = int(cesq_data[-2])
                rsrp_tmp = int(cesq_data[-1])
                if rsrq_tmp >= 0 and rsrq_tmp <= 34:
                    self.rsrq = -20 + rsrq_tmp * 0.5
                if rsrp_tmp >= 0 and rsrp_tmp <= 97:
                    self.rsrp = -141 + rsrp_tmp
        return (self.rsrp, self.rsrq)

    def get_lac_n_cell_id(self):
        if self.ppp is None:
            regex_creg = r"\+CREG:\s+\d,\d,\"(\w+)\",\"(\w+)\""
            self.lac = None
            self.ci = None
            (status, lines) = self.send_at_cmd("AT+CREG?")
            if status:
                for line in lines:
                    match_res = ure.search(regex_creg, line)
                    if match_res is not None:
                        logging.debug("LAC: {}, CI: {}".format(match_res.group(1), match_res.group(2)))
                        self.lac = int(match_res.group(1), 16)
                        self.ci = int(match_res.group(2), 16)
                        break
        return (self.lac, self.ci)

    def _match_regex(self, regex, lines):
        import ure

        if regex is not None or lines is not None:
            for line in lines:
                match_res = ure.search(regex, line)
                if match_res is not None:
                    return match_res
        return None

    def get_registered_mcc_mnc(self):
        if self.ppp is None:
            self.mcc = None
            self.mnc = None
            (status, lines) = self.send_at_cmd("AT+COPS?")
            if status:
                match_res = self._match_regex(r"\+COPS:\s+\d,2,\"(\d+)", lines)
                if match_res is not None:
                    try:
                        self.mcc = int(match_res.group(1)[0:3])
                        self.mnc = int(match_res.group(1)[3:5])
                    except:
                        pass
        return (self.mcc, self.mnc)

    def get_sim_card_ids(self):
        self.sim_imsi = None
        self.sim_iccid = None

        (status, lines) = self.send_at_cmd("at+cimi")
        if status:
            match_res = self._match_regex(r"(\d+)", lines)
            if match_res is not None:
                self.sim_imsi = match_res.group(1)

        return (self.sim_imsi, self.sim_iccid)

    # to be overriden by children
    def set_gps_state(self, poweron=True):
        logging.debug("base modem.set_gps_state is empty")
        pass

    # to be overriden by children
    def is_gps_on(self):
        logging.debug("base modem.is_gps_on is empty")
        return False

    # to be overriden by children
    def get_gps_position(self, timeoutms=300000, satellite_number_threshold=5):
        logging.debug("base modem.get_gps_position is empty")

    def send_at_cmd(self, command, timeoutms=30000, success_condition="OK", extra_error_condition=""):
        status = None
        responseLines = []

        if self.connected:
            responseLines = ["error: ppp connection active"]
            return (status, responseLines)

        if self.uart is None:
            responseLines = ["error: invalid uart"]
            return (status, responseLines)

        # clear incoming message buffer
        while self.uart.any():
            self.uart.readline()

        logging.debug("> " + command)
        write_success = self.uart.write(command + "\r\n")
        if not write_success:
            return (status, ["error: can not send command"])

        start_timestamp = ticks_ms()
        timeout_timestamp = ticks_add(start_timestamp, timeoutms)

        success_regex = "^([\\w\\s\\+]+)?" + success_condition
        error_regex = "(\\w+\\s+)?(ERROR|FAIL|(\\+CM[ES] ERROR)" + (
            "|({}))".format(extra_error_condition) if extra_error_condition else ")"
        )
        first_line = True
        is_echo_on = True

        watchdog_reset_period_ms = 1000
        last_wdt_reset_timestamp = ticks_ms()

        wdt_reset()

        while 1:
            now = ticks_ms()
            remaining_bytes = self.uart.any()
            if ticks_diff(now, timeout_timestamp) >= 0:
                if status is None:
                    status = False
                break

            if ticks_diff(now, last_wdt_reset_timestamp) >= watchdog_reset_period_ms:
                wdt_reset()
                last_wdt_reset_timestamp = now

            # if OK or ERROR has already been read though there are still
            # data on the UART, keep reading
            if status is not None and remaining_bytes == 0:
                break
            elif remaining_bytes != 0:
                line = self.uart.readline()
                try:
                    line = line if line is None else line.decode("utf8", "ignore").strip()
                except Exception as e:
                    logging.error("! " + str(line))
                    line = ""

                if line:
                    if line == command:
                        logging.debug("- <command echo is on - ignoring>")
                        is_echo_on = False
                        # possibly deactivate echo through ATE0
                    else:
                        if first_line:
                            logging.debug("< " + str(line))
                            first_line = False
                        else:
                            logging.debug("  " + str(line))
                        responseLines.append(line)
                        try:
                            if ure.search(success_regex, line) is not None:
                                status = True
                            elif ure.search(error_regex, line) is not None:
                                status = False
                        except Exception as e:
                            logging.exception(e, "Excluding line from success matching...")

            sleep_ms(5)

        if status is None:
            status = False

        return (status, responseLines)
