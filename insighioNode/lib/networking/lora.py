import device_info
import machine
import socket
import utime
import ubinascii
import logging

modem_instance = None
pin_modem_tx = None
pin_modem_rx = None
pin_modem_power_on = None
i2c_gps_address = None


def set_pins(power_on=None, modem_tx=None, modem_rx=None, gps_address=None):
    global pin_modem_tx
    global pin_modem_rx
    global pin_modem_power_on
    global i2c_gps_address
    pin_modem_tx = modem_tx
    pin_modem_rx = modem_rx
    pin_modem_power_on = power_on
    i2c_gps_address = gps_address

def set_keys(cfg):
    try:
        # get app_eui and app_key in right formats
        if cfg._APP_EUI and cfg._APP_KEY:
            dev_eui = cfg._DEV_EUI
            app_key = cfg._APP_KEY
            app_eui = cfg._APP_EUI
            return(dev_eui, app_eui, app_key)
    except Exception as e:
        logging.exception(e, "Invalid lora keys: {}, {}, {}".format(cfg._DEV_EUI, cfg._APP_EUI, cfg._APP_KEY))

    return(None, None, None)


def get_modem_instance():
    global modem_instance
    logging.debug("getting lora modem instance...")
    if modem_instance is None:
        from networking.modem import modem_rak4270
        modem_instance = modem_rak4270.ModemRak4270(pin_modem_power_on, pin_modem_tx, pin_modem_rx)
        modem_instance.power_on()
    else:
        logging.debug("modem_instance is not None")

    return modem_instance


def join(cfg, lora_keys):
    """ Join network using a tuple of (dev_eui,app_eui,app_key) """
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
    modem.set_app_eui(lora_keys[1])
    modem.set_app_key(lora_keys[2])

    # # If we came up from POWERON//WDT_RESET then explicitly JOIN else if we came up from DEEPSLEEP then check NVRAM for stored keys"""
    # if device_info.get_reset_cause() == 0 or device_info.get_reset_cause() == 2:
    #     # clear NVRAM if something is in
    #     lora.nvram_erase()
    #     logging.debug("Erased LoRa status from NVRAM")
    # else:
    #     # restore status if any
    #     lora.nvram_restore()
    #     logging.debug("Restored LoRa status from NVRAM")

    # join network
    start_time = utime.ticks_ms()
    join_status = modem.join()
    return (join_status, utime.ticks_ms() - start_time)
    #     # set the 3 default channels to the same frequency (must be before sending the OTAA join request)
    #     config_dr = cfg._LORA_DR if cfg._LORA_DR is not None else 5
    #     try:
    #         lora.join(activation=LoRa.OTAA, auth=(lora_keys[0], lora_keys[1], lora_keys[2]), timeout=0, dr=config_dr)
    #
    #         join_timeout = start_time + cfg._MAX_CONNECTION_ATTEMPT_TIME_SEC * 1000
    #         # wait until the module has joined the network
    #         while not lora.has_joined() and utime.ticks_ms() < join_timeout:
    #             utime.sleep_ms(10)
    #             # print('Not yet joined...')
    #     except Exception as e:
    #         logging.exception(e, "exception during LoRA join")
    #
    # conn_attempt_duration = utime.ticks_ms() - start_time
    # if lora.has_joined():
    #     logging.debug('Lora has joined the network sucessfully in {} sec'.format(conn_attempt_duration))
    #     # save status for potential deep sleep
    #     lora.nvram_save()
    #     return (True, conn_attempt_duration)
    # else:
    #     logging.debug("Not joined (timeout = {} expired)".format(conn_attempt_duration))
    #     return (False, conn_attempt_duration)

def is_connected():
    modem = get_modem_instance()

    if modem is None:
        logging.info("No modem detected")
        return False
    return modem.is_connected()

def send(cfg, byte_msg):
    """ Send lora packet """
    modem = get_modem_instance()

    if modem is None:
        logging.info("No modem detected, ignoring send request")

    status = modem.send(ubinascii.hexlify(byte_msg).lower().decode('utf-8'))
    return status

def deinit():
    global modem_instance
    modem = get_modem_instance()

    if modem is None:
        logging.info("No modem detected, ignoring deinit request")
    modem.power_off()
    modem_instance = None
