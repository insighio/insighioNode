import network

import sys
from external.MicroWebSrv2 import *

import device_info
import utime
import utils
import machine
import logging
import ure


class WebServer:
    def __init__(self):
        device_info.set_defaults()
        logging.info("Initializing WiFi APs in range")
        self.wlan = None
        self.wlan = network.WLAN(network.STA_IF)

        try:
            nets = self.wlan.scan()
            self.wlan.active(False)
            nets = nets[:min(10, len(nets))]
        except Exception as e:
            logging.error("WiFi scan failed. Will provide empty SSID list")
            nets = []

        self.available_nets = []

        class TmpSSIDELEm:
            def __init__(self):
                self.ssid = None
                self.rssi = None

        for net in nets:
            tmpObj = TmpSSIDELEm()
            tmpObj.ssid = net[0].decode('UTF-8')
            tmpObj.rssi = net[3]
            self.available_nets.append(tmpObj)

        self.ssidCustom = "insigh-" + device_info.get_device_id()[0][-4:]
        logging.info("SSID: " + self.ssidCustom)
        logging.info("Original device id: " + device_info.get_device_id()[0])
        device_info.set_defaults()

    def storeIds(self):
        self.pyhtmlMod.SetGlobalVar("wifiAvailableNets", self.available_nets)
        from www import stored_config_utils
        try:
            keyValues = stored_config_utils.get_config_values()
            for key in keyValues:
                self.pyhtmlMod.SetGlobalVar(key, keyValues[key])
        except Exception as e:
            logging.exception(e, "Unable to retrieve old configuration")
            pass

    def start(self, timeoutMs=-1):
        logging.info('\n\n** Init WLAN mode and WAP2')
        device_info.wdt_reset()
        self.wlan = network.WLAN(network.AP_IF)
        self.wlan.active(True)
        self.wlan.config(essid=self.ssidCustom)  # set the ESSID of the access point
        self.wlan.config(password='insighiodev')
        self.wlan.config(authmode=3)  # 3 -- WPA2-PSK
        self.wlan.config(max_clients=1)  # set how many clients can connect to the network

        device_info.wdt_reset()

        # Loads the PyhtmlTemplate module globally and configure it,
        self.pyhtmlMod = MicroWebSrv2.LoadModule('PyhtmlTemplate')
        self.pyhtmlMod.ShowDebug = True
        self.storeIds()

        MicroWebSrv2._HTML_ESCAPE_CHARS={}
        self.mws2 = MicroWebSrv2()
        self.mws2.SetEmbeddedConfig()
        self.mws2.BindAddress = ('192.168.4.1', 80)

        # Starts the server as easily as possible in managed mode
        # 1 parallel process, 32K stack size
        #if device_info.get_hw_module_verison() == "esp32s3":

        if device_info.get_hw_module_verison() == "esp32s2":
            self.mws2.StartManaged(0, 16*1024)
        else:
            self.mws2.StartManaged(1, 32*1024)
        # else:
        #     self.mws2.StartManaged(1, 32*1024)

        logging.info("Web UI started")

        purple = 0x4c004c
        device_info.set_led_color(purple)

        device_info.wdt_reset()

        # Main program loop until keyboard interrupt,
        try:
            start_time = utime.ticks_ms()
            end_time = start_time + timeoutMs
            # 5 minutes timeout if timeoutMs is > -1 and someone has connected to the wifi
            # self.wlan.isconnected() is confirmed to be NOT supported by firmware 1.18
            end_time_when_connected = start_time + 600000
            is_connected  = False
            now = 0
            cnt = 0
            while True:
                is_connected = self.wlan.isconnected()
                now = utime.ticks_ms()
                if (self.mws2.IsRunning
                    and (
                        timeoutMs <= 0
                        or (
                            (not is_connected and now < end_time)
                            or (is_connected and now < end_time_when_connected)
                           )
                        )
                   ):
                   pass
                else:
                    break
                device_info.set_led_color(purple)
                if not is_connected:
                    utime.sleep_ms(100)
                    device_info.set_led_color('black')

                if cnt % 10 == 0:
                    device_info.wdt_reset()
                cnt += 1
                utime.sleep_ms(500)
        except KeyboardInterrupt:
            pass

        device_info.set_led_color('black')

        self.stop()

    def stop(self):
        # End
        self.mws2.Stop()
        for m in sys.modules:
            try:
                module = str(m)
                if module.startswith("external.MicroWebSrv2"):
                    del sys.modules[module]
            except Exception as e:
                sys.print_exception(e)
        self.wlan.active(False)
        logging.info('Bye\n')
