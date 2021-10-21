import device_info
import machine
import socket
import utime
import ubinascii
import logging


def set_keys(cfg):
    try:
        # get app_eui and app_key in right formats
        if cfg._APP_EUI and cfg._APP_KEY:
            dev_eui = ubinascii.unhexlify(cfg._DEV_EUI)
            app_key = ubinascii.unhexlify(cfg._APP_KEY)
            app_eui = ubinascii.unhexlify(cfg._APP_EUI)
            return(dev_eui, app_eui, app_key)
        elif cfg._APP_EUIs and cfg._APP_KEYs:
            lora_mac_addresses = device_info.get_lora_mac()
            curr_dev = lora_mac_addresses[0]
            i = cfg._DEV_EUIs.index(curr_dev)
            # get app_eui and app_key in right formats
            dev_eui = device_info.get_lora_mac()[1]
            app_eui = ubinascii.unhexlify(cfg._APP_EUIs[i])
            app_key = ubinascii.unhexlify(cfg._APP_KEYs[i])
            return(dev_eui, app_eui, app_key)
    except Exception as e:
        logging.exception(e, "Invalid lora keys: {}, {}, {}".format(cfg._DEV_EUI, cfg._APP_EUI, cfg._APP_KEY))

    return(None, None, None)


def join(cfg, lora_keys):
    """ Join network using a tuple of (dev_eui,app_eui,app_key) """
    conn_attempt_duration = -1
    from network import LoRa

    # default values
    config_region = cfg._LORA_REGION if cfg._LORA_REGION is not None else LoRa.EU868
    config_adr = cfg._LORA_ADR if cfg._LORA_ADR is not None else False
    config_tx_retries = cfg._LORA_TX_RETRIES if cfg._LORA_TX_RETRIES is not None else 1

    # initialize lorawan "interface"
    lora = LoRa(mode=LoRa.LORAWAN, region=config_region, adr=config_adr, public=True, tx_retries=config_tx_retries, device_class=LoRa.CLASS_A)

    # If we came up from POWERON//WDT_RESET then explicitly JOIN else if we came up from DEEPSLEEP then check NVRAM for stored keys"""
    if device_info.get_reset_cause() == 0 or device_info.get_reset_cause() == 2:
        # clear NVRAM if something is in
        lora.nvram_erase()
        logging.debug("Erased LoRa status from NVRAM")
    else:
        # restore status if any
        lora.nvram_restore()
        logging.debug("Restored LoRa status from NVRAM")

    # join network
    start_time = utime.ticks_ms()
    if not lora.has_joined():
        # set the 3 default channels to the same frequency (must be before sending the OTAA join request)
        config_dr = cfg._LORA_DR if cfg._LORA_DR is not None else 5
        try:
            lora.join(activation=LoRa.OTAA, auth=(lora_keys[0], lora_keys[1], lora_keys[2]), timeout=0, dr=config_dr)

            join_timeout = start_time + cfg._MAX_CONNECTION_ATTEMPT_TIME_SEC * 1000
            # wait until the module has joined the network
            while not lora.has_joined() and utime.ticks_ms() < join_timeout:
                utime.sleep_ms(10)
                # print('Not yet joined...')
        except Exception as e:
            logging.exception(e, "exception during LoRA join")

    conn_attempt_duration = utime.ticks_ms() - start_time
    if lora.has_joined():
        logging.debug('Lora has joined the network sucessfully in {} sec'.format(conn_attempt_duration))
        # save status for potential deep sleep
        lora.nvram_save()
        return (True, conn_attempt_duration)
    else:
        logging.debug("Not joined (timeout = {} expired)".format(conn_attempt_duration))
        return (False, conn_attempt_duration)


def send(cfg, byte_msg):
    """ Send lora packet """
    from network import LoRa
    try:
        # create socket and set socket parameters
        s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
        s.setsockopt(socket.SOL_LORA, socket.SO_DR, cfg._LORA_DR)
        s.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, cfg._LORA_CONFIRMED)
        try:
            timeout = cfg._LORA_SOCKET_TIMEOUT
        except AttributeError:
            timeout = 30  # default value if the timeout is not defined in configuration
        logging.debug('LoRa send blocking for {} sec'.format(timeout))
        s.settimeout(timeout)

        # send packet
        s.send(byte_msg)
        logging.debug('Success in LoRa transmission')

        # if we expect something from DL #### deactivated for now
        # try:
        #     listenForDL = cfg._LISTEN_DL_MSG
        #     if listenForDL:
        #         try:
        #             bufsize = cfg._LORA_SOCKET_BUFFER_SIZE
        #         except AttributeError:
        #             bufsize = 128  # default value if the buffer size is not defined in configuration
        #
        #         # try to receive anything
        #         logging.debug('Try to receive {} secs'.format(timeout))
        #         try:
        #             received = s.recv(bufsize)
        #             logging.debug('Received:{}'.format(received))
        #             if received == b'\x01\x02\x03':
        #                 logging.debug('Command 1 received')
        #             elif received == b'\x03\x02\x01':
        #                 logging.debug('Command 2 received')
        #             else:
        #                 logging.debug('No identified command received')
        #         except Exception as e:
        #             logging.exception(e, 'Timeout in receiving')
        #     else:
        #         logging.debug("DL messages option configured to false")
        # except AttributeError:
        #     logging.exception(e, "DL messages option wasn't configured")

        # release socket and end
        logging.debug('Ending lora send')
        utime.sleep_ms(500)
        s.close()

    except Exception as e:
        logging.exception(e, "Exception in lora packet send")
        s.close()
