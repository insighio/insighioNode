from . import modem_base
import utime
import logging

class ModemBG600(modem_base.Modem):
    def __init__(self, power_on, power_key, modem_tx, modem_rx, gps_tx=None, gps_rx=None):
        super().__init__(power_on, power_key, modem_tx, modem_rx, gps_tx, gps_rx)

    def init(self, ip_version, apn):
        if self.is_alive():
            # set auto-registration
            # self.send_at_cmd("AT+CFUN=0")
            # disable unsolicited report of network registration
            self.send_at_cmd("AT+CREG=0")
            self.send_at_cmd("AT+CFUN=1")

            self.send_at_cmd('AT+QCFG="nwscanmode",1,1')

            self.send_at_cmd('AT+CGDCONT=1,"IP","' + apn + '"')

        #     AT+CGDCONT=1,"PPP","iot.1nce.net"

            self.set_technology() # placeholder

            return True
        return False

    def connect(self, timeoutms=30000):
        for i in range(0, 5):
            (status, lines) = self.send_at_cmd('AT+CGACT=1,1')
            if status:
                break

        if not status:
            return False

        (status, lines) = self.send_at_cmd('ATD*99***1#', 30000, "CONNECT(\\s*\\w+)?")
        if not status:
            return False

        from network import PPP

        logging.debug("PPP: instantiating...")
        self.ppp = PPP(self.uart)
        logging.debug("PPP: activating...")
        self.ppp.active(True)
        logging.debug("PPP: connecting...")
        self.ppp.connect()

        start_timestamp = utime.ticks_ms()
        timeout_timestamp = start_timestamp + timeoutms
        while utime.ticks_ms() < timeout_timestamp:
            self.connected = self.is_connected()
            if self.connected:
                break
            utime.sleep_ms(100)

        logging.debug("PPP successsful: " + str(self.connected))

        return self.connected
