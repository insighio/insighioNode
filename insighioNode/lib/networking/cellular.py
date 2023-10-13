import sys
import device_info
import utime
import logging

import gc

CELLULAR_NO_INIT = None
CELLULAR_NO      = 0
CELLULAR_SEQUANS = 1
CELLULAR_MC60    = 2
CELLULAR_BG600   = 3
CELLULAR_UNKNOWN = 4

CELLULAR_MC60_STR  = 'mc60'
CELLULAR_BG600_STR = 'bg600'

# Modem state
MODEM_DETTACHED = -1  # initial value, nothing happened
MODEM_ACTIVATED = 0
MODEM_ATTACHED = 1
MODEM_CONNECTED = 2

cellular_model = CELLULAR_NO_INIT
modem_instance = None

pin_modem_tx = None
pin_modem_rx = None
pin_modem_power_on = None
pin_modem_power_key = None


def set_pins(power_on=None, power_key=None, modem_tx=None, modem_rx=None, gps_tx=None, gps_rx=None):
    global pin_modem_tx
    global pin_modem_rx
    global pin_modem_power_on
    global pin_modem_power_key
    pin_modem_tx = modem_tx
    pin_modem_rx = modem_rx
    pin_modem_power_on = power_on
    pin_modem_power_key = power_key


def detect_modem():
    global cellular_model
    from networking.modem.modem_base import Modem
    modemInst = Modem(pin_modem_power_on, pin_modem_power_key, pin_modem_tx, pin_modem_rx)
    if not modemInst.is_alive():
        modemInst.power_on()
    model_name = modemInst.get_model()
    # logging.debug("modem name returned: " + model_name)
    # if modem is still not responding, try power off/on
    if not model_name:
        modemInst.power_off()
        utime.sleep_ms(1000)
        modemInst.power_on()
        model_name = modemInst.get_model()

    if not model_name:
        cellular_model = CELLULAR_NO
    elif CELLULAR_MC60_STR in model_name:
        cellular_model = CELLULAR_MC60
    elif CELLULAR_BG600_STR in model_name:
        cellular_model = CELLULAR_BG600
    else:
        cellular_model = CELLULAR_UNKNOWN

    logging.debug("selected modem: " + str(cellular_model))
    return cellular_model


def get_modem_instance():
    global modem_instance
    logging.debug("getting modem instance...")
    if modem_instance is None:
        modem_id = cellular_model
        if modem_id == CELLULAR_NO_INIT:
            modem_id = detect_modem()

        if modem_id == CELLULAR_MC60 or modem_id == CELLULAR_BG600 or modem_id == CELLULAR_UNKNOWN:
            if modem_id == CELLULAR_MC60:
                from networking.modem.modem_mc60 import ModemMC60
                modem_instance = ModemMC60(pin_modem_power_on, pin_modem_power_key, pin_modem_tx, pin_modem_rx)
            elif modem_id == CELLULAR_BG600:
                from networking.modem.modem_bg600 import ModemBG600
                modem_instance = ModemBG600(pin_modem_power_on, pin_modem_power_key, pin_modem_tx, pin_modem_rx)
            else:
                from networking.modem.modem_base import Modem
                modem_instance = Modem(pin_modem_power_on, pin_modem_power_key, pin_modem_tx, pin_modem_rx)  # generic
        elif modem_id == CELLULAR_SEQUANS:
            from networking.modem.modem_sequans import ModemSequans
            modem_instance = ModemSequans()
    else:
        logging.debug("modem_instance is not None")

    return modem_instance


def connect(cfg):
    """ Complete cellular connection procedure (activation, attachment, data connection)
            Returns:
                status: "Modem state" see enums NBIOT_*.
                a list of time duration consumed for (activation,attachment,connection)
    """
    status = MODEM_DETTACHED
    activation_duration = -1
    attachment_duration = -1
    connection_duration = -1
    rssi = None
    rsrp = None
    rsrq = None

    try:
        logging.debug('Initializing modem')
        modemInst = get_modem_instance()
        modemInst.init(cfg._IP_VERSION, cfg._APN, cfg._CELLULAR_TECHNOLOGY)

        # force modem activation and query status
        # comment by ag: noticed that in many cases the modem is initially set to mode 4
        start_activation_duration = utime.ticks_ms()
        if modemInst.wait_for_registration(120000):
            # print("Modem activated (AT+CFUN=1), continuing...")
            # logging.debug("Deattaching (precautionary)")
            # modemInst.attach(False)
            # utime.sleep_ms(1000)

            status = MODEM_ACTIVATED
            activation_duration = utime.ticks_ms() - start_activation_duration
            # proceed with attachment
            start_attachment_duration = utime.ticks_ms()
            attachment_timeout = start_attachment_duration + cfg._MAX_ATTACHMENT_ATTEMPT_TIME_SEC * 1000

            modemInst.get_registered_mcc_mnc()

            if not modemInst.is_attached():
                logging.debug('Attaching...')
                modemInst.attach()
                # lte.attach(band=int(cfg._BAND), apn=cfg._APN, legacyattach=False)
                while not modemInst.is_attached() and (utime.ticks_ms() < attachment_timeout):
                    utime.sleep_ms(10)

            update_rtc_from_network_time(modemInst)

            if modemInst.is_attached():
                status = MODEM_ATTACHED
                attachment_duration = utime.ticks_ms() - start_attachment_duration
                logging.debug('Modem attached')

                # signal quality
                rssi = modemInst.get_rssi()
                (rsrp, rsrq) = modemInst.get_extended_signal_quality()
                modemInst.get_lac_n_cell_id()

                logging.debug('Signal Quality - RSSI/RSRP/RSRQ: {}, {}, {}'.format(rssi, rsrp, rsrq))

                # ready to connect
                if modemInst.has_data_over_ppp():
                    logging.debug('Entering Data State. Modem connecting...')
                    start_connection_duration = utime.ticks_ms()
                    connection_timeout = start_connection_duration + cfg._MAX_CONNECTION_ATTEMPT_TIME_SEC * 1000
                    if not modemInst.is_connected():
                        modemInst.connect()

                    if modemInst.is_connected():
                        modemInst.force_time_update()
                        update_rtc_from_network_time(modemInst)
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

    return (status, activation_duration, attachment_duration, connection_duration)


def update_rtc_from_network_time(modem):
    try:
        from machine import RTC
        time_tuple = modem.get_network_date_time()

        rtc = RTC()

        # (year, month, day, day of week, hour, minute, seconds, usec)
        if time_tuple is None or (time_tuple and time_tuple[0] < 2021 or time_tuple[0] > 2050):
            # wrong time set, try to get time from other source
            now = rtc.datetime()
            set_gps_date = modem.gps_timestamp is not None and len(modem.gps_timestamp) == 8 and (modem.gps_timestamp[0] != 0 or modem.gps_timestamp[1] != 0 or modem.gps_timestamp[2] != 0)
            set_gps_time = modem.gps_timestamp is not None and len(modem.gps_timestamp) == 8 and (modem.gps_timestamp[4] != 0 or modem.gps_timestamp[5] != 0 or modem.gps_timestamp[6] != 0)
            time_tuple = (
                modem.gps_timestamp[0] if set_gps_date else now[0],
                modem.gps_timestamp[1] if set_gps_date else now[1],
                modem.gps_timestamp[2] if set_gps_date else now[2],
                0,
                modem.gps_timestamp[4] if set_gps_time else now[4],
                modem.gps_timestamp[5] if set_gps_time else now[5],
                int(modem.gps_timestamp[6]) if set_gps_time else now[6],
                0
            )

            if modem.gps_timestamp is None and modem.gps_date is None:
                logging.error("time not set to RTC...check if NTP can solve it...")
                time_tuple = None

        if time_tuple is not None:
            logging.debug("Setting cellular RTC with: " + str(time_tuple))

            rtc.datetime(time_tuple)
            logging.debug("New RTC: " + str(rtc.datetime()))
    except Exception as e:
        logging.exception(e, "RTC init failed")


def deactivate():
    """ Actions implemented when turning off lte modem, before deep sleep """

    modemInst = get_modem_instance()
    deactivation_status = False
    start_time_deactivation = utime.ticks_ms()

    try:
        if modemInst:
            logging.debug('Modem disconnecting...')
            modemInst.disconnect()
            logging.debug('Modem deinitializing...')
            modemInst.power_off()
            modemInst.wait_for_modem_power_off()
        # LTE().send_at_cmd('AT+CFUN=0')
        deactivation_status = True
    except Exception as e:
        logging.exception(e, "Error in deactivation")

    return (deactivation_status, utime.ticks_ms() - start_time_deactivation)
