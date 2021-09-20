import utime
from machine import Pin, UART
import ure
import logging
import device_info
# TODO: check if some regexes need to be precompiled: ure.compile('\d+mplam,pla')


class Modem:
    def __init__(self, power_on=None, power_key=None, modem_tx=None, modem_rx=None, gps_tx=None, gps_rx=None):
        self.connected = False
        self.ppp = None
        self.uart = None
        self.modem_power_on = None
        self.modem_power_key = None
        self.apn = None
        self.gps_timestamp = None
        self.gps_date = None
        self.use_timezone_over_gmt = True

        if modem_tx is not None and modem_rx is not None:
            self.uart = UART(1, 115200, tx=modem_tx, rx=modem_rx)
            self.uart.init(115200, bits=8, parity=None, stop=1, tx=modem_tx, rx=modem_rx, timeout=500, timeout_char=1000)

        self.modem_power_on = power_on
        self.modem_power_key = power_key

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

        return lines[1].lower()

    def power_on(self):
        # network registration
        Pin(self.modem_power_on, Pin.OUT).on()
        # modem boot
        p0 = Pin(self.modem_power_key, Pin.OUT)
        p0.on()
        logging.debug("Output Pin {} {}".format(self.modem_power_key, p0.value()))
        utime.sleep_ms(1200)
        p0.off()
        logging.debug("Output Pin {} {}".format(self.modem_power_key, p0.value()))
        logging.info("Waiting for the modem to finish power on")
        status = self.wait_for_modem_power_on()
        logging.info("Modem ready: " + str(status))

        if status:
            self.send_at_cmd("at+cmee=2")

    def wait_for_modem_power_on(self):
        retries = 0
        while retries < 10:
            (status, response) = self.send_at_cmd("AT", 500)
            if status:
                return True
            retries += 1
        return False

    def power_off(self):
        p0 = Pin(self.modem_power_key, Pin.OUT)
        p0.on()
        logging.debug("Output Pin {} {}".format(self.modem_power_key, p0.value()))
        utime.sleep_ms(800)
        p0.off()
        p0 = Pin(self.modem_power_on, Pin.OUT)
        p0.off()
        logging.debug("Output Pin {} {}".format(self.modem_power_on, p0.value()))

    def init(self, ip_version, apn, technology):
        if self.is_alive():
            self.apn = apn
            # disable command echo
            self.send_at_cmd('ATE0')
            # set auto-registration
            # self.send_at_cmd("AT+CFUN=0")
            self.send_at_cmd("AT+COPS=3,2")  # set network name as numeric value
            self.send_at_cmd("AT+CREG=2")  # enable LAC, CI reporting
            self.send_at_cmd("AT+CTZU=1")  # automatic time update
            self.send_at_cmd("AT+CFUN=1")

            self.send_at_cmd('AT+CGDCONT=1,"' + ip_version + '","' + apn + '"')

            self.set_technology(technology)

            return True
        return False

    def set_technology(self, technology):
        pass

    def get_network_date_time(self):
        start_timestamp = utime.ticks_ms()
        timeout_timestamp = start_timestamp + 10000
        regex = '(\\d+)\\/(\\d+)\\/(\\d+),(\\d+):(\\d+):(\\d+)([+-]\\d+)'
        while utime.ticks_ms() < timeout_timestamp:
            (status, lines) = self.send_at_cmd("AT+CCLK?")
            if status and len(lines) > 0:
                reg_res = ure.search(regex, lines[0])
                if reg_res:
                    logging.debug("Setting cellular RTC")
                    try:
                        year = int(reg_res.group(1))
                        if year < 100:
                            year += 2000
                        result = (year,
                            int(reg_res.group(2)),
                            int(reg_res.group(3)),
                            0,  # day of week
                            int(reg_res.group(4)) + (int(float(reg_res.group(7)) // 4) if self.use_timezone_over_gmt else 0),
                            int(reg_res.group(5)) + (int((float(reg_res.group(7)) % 4) * 15) if self.use_timezone_over_gmt else 0),
                            int(reg_res.group(6)),
                            0)  # usec
                        return result
                    except Exception as e:
                        logging.exception(e, "Error reading network time")
                        pass
                else:
                    logging.debug("Network time not ready yet")
            utime.sleep_ms(250)


    def wait_for_registration(self, timeoutms=30000):
        status = False

        start_timestamp = utime.ticks_ms()
        timeout_timestamp = start_timestamp + timeoutms
        regex_creg = "\\+CREG:\\s+\\d,(\\d)"
        while utime.ticks_ms() < timeout_timestamp:
            (status, lines) = self.send_at_cmd('AT+CREG?')
            if status and len(lines) > 0:
                regex_match = None
                for line in lines:
                    regex_match = ure.search(regex_creg, line)
                    if regex_match and (regex_match.group(1) == "1" or regex_match.group(1) == "5"):
                        return True
            utime.sleep_ms(100)
        return False

    def attach(self, do_attach=True):
        (status, _) = self.send_at_cmd('at+cgatt={}'.format("1" if do_attach else "0"))
        return status

    def detach(self):
        return self.attach(False)

    def is_attached(self):
        (status, lines) = self.send_at_cmd("at+cgatt?")
        return (status and len(lines) > 0 and '+CGATT: 1' in lines[0])

    def connect(self, timeoutms=30000):
        (status, lines) = self.send_at_cmd('AT+CGDATA="PPP",1', 30000, "CONNECT")
        if not status:
            return False

        from network import PPP

        self.ppp = PPP(self.uart)
        self.ppp.active(True)
        self.ppp.connect()

        start_timestamp = utime.ticks_ms()
        timeout_timestamp = start_timestamp + timeoutms
        while utime.ticks_ms() < timeout_timestamp:
            self.connected = self.is_connected()
            if self.connected:
                break
            utime.sleep_ms(100)

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
        (status_act, _) = self.send_at_cmd("AT+CGACT=0,1")
        status_att = self.detach()
        return status_att and status_act

    def get_rssi(self):
        rssi = -141
        (status, lines) = self.send_at_cmd('AT+CSQ')
        if status and len(lines) > 0:
            rssi_tmp = int(lines[0].split(',')[0].split(' ')[-1])
            if(rssi_tmp >= 0 and rssi_tmp <= 31):
                return -113 + rssi_tmp * 2
        else:
            return -141

    def get_extended_signal_quality(self):
        rsrp = -141
        rsrq = -40
        (status, lines) = self.send_at_cmd('AT+CESQ')
        if status and len(lines) > 0:
            cesq_data = lines[0].split(',')
            rsrq_tmp = int(cesq_data[-2])
            rsrp_tmp = int(cesq_data[-1])
            if(rsrq_tmp >= 0 and rsrq_tmp <= 34):
                rsrq = -20 + rsrq_tmp * 0.5
            if(rsrp_tmp >= 0 and rsrp_tmp <= 97):
                rsrp = -141 + rsrp_tmp
        return (rsrp, rsrq)

    def get_lac_n_cell_id(self):
        regex_creg = r"\+CREG:\s+\d,\d,\"(\w+)\",\"(\w+)\""
        lac = None
        ci = None
        (status, lines) = self.send_at_cmd('AT+CREG?')
        if status:
            for line in lines:
                match_res = ure.search(regex_creg, line)
                if match_res is not None:
                    lac = int('0x' + match_res.group(1))
                    ci = int('0x' + match_res.group(2))
                    break
        return (lac, ci)

    def get_registered_mcc_mnc(self):
        regex_cops = r"\+COPS:\s+\d,2,\"(\d+)"
        mcc = None
        mnc = None
        (status, lines) = self.send_at_cmd('AT+COPS?')
        if status:
            for line in lines:
                match_res = ure.search(regex_cops, line)
                if match_res is not None:
                    mcc = match_res.group(1)[0:3]
                    mnc = match_res.group(1)[3:5]
                    break
        return (mcc, mnc)

    # to be overriden by children
    def set_gps_state(self, poweron=True):
        logging.debug("base modem.set_gps_state is empty")
        pass

    # to be overriden by children
    def is_gps_on(self):
        logging.debug("base modem.is_gps_on is empty")
        return False

    # to be overriden by children
    def get_gps_position(self, timeoutms=300000):
        logging.debug("base modem.get_gps_position is empty")
        pass

    def send_at_cmd(self, command, timeoutms=30000, success_condition="OK"):
        status = None
        responseLines = []

        if self.connected:
            responseLines = ['error: ppp connection active']
            return (status, responseLines)

        if self.uart is None:
            responseLines = ['error: invalid uart']
            return (status, responseLines)

        # clear incoming message buffer
        while self.uart.any():
            self.uart.readline()

        logging.debug("> " + command)
        write_success = self.uart.write(command + '\r\n')
        if not write_success:
            return (status, ['error: can not send command'])

        start_timestamp = utime.ticks_ms()
        timeout_timestamp = start_timestamp + timeoutms

        success_regex = "^([\\w\\s\\+]+)?(" + success_condition + ")$"
        error_regex = "^((\\w+\\s+)?(ERROR|FAIL)$)|(\\+CM[ES] ERROR)"
        first_line = True
        is_echo_on = True

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
                    if ure.search(success_regex, line) is not None:
                        status = True
                    elif ure.search(error_regex, line) is not None:
                        status = False

            utime.sleep_ms(50)

        if status is None:
            status = False

        return (status, responseLines)
