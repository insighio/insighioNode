from utime import ticks_ms, sleep_ms, ticks_diff
import ubinascii
import logging

modem_instance = None
pin_modem_tx = None
pin_modem_rx = None
pin_modem_power_on = None
pin_modem_reset = None


def set_pins(power_on=None, modem_tx=None, modem_rx=None, modem_reset=None):
    global pin_modem_tx
    global pin_modem_rx
    global pin_modem_power_on
    global i2c_gps_address
    pin_modem_tx = modem_tx
    pin_modem_rx = modem_rx
    pin_modem_power_on = power_on
    pin_modem_reset = modem_reset


def set_keys(cfg):
    try:
        # get app_eui and app_key in right formats
        if cfg._APP_EUI and cfg._APP_KEY:
            dev_eui = cfg._DEV_EUI
            app_key = cfg._APP_KEY
            app_eui = cfg._APP_EUI
            return (dev_eui, app_eui, app_key)
    except Exception as e:
        logging.exception(e, "Invalid lora keys: {}, {}, {}".format(cfg._DEV_EUI, cfg._APP_EUI, cfg._APP_KEY))

    return (None, None, None)


def get_modem_instance():
    global modem_instance
    logging.debug("getting lora modem instance...")
    if modem_instance is None:
        from networking.modem import modem_rak3172

        modem_instance = modem_rak3172.ModemRak3172(pin_modem_reset, pin_modem_tx, pin_modem_rx)
        if not modem_instance.is_alive():
            modem_instance.reset()
            sleep_ms(1000)

        modem_instance.init()

        logging.debug("modem rak3172 is alive: ".format(modem_instance.is_alive()))
    else:
        logging.debug("modem_instance is not None")

    return modem_instance


def join(cfg, lora_keys):
    """Join network using a tuple of (dev_eui,app_eui,app_key)"""
    modem = get_modem_instance()

    if modem is None:
        logging.info("No modem detected, ignoring join request")
        return (False, -1)

    modem.set_region(cfg._LORA_REGION if cfg._LORA_REGION is not None else "EU868")
    modem.set_dr(cfg._LORA_DR if cfg._LORA_DR is not None else 5)
    modem.set_confirm(cfg._LORA_CONFIRMED if cfg._LORA_CONFIRMED is not None else 0)
    modem.set_adr(cfg._LORA_ADR if cfg._LORA_ADR is not None else 0)
    modem.set_retries(cfg._LORA_TX_RETRIES if cfg._LORA_TX_RETRIES is not None else 0)

    modem.set_dev_eui(lora_keys[0])

    if lora_keys[1] and lora_keys[1] != "None":
        modem.set_app_eui(lora_keys[1])
    else:
        _DEFAULT_APP_EUI = "0000000000000001"
        modem.set_app_eui(_DEFAULT_APP_EUI)
    modem.set_app_key(lora_keys[2])

    # join network
    start_time = ticks_ms()

    if not modem.is_connected():
        join_status = modem.join()

    return (modem.is_connected(), ticks_diff(ticks_ms(), start_time))


def is_connected():
    modem = get_modem_instance()

    if modem is None:
        logging.info("No modem detected")
        return False
    return modem.is_connected()


def send(cfg, byte_msg):
    """Send lora packet"""
    modem = get_modem_instance()

    if modem is None:
        logging.info("No modem detected, ignoring send request")

    status = modem.send(ubinascii.hexlify(byte_msg).lower().decode("utf-8"))
    return status


def deinit():
    global modem_instance
    modem = get_modem_instance()

    if modem is None:
        logging.info("No modem detected, ignoring deinit request")
    modem_instance = None
