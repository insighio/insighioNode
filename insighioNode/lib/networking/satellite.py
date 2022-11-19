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
cellular_model = CELLULAR_NO_INIT

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
        from external.astronode import astronode
        modem_instance = astronode.ASTRONODE(pin_modem_tx, pin_modem_rx)
        if not _initialize(modem_instance):
            modem_instance = None
    else:
        logging.debug("modem_instance is not None")

    return modem_instance

def _initialize(modem):
    if modem is None:
        logging.info("No modem detected")
        return False

    if not modem.is_alive():
        logging.info("Modem is unresponsive")
        return False

    modem.print_status()
    modem.set_default_configuration()
    return True

def is_alive():
    modem = get_modem_instance()
    if modem is None:
        logging.info("No modem detected")
        return False

    return modem.is_alive():

def send(cfg, byte_msg):
    modem = get_modem_instance()

    if modem is None:
        logging.info("No modem detected, ignoring send request")
        return

    # status = modem.enqueue_payload(ubinascii.hexlify(byte_msg).upper().decode('utf-8'))
    # return status()
    return modem.send_payload(byte_msg)