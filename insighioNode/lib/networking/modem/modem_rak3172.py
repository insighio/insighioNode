from . import modem_base
import logging
import ure
import gpio_handler
from utime import sleep_ms, ticks_ms


class ModemRak3172(modem_base.Modem):
    def __init__(self, modem_reset, modem_tx, modem_rx):
        super().__init__(None, None, modem_tx, modem_rx)
        self.connection_status = False
        self.data_over_ppp = True
        self.modem_reset = modem_reset
        self.LORA_REGIONS = ["EU433","CN470","RU864","IN865","EU868","US915","AU915","KR920","AS923-1","AS923-2","AS923-3","AS923-4","LA915"]

    def power_on(self):
        pass

    def power_off(self):
        pass

    def init(self):
        #LPM makes the device sleep automatically after sending AT commands
        (status, lines) = self.send_at_cmd("AT+LPM=1")
        return status


    def reset(self):
        # simulate the double press of a reset button on modem_reset pin
        logging.debug("About to reset Rak3172 modem")
        gpio_handler.set_pin_value(self.modem_reset, 0)
        sleep_ms(100)
        gpio_handler.set_pin_value(self.modem_reset, 1)
        sleep_ms(100)
        gpio_handler.set_pin_value(self.modem_reset, 0)
        sleep_ms(100)
        gpio_handler.set_pin_value(self.modem_reset, 1)
        sleep_ms(100)
        gpio_handler.set_pin_value(self.modem_reset, 0)
        logging.debug("Rak3172 modem has been reset")

    def is_connected(self):
        # has joined ??
        (status, lines) =  self.send_at_cmd("AT+NJS=?")

        line_regex = r"AT+NJS=(\d+)"
        if status:
            match = ure.search(line_regex, lines[0])
            if match is None:
                continue
            return match.group(1) == "1"
        return False

    def set_dev_eui(self, dev_eui):
        (status, lines) = self.send_at_cmd("AT+DEVEUI=" + dev_eui)
        return status

    def set_app_eui(self, app_eui):
        (status, lines) = self.send_at_cmd("AT+APPEUI=" + app_eui)
        return status

    def set_app_key(self, app_key):
        (status, lines) = self.send_at_cmd("AT+APPKEY=" + app_key)
        return status

    def set_region(self, region):
        region_index = -1
        try:
            region_index = self.LORA_REGIONS.index(region)
            (status, lines) = self.send_at_cmd("AT+BAND=" + region)
            return status
        except:
            return False

    def set_dr(self, dr):
        (status, lines) = self.send_at_cmd("AT+DR{}".format(dr))
        return status

    def set_confirm(self, confirm):
        (status, lines) = self.send_at_cmd("AT+CFM={}".format(1 if confirm else 0))
        return status

    def set_adr(self, adr):
        (status, lines) = self.send_at_cmd("AT+ADR={}".format(1 if adr else 0))
        return status

    def set_retries(self, retries):
        (status, lines) = self.send_at_cmd("AT+RETY={}".format(retries if retries else 0))
        return status

    def join(self):
        (join_succeded, lines) = self.send_at_cmd("AT+JOIN")

        if join_succeded:
            start_time = ticks_ms()
            end_time = start_time + 30000
            while ticks_ms() < end_time:
                if self.is_connected():
                    break
                sleep_ms(50)

        return self.is_connected()

    def send(self, bytes_hex):
        # random port -> 5
        (status, lines) = self.send_at_cmd("AT+SEND=5:" + bytes_hex)
        return status
