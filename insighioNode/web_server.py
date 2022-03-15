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
        if device_info.is_esp32():
            self.wlan = network.WLAN(network.STA_IF)
        else:
            self.wlan = network.WLAN(mode=network.WLAN.STA, antenna=network.WLAN.INT_ANT)
        try:
            nets = self.wlan.scan()
            if not device_info.is_esp32():
                self.wlan.deinit()
            else:
                self.wlan.active(False)
            nets = nets[:min(10, len(nets))]
        except Exception as e:
            logging.error("WiFi scan failed. Will provide empty SSID list")
            nets = []
        # nets = list(filter(lambda net: net.rssi > -89, nets))
        if device_info.is_esp32():
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
        else:
            self.available_nets = nets
        self.ssidCustom = "insigh-" + device_info.get_device_id()[0][-4:]
        logging.info("SSID: " + self.ssidCustom)
        logging.info("Original device id: " + device_info.get_device_id()[0])
        device_info.set_defaults()

    def saveGlobalVarIfFoundInLine(self, line, strToSearch, globalVarName, delimiter):
        if ure.match(strToSearch, line):
        #if line.startswith(strToSearch):
            elems = line.split(delimiter)
            if len(elems) > 1 and elems[1] != "":
                self.pyhtmlMod.SetGlobalVar(globalVarName, elems[1])
                logging.debug("var '{}' = {}".format(globalVarName, elems[1]))
                return True
        return False

    def extractInsighioIds(self):
        projectConfig = utils.readFromFile(device_info.get_device_root_folder() + "apps/demo_console/demo_config.py").strip().split("\n")
        linesCount = len(projectConfig)

        i = 0
        euisFilled = 0
        self.pyhtmlMod.SetGlobalVar("insighioChannelId", "")
        self.pyhtmlMod.SetGlobalVar("insighioControlChannel", "")
        self.pyhtmlMod.SetGlobalVar("insighioDeviceId", "")
        self.pyhtmlMod.SetGlobalVar("insighioDeviceToken", "")

        while i < linesCount:
            if (self.saveGlobalVarIfFoundInLine(projectConfig[i], r'^(\s*\w+\.)?message_channel_id', "insighioChannelId", '"') or
                self.saveGlobalVarIfFoundInLine(projectConfig[i], r'^(\s*\w+\.)?control_channel_id', "insighioControlChannel", '"') or
                self.saveGlobalVarIfFoundInLine(projectConfig[i], r'^(\s*\w+\.)?thing_id', "insighioDeviceId", '"') or
                self.saveGlobalVarIfFoundInLine(projectConfig[i], r'^(\s*\w+\.)?thing_token', "insighioDeviceToken", '"')):
               euisFilled = euisFilled + 1

            if euisFilled == 4:
                return True
            else:
                i = i + 1

        return False

    def extractLoRaUIDS(self):
        loraDevEUI = ""
        try:
            logging.debug("Lora MAC: " + str(device_info.get_lora_mac()))
            loraDevEUI = device_info.get_lora_mac()[0]
        except Exception as e:
            logging.exception(e, "lora deveui")
            pass
        projectConfig = utils.readFromFile(device_info.get_device_root_folder() + "apps/demo_console/demo_config.py").strip().split("\n")
        linesCount = len(projectConfig)
        i = 0
        euisFilled = 0
        self.pyhtmlMod.SetGlobalVar("loraDevEUI", loraDevEUI)
        self.pyhtmlMod.SetGlobalVar("loraAppEUI", "")
        self.pyhtmlMod.SetGlobalVar("loraAppKey", "")

        while i < linesCount:
            if (self.saveGlobalVarIfFoundInLine(projectConfig[i], '_APP_EUI', "loraAppEUI", '"') or
                self.saveGlobalVarIfFoundInLine(projectConfig[i], '_APP_KEY', "loraAppKey", '"')):
                euisFilled = euisFilled + 1

            if euisFilled == 3:
                return True
            else:
                i = i + 1

        return False

    def storeIds(self):
        self.extractLoRaUIDS()
        self.extractInsighioIds()
        self.pyhtmlMod.SetGlobalVar("wifiAvailableNets", self.available_nets)

    def start(self, timeoutMs=-1):
        logging.info('\n\n** Init WLAN mode and WAP2')
        device_info.wdt_reset()
        if device_info.is_esp32():
            self.wlan = network.WLAN(network.AP_IF)
            self.wlan.active(True)
            self.wlan.config(essid=self.ssidCustom)  # set the ESSID of the access point
            self.wlan.config(password='insighiodev')
            self.wlan.config(authmode=3)  # 3 -- WPA2-PSK
            self.wlan.config(max_clients=1)  # set how many clients can connect to the network
        else:
            self.wlan = network.WLAN(mode=network.WLAN.AP, ssid=self.ssidCustom, auth=(network.WLAN.WPA2, 'insighiodev'))

        device_info.wdt_reset()

        # Loads the PyhtmlTemplate module globally and configure it,
        self.pyhtmlMod = MicroWebSrv2.LoadModule('PyhtmlTemplate')
        self.pyhtmlMod.ShowDebug = True
        self.storeIds()

        self.mws2 = MicroWebSrv2()
        self.mws2.SetEmbeddedConfig()
        self.mws2.BindAddress = ('192.168.4.1', 80)

        # Starts the server as easily as possible in managed mode,
        self.mws2.StartManaged()

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
            while self.mws2.IsRunning and (timeoutMs == -1 or (timeoutMs > 0
              and (not self.wlan.isconnected() and utime.ticks_ms() < end_time)
              or (self.wlan.isconnected() and utime.ticks_ms() < end_time_when_connected))):
                device_info.set_led_color(purple)
                if not self.wlan.isconnected():
                    utime.sleep_ms(100)
                    device_info.set_led_color('black')

                device_info.wdt_reset()
                utime.sleep_ms(1000)
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
        if not device_info.is_esp32():
            self.wlan.deinit()
        else:
            self.wlan.active(False)
        logging.info('Bye\n')
