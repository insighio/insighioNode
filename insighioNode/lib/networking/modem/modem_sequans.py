from modem_base import Modem
from network import LTE
import logging


class ModemSequans(Modem):
    def __init__(self, uart):
        self.lte = LTE()

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
        self.lte.init()

    def power_off(self):
        self.lte.deinit(dettach=True, reset=True)

    def init(self):
        return True

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
        return self.lte.isconnected()

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

    def get_gps_position(self, timeoutms=300000):
        return None

    def send_at_cmd(self, command, timeoutms=30000, success_condition="OK"):
        response = ""
        status = False

        logging.debug(command)
        response = self.lte.send_at_cmd(command)
        if response:
            response = response.strip().splitlines()
        logging.debug(response)
        status = (response.find("OK") != -1)

        return (status, response)
