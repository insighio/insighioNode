import utime
from machine import Pin, UART
import ure
# TODO: check if some regexes need to be precompiled: ure.compile('\d+mplam,pla')

# Modem state
MODEM_DETTACHED = -1  # initial value, nothing happened
MODEM_ACTIVATED = 0
MODEM_ATTACHED = 1
MODEM_CONNECTED = 2


class Modem:
    def __init__(self, uart):
        self.uart = uart
        self.connected = False
        self.ppp = None

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
        if not status or len(lines) < 3:
            return None

        if lines[0].lower().startwith("quectel"):
            if "mc60" in lines[1].lower():
                return "MC60"
            elif "bg600" in lines[1].lower():
                return "BG600"
        return lines[1]

    def power_on(self):
        # network registration
        p0 = Pin(26, Pin.OUT)
        p0.on()
        # modem boot
        pinNum = 23
        p0 = Pin(pinNum, Pin.OUT)
        p0.on()
        print("Output Pin {} {}".format(pinNum, p0.value()))
        utime.sleep_ms(1200)
        p0.off()
        print("Output Pin {} {}".format(pinNum, p0.value()))
        utime.sleep_ms(2000)

    def power_off(self):
        pinNum = 23
        p0 = Pin(pinNum, Pin.OUT)
        p0.on()
        print("Output Pin {} {}".format(pinNum, p0.value()))
        utime.sleep_ms(800)
        p0.off()

    def init(self):
        if not self.is_alive():
            self.power_on()

        if self.is_alive():
            # disable command echo
            self.send_at_cmd('ATE0')

            # set auto-registration
            self.send_at_cmd("AT+COPS=0")

            # disable unsolicited report of network registration
            self.send_at_cmd("AT+CREG=0")
            return True

        return False

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
            utime.sleep_ms(1000)
        return False

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
