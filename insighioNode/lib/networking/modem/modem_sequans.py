from modem_base import Modem
from network import LTE
import logging


class ModemSequans(Modem):
    def __init__(self, uart):
        self.lte = LTE()

    def power_on(self):
        self.lte.init()

    def power_off(self):
        self.lte.deinit(dettach=True, reset=True)

    def init(self):
        return True

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
