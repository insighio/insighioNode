import utime
from machine import Pin, UART
import ure
# TODO: check if some regexes need to be precompiled: ure.compile('\d+mplam,pla')


class Modem:
    def __init__(self, cfg):
        self.connected = False
        self.ppp = None
        self.uart = None
        self.modem_power_on = None
        self.modem_power_key = None

        if cfg._UC_UART_MODEM_TX is not None and cfg._UC_UART_MODEM_RX is not None:
            self.uart = UART(1)
            self.uart.init(115200, bits=8, parity=None, stop=1, tx=cfg._UC_UART_MODEM_TX, rx=cfg._UC_UART_MODEM_RX, timeout=500, timeout_char=1000)

        if cfg._UC_IO_RADIO_ON:
            self.modem_power_on = cfg._UC_IO_RADIO_ON

        if cfg._UC_IO_PWRKEY:
            self.modem_power_key = cfg._UC_IO_PWRKEY

        if not self.is_alive():
            self.power_on()

    def is_alive(self):
        (status, response) = self.send_at_cmd("AT", 5000)
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
        print("Output Pin {} {}".format(pinNum, p0.value()))
        utime.sleep_ms(1200)
        p0.off()
        print("Output Pin {} {}".format(pinNum, p0.value()))

    def power_off(self):
        p0 = Pin(self.modem_power_key, Pin.OUT)
        p0.on()
        print("Output Pin {} {}".format(pinNum, p0.value()))
        utime.sleep_ms(800)
        p0.off()
        Pin(self.modem_power_on, Pin.OUT).off()

    def init(self, cfg):
        if self.is_alive():
            # disable command echo
            self.send_at_cmd('ATE0')

            # set auto-registration
            self.send_at_cmd("AT+CFUN=0")
            # disable unsolicited report of network registration
            self.send_at_cmd("AT+CREG=0")

            self.send_at_cmd("AT+CGDCONT=1,\"" + cfg._IP_VERSION + "\",\"" + cfg._APN + "\"")
            self.set_technology(cfg)

            lte.send_at_cmd("AT+CFUN=1")
            return True
        return False

    def set_technology(self, cfg):
        pass

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
                    if regex_match and regex_match.group(1) == "1":
                        return True
            utime.sleep_ms(100)
        return False

    def is_attached(self):
        (status, lines) = self.send_at_cmd("at+cgatt?")
        return (status and len(lines) > 0 and '+CGATT: 1' in lines[0])

    def connect(self, timeoutms=30000):
        (status, lines) = self.send_at_cmd('AT+CGDATA="PPP",1', 30000, "CONNECT")
        if not status:
            return False

        import network

        self.ppp = network.PPP(self.uart)
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
        (status, _) = self.send_at_cmd("AT+CGACT=0,1")
        return status

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
        (status, lines) = lte.send_at_cmd('AT+CESQ').split(',')
        if status and len(lines) > 0:
            cesq_data = lines[0].split(',')
            rsrq_tmp = int(cesq_data[-2])
            rsrp_tmp = int(cesq_data[-1])
            if(rsrq_tmp >= 0 and rsrq_tmp <= 34):
                rsrq = -20 + rsrq_tmp * 0.5
            if(rsrp_tmp >= 0 and rsrp_tmp <= 97):
                rsrp = -141 + rsrp_tmp
        return (rsrp, rsrq)

    # to be overriden by children
    def set_gps_state(self, poweron=True):
        pass

    # to be overriden by children
    def is_gps_on(self):
        return False

    # to be overriden by children
    def get_gps_position(self, timeoutms=300000):
        pass

    def send_at_cmd(self, command, timeoutms=30000, success_condition="OK"):
        status = None
        responseLines = []

        if self.connected:
            responseLines = ['error: ppp connection active']
            return (status, responseLines)

        # clear incoming message buffer
        while self.uart.any():
            print(self.uart.readline())

        print("> " + command)
        write_success = self.uart.write(command + '\r\n')
        if not write_success:
            return (status, ['error: can not send command'])

        start_timestamp = utime.ticks_ms()
        timeout_timestamp = start_timestamp + timeoutms

        success_regex = "^(\\w+\\s+)?(" + success_condition + ")$"
        error_regex = "^((\\w+\\s+)?(ERROR|FAIL)$)|(\\+CM[ES] ERROR)"
        first_line = True

        while True:
            remaining_bytes = self.uart.any()
            if(utime.ticks_ms() >= timeout_timestamp):
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
                print("! " + str(line))
                line = ""

            if line:
                if first_line:
                    print("< " + str(line))
                    first_line = False
                else:
                    print("  " + str(line))
                responseLines.append(line)
                if ure.search(success_regex, line) is not None:
                    status = True
                elif ure.search(error_regex, line) is not None:
                    status = False

            utime.sleep_ms(50)

        if status is None:
            status = False

        return (status, responseLines)
