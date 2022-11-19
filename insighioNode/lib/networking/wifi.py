#from network import WLAN
import network
import utime
import machine
import logging
import device_info


def connect(known_nets, max_connection_attempt_time_sec, force_no_scan=True):
    """ Connect to WiFi network based on a predefined list of candidates
            Returns a list of a boolean indicating success/failure and connection time
    """

    connection_status = False
    conn_attempt_duration = -1
    scan_attempt_duration = -1
    nrScannedNetworks = 1
    rssi = -121
    channel = -1

    wl = network.WLAN(network.STA_IF)
    wl.active(True)

    try:
        if not force_no_scan:
            logging.debug("Scanning for known wifi nets")
            start_time = utime.ticks_ms()
            available_nets = wl.scan()
            nrScannedNetworks = len(available_nets)
            scan_attempt_duration = utime.ticks_ms() - start_time
            nets = frozenset([e.ssid for e in available_nets])
            known_nets_names = frozenset([key for key in known_nets])
            net_to_use = list(nets & known_nets_names)

            if(len(net_to_use) == 0):
                logging.debug("No known network found in range. Aborting.")
                return (connection_status, conn_attempt_duration, scan_attempt_duration, channel, rssi)

            net_to_use = net_to_use[0]
            net_properties = known_nets[net_to_use]
            pwd = net_properties['pwd']
            sec = [e.sec for e in available_nets if e.ssid == net_to_use][0]
            if 'wlan_config' in net_properties:
                wl.ifconfig(config=net_properties['wlan_config'])
        else:
            # pick one
            net_to_use = list(frozenset([key for key in known_nets]))[0]
            sec = 3
            pwd = known_nets[net_to_use]['pwd']
            logging.debug(net_to_use, sec, pwd)
        # connect
        start_time = utime.ticks_ms()
        connect_timeout = start_time + max_connection_attempt_time_sec * 1000
        wl.connect(net_to_use, pwd)
        while not wl.isconnected() and utime.ticks_ms() < connect_timeout:
            utime.sleep_ms(10)
        conn_attempt_duration = utime.ticks_ms() - start_time

        if wl.isconnected():
            logging.debug("Connected to " + net_to_use + " with IP address:" + wl.ifconfig()[0])
            connection_status = True

            # update_time_ntp()

            # obtain some extra KPIs from joined AP
            channel = -1
            rssi = -1
        else:
            logging.debug("Not connected to {}".format(net_to_use))
    except Exception as e:
        logging.exception(e, "Exception during wifi connect:")
        # uncomment the following lines for fallback mode enabling
        """
        print("Failed to connect to any known network, going into AP mode")
        wl.init(mode=WLAN.AP, ssid=original_ssid, auth=original_auth, channel=6, antenna=WLAN.INT_ANT)
        """

    return (connection_status, conn_attempt_duration, scan_attempt_duration, channel, rssi)

def getSignalQuality():
    pass

def is_connected():
    return network.WLAN(network.STA_IF).isconnected()

def deactivate():
    """ Actions implemented when turning off wifi, before deep sleep """

    deactivation_status = False
    start_time_deactivation = utime.ticks_ms()

    try:
        wl = network.WLAN(network.STA_IF)
        wl.disconnect()
        wl.active(False)
    except:
        logging.debug('WiFi disconnecting ignored.')

    return (deactivation_status, utime.ticks_ms() - start_time_deactivation)


def update_time_ntp():
    # adjust time
    rtc = machine.RTC()
    rtc.ntp_sync("pool.ntp.org")
    utime.sleep_ms(3000)
    logging.debug('\nRTC Set from NTP to UTC:', rtc.now())
