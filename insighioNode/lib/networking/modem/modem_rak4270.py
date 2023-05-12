from . import modem_base
import utime
import logging
import ure
import device_info
import ure
from machine import Pin
import gpio_handler


class ModemRak4270(modem_base.Modem):
    def __init__(self, power_on, modem_tx, modem_rx):
        super().__init__(power_on, None, modem_tx, modem_rx)
        self.connection_status = False
        self.data_over_ppp = True

    def power_on(self):
        # network registration
        gpio_handler.set_pin_value(self.modem_power_on, 1)
        # modem boot
        logging.info("Waiting for the lora modem to finish power on")
        status = self.wait_for_modem_power_on("at+version")
        logging.info("Modem ready: " + str(status))

    def power_off(self):
        gpio_handler.set_pin_value(self.modem_power_on, 0)
        logging.debug("modem powered off")

    def is_connected(self):
        status = self.send_at_cmd('at+get_config=lora:channel')
        (status, lines) = self.send_at_cmd('at+get_config=lora:status')
        line_regex = r'Joined Network\s*:\s*(\w+)'
        for line in lines:
            match = ure.search(line_regex, line)
            if match is None:
                continue

            return match.group(1) == 'true'
        return False

    def set_dev_eui(self, dev_eui):
        (status, lines) = self.send_at_cmd('at+set_config=lora:dev_eui:' + dev_eui)
        return status

    def set_app_eui(self, app_eui):
        (status, lines) = self.send_at_cmd('at+set_config=lora:app_eui:' + app_eui)
        return status

    def set_app_key(self, app_key):
        (status, lines) = self.send_at_cmd('at+set_config=lora:app_key:' + app_key)
        return status

    def set_region(self, region):
        (status, lines) = self.send_at_cmd('at+set_config=lora:region:' + region)
        return status

    def set_dr(self, dr):
        (status, lines) = self.send_at_cmd('at+set_config=lora:dr:{}'.format(dr))
        return status

    def join(self):
        self.send_at_cmd('at+set_config=lora:ch_mask:8:0')
        self.send_at_cmd('at+set_config=lora:ch_mask:9:0')
        self.send_at_cmd('at+set_config=lora:ch_mask:10:0')
        self.send_at_cmd('at+set_config=lora:ch_mask:11:0')
        self.send_at_cmd('at+set_config=lora:ch_mask:12:0')

        (status, lines) = self.send_at_cmd('at+join')
        return status

    def send(self, bytes_hex):
        (status, lines) = self.send_at_cmd('at+send=lora:5:' + bytes_hex)
        return status
