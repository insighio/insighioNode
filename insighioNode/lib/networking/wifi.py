# from network import WLAN
import network
from machine import RTC
from utime import ticks_ms, sleep_ms, time
import logging

wl = None

class WifiConfig:
    def __init__(self):
        self.ssid = ""
        self.pass = _DEFAULT_LORA_APP_EUI
        self.max_connection_attempt_time_sec = 60


def get_instance():
    global wl
    if not wl:
        wl = network.WLAN(network.STA_IF)
    return wl


def connect_to_network(wifi_ssid, wifi_pass, max_connection_attempt_time_sec):
    connection_status = False
    conn_attempt_duration = -1
    scan_attempt_duration = -1
    rssi = -121
    channel = -1

    get_instance()
    wl.active(True)

    try:
        # connect
        start_time = ticks_ms()
        connect_timeout = start_time + max_connection_attempt_time_sec * 1000
        wl.connect(wifi_ssid, wifi_pass)
        while not wl.isconnected() and ticks_ms() < connect_timeout:
            sleep_ms(10)
        conn_attempt_duration = ticks_ms() - start_time

        if wl.isconnected():
            logging.debug("Connected to " + wifi_ssid + " with IP address:" + wl.ifconfig()[0])
            connection_status = True

            update_time_ntp()

            # obtain some extra KPIs from joined AP
            channel = -1
            try:
                rssi = wl.status("rssi")
            except:
                rssi = -1
        else:
            logging.debug("Not connected to {}".format(wifi_ssid))
    except Exception as e:
        logging.exception(e, "Exception during wifi connect:")

    return (connection_status, conn_attempt_duration, scan_attempt_duration, channel, rssi)


def connect(wifi_cfg):
    (connection_status, conn_attempt_duration, _, channel, rssi) = connect_to_network(wifi_cfg.ssid, wifi_cfg.pass, wifi_cfg.max_connection_attempt_time_sec)
    return (connection_status, conn_attempt_duration, scan_attempt_duration, channel, rssi)


def is_connected():
    return network.WLAN(network.STA_IF).isconnected()


def deactivate():
    """Actions implemented when turning off wifi, before deep sleep"""

    deactivation_status = False
    start_time_deactivation = ticks_ms()

    try:
        get_instance()
        wl.disconnect()
        wl.active(False)
    except:
        logging.debug("WiFi disconnecting ignored.")

    return (deactivation_status, ticks_ms() - start_time_deactivation)


def update_time_ntp():
    import ntptime
    import utils

    rtc = RTC()

    logging.info("time before sync: " + str(rtc.datetime()))
    ntptime.host = "pool.ntp.org"
    cnt = 0
    max_tries = 5
    while cnt < max_tries:
        try:
            epoch_before = time()
            ntptime.settime()
            logging.info("time set")
            break
        except:
            logging.info("time failed")
        cnt += 1
    epoch_diff = time() - epoch_before
    utils.writeToFlagFile("/epoch_diff", "{}".format(epoch_diff))
    logging.info("time after sync: " + str(rtc.datetime()))


def getSignalQuality():
    return get_instance().status("rssi")
