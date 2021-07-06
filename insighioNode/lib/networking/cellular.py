import sys
import device_info

CELLULAR_NO_INIT = None
CELLULAR_NO      = 0
CELLULAR_SEQUANS = 1
CELLULAR_MC60    = 2
CELLULAR_BG600   = 3
CELLULAR_UNKNOWN = 4

CELLULAR_MC60_STR  = "mc60"
CELLULAR_BG600_STR = "bg600"

# Modem state
MODEM_DETTACHED = -1  # initial value, nothing happened
MODEM_ACTIVATED = 0
MODEM_ATTACHED = 1
MODEM_CONNECTED = 2

cellular_model = CELLULAR_NO
modem_instance = None


def get_modem_id():
    global cellular_model
    return cellular_model


def detect_modem(cfg):
    global cellular_model
    if sys.platform == 'esp32':
        from networking.modem.modem_base import Modem
        uart1 = UART(1)
        uart1.init(115200, bits=8, parity=None, stop=1, tx=cfg.MODEM_PIN_TX, rx=cfg.MODEM_PIN_RX, timeout=500, timeout_char=1000)
        modemInst = Modem(uart1)
        model_name = modemInst.get_model()
        modemInst = None
        uart1 = None
        if not model_name:
            cellular_model = CELLULAR_NO
        elif CELLULAR_MC60_STR in model_name:
            cellular_model = CELLULAR_MC60
        elif CELLULAR_BG600_STR in model_name:
            cellular_model = CELLULAR_BG600
        else:
            cellular_model = CELLULAR_UNKNOWN
    else:
        try:
            import pycom
            cellular_model = CELLULAR_SEQUANS if sys.platform in device_info._LTE_COMPATIBLE_PLATFORMS else CELLULAR_NO
        except Exception as e:
            cellular_model = CELLULAR_NO
    return cellular_model


def get_modem_instance(cfg=None):
    global modem_instance
    if modem_instance is None and cfg is not None:
        modem_id = get_modem_id()
        if modem_id == CELLULAR_NO_INIT:
            modem_id = detect_modem(cfg)

        if modem_id == CELLULAR_MC60 or modem_id == CELLULAR_BG600 or modem_id == CELLULAR_UNKNOWN:
            uart1 = UART(1)
            uart1.init(115200, bits=8, parity=None, stop=1, tx=cfg.MODEM_PIN_TX, rx=cfg.MODEM_PIN_RX, timeout=500, timeout_char=1000)

            if modem_id == CELLULAR_MC60:
                from networking.modem.modem_mc60 import ModemMC60
                modem_instance = ModemMC60(uart1)
            elif modem_id == CELLULAR_BG600:
                from networking.modem.modem_bg600 import ModemBG600
                modem_instance = ModemBG600(uart1)
            else:
                from networking.modem.modem_base import Modem
                modem_instance = Modem(uart1)  # generic
        elif modem_id == CELLULAR_SEQUANS:
            from networking.modem.modem_sequans import ModemSequans
            modem_instance = ModemSequans()

    return modem_instance


def connect(cfg, dataStateOn=True):
    """ Complete cellular connection procedure (activation, attachment, data connection)
            Returns:
                status: "Modem state" see enums NBIOT_*.
                a list of time duration consumed for (activation,attachment,connection)
    """
    status = MODEM_DETTACHED
    activation_duration = -1
    attachment_duration = -1
    connection_duration = -1
    rssi = -141

    try:
        logging.debug('Initializing modem')
        modemInst = get_modem_instance(cfg)
        modemInst.init(cfg)

        # force modem activation and query status
        # comment by ag: noticed that in many cases the modem is initially set to mode 4
        start_activation_duration = utime.ticks_ms()
        if self.wait_for_registration():
            # print("Modem activated (AT+CFUN=1), continuing...")
            status = MODEM_ACTIVATED
            activation_duration = utime.ticks_ms() - start_activation_duration
            # proceed with attachment
            start_attachment_duration = utime.ticks_ms()
            attachment_timeout = start_attachment_duration + cfg._MAX_ATTACHMENT_ATTEMPT_TIME_SEC * 1000

            # start attachment
            logging.debug('Attaching...')
            # lte.attach(band=cfg._BAND, apn=cfg._APN, legacyattach=False)
            while not modemInst.is_attached() and (utime.ticks_ms() < attachment_timeout):
                utime.sleep_ms(10)

            if modemInst.is_attached():
                status = MODEM_ATTACHED
                attachment_duration = utime.ticks_ms() - start_attachment_duration
                logging.debug('Modem attached')

                # printout/gather some information before activating PDP
                # check registation status
                # reg_data = lte.send_at_cmd('AT+CEREG?').split('\r\n')[1].split(',')
                # logging.debug('Registration Status: {}, RAT type selected: {}'.format(reg_data[1], reg_data[-1]))
                # # get PDP context status
                # pdp_data = lte.send_at_cmd('AT+CGCONTRDP=1').split('\r\n')[1].split(',')
                # logging.debug('IP/Subnet: {}, Primary DNS: {}'.format(pdp_data[3], pdp_data[5]))
                # signal quality
                rssi = modemInst.get_rssi()
                # (rsrp, rsrq) = modemInst.get_extended_signal_quality()

                logging.debug('Signal Quality - RSSI/RSRP/RSRQ: {}, {}, {}'.format(rssi, rsrp, rsrq))

                # ready to connect
                if dataStateOn:
                    logging.debug('Entering Data State. Modem connecting...')
                    start_connection_duration = utime.ticks_ms()
                    connection_timeout = start_connection_duration + cfg._MAX_CONNECTION_ATTEMPT_TIME_SEC * 1000
                    modemInst.connect()
                    while not modemInst.is_connected() and utime.ticks_ms() < connection_timeout:
                        utime.sleep_ms(10)

                    if modemInst.is_connected():
                        status = MODEM_CONNECTED
                        connection_duration = utime.ticks_ms() - start_connection_duration
                        logging.debug('Modem connected')
                        device_info.set_led_color('yellow')
                else:
                    # when using AT commands we don't need to explicitly enter data mode
                    status = MODEM_CONNECTED
            else:
                logging.debug('Unable to attach in {} sec'.format(cfg._MAX_ATTACHMENT_ATTEMPT_TIME_SEC))
    except Exception as e:
        logging.exception(e, "Outer Exception: {}".format(e))

    return (status, activation_duration, attachment_duration, connection_duration, rssi, rsrp, rsrq)


def deactivate():
    """ Actions implemented when turning off lte modem, before deep sleep """

    modemInst = get_modem_instance()
    deactivation_status = False
    start_time_deactivation = utime.ticks_ms()

    try:
        logging.debug('Modem disconnecting...')
        modemInst.disconnect()

        logging.debug('Modem deinitializing...')
        modemInst.power_off()
        # LTE().send_at_cmd('AT+CFUN=0')
        deactivation_status = True
    except Exception as e:
        logging.exception(e, "Error in deactivation")

    return (deactivation_status, utime.ticks_ms() - start_time_deactivation)
