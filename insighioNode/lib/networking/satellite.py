import device_info
import machine
import socket
import utime
import ubinascii
import logging

SATELLITE_NO_INIT   = None
SATELLITE_NO        = 0
SATELLITE_ASTRONODE = 1
SATELLITE_UNKNOWN = 2

SATELLITE_ASTRONODE_STR  = 'AST50108'
satellite_model = SATELLITE_NO_INIT

modem_instance = None
pin_modem_tx = None
pin_modem_rx = None
i2c_gps_address = None


def set_pins(modem_tx=None, modem_rx=None, gps_address=None):
    global pin_modem_tx
    global pin_modem_rx
    global i2c_gps_address
    pin_modem_tx = modem_tx
    pin_modem_rx = modem_rx
    i2c_gps_address = gps_address

def get_modem_instance():
    global modem_instance
    logging.debug("getting satellite modem instance...")
    if modem_instance is None:
        from networking.modem_satellite import modem_astronode
        modem_instance = modem_astronode.ModemAstronode(pin_modem_tx, pin_modem_rx)
        modem_instance.modem_instance.enableDebugging()
        if not _initialize(modem_instance):
            modem_instance = None
    else:
        logging.debug("modem_instance is not None")

    return modem_instance

def update_rtc_from_network_time(modem):
    try:
        from machine import RTC
        (status, timeEpoch2018) = modem.get_network_date_time()

        logging.info("satellite RTC: status {}, epoch{}".format(status, timeEpoch2018))

        time_tuple = None
        if status:
            rtc = RTC()

            # 1514764800 -> 2018/01/01 00:00:00 # astronode base time
            #  946684800 -> 2000/01/01 00:00:00 # esp32 base time
            time_tuple = utime.gmtime(timeEpoch2018 - 946684800)
            time_tuple = (
                time_tuple[0],
                time_tuple[1],
                time_tuple[2],
                0,
                time_tuple[3],
                time_tuple[4],
                time_tuple[5],
                0
            )

        if time_tuple is not None:
            logging.debug("Setting satellite RTC with: " + str(time_tuple))

            rtc.datetime(time_tuple)
            logging.debug("New RTC: " + str(rtc.datetime()))
    except Exception as e:
        logging.exception(e, "RTC init failed")

def _initialize(modem):
    if modem is None:
        logging.info("No modem detected")
        return False

    modem_is_alive = False
    for x in range(3):
        modem_is_alive = modem.is_alive()
        if modem_is_alive:
            break
        utime.sleep_ms(500)
    if not modem_is_alive:
        logging.info("Modem is unresponsive")
        return False

    modem.print_status()
    modem.set_default_configuration()

    update_rtc_from_network_time(modem)

    return True

def is_alive():
    modem = get_modem_instance()
    if modem is None:
        logging.info("No modem detected")
        return False

    return modem.is_alive()

def send(cfg, byte_msg):
    modem = get_modem_instance()

    if modem is None:
        logging.info("No modem detected, ignoring send request")
        return False

    return modem.send_payload(byte_msg)
