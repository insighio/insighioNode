from network import LTE
import machine
import utime
import device_info
import logging

# Modem state
NBIOT_DETTACHED = -1  # initial value, nothing happened
NBIOT_MODEM_ACTIVATED = 0
NBIOT_ATTACHED = 1
NBIOT_CONNECTED = 2


def connect(cfg, dataStateOn=True):
    """ Complete nb-iot connection procedure (activation, attachment, data connection)
            Returns:
                status: "Modem state" see enums NBIOT_*.
                a list of time duration consumed for (activation,attachment,connection)
    """
    status = NBIOT_DETTACHED
    activation_duration = -1
    attachment_duration = -1
    connection_duration = -1
    rssi = -141
    rsrp = -141
    rsrq = -40

    try:
        logging.debug('Initializing LTE')
        global lte
        lte = LTE()
        lte.init()

        # force modem activation and query status
        # comment by ag: noticed that in many cases the modem is initially set to mode 4
        lte.send_at_cmd("AT+CFUN=0")
        sendAtCommand("AT+CGDCONT=1,\"" + cfg._IP_VERSION + "\",\"" + cfg._APN + "\"")
        start_activation_duration = utime.ticks_ms()
        lte.send_at_cmd("AT+CFUN=1")
        response, status = sendAtCommand("AT+CFUN?")
        if response.startswith("+CFUN: 1"):
            # print("Modem activated (AT+CFUN=1), continuing...")
            status = NBIOT_MODEM_ACTIVATED
            activation_duration = utime.ticks_ms() - start_activation_duration
            # proceed with attachment
            start_attachment_duration = utime.ticks_ms()
            attachment_timeout = start_attachment_duration + cfg._MAX_ATTACHMENT_ATTEMPT_TIME_SEC * 1000

            # start attachment
            logging.debug('Attaching...')
            # lte.attach(band=int(cfg._BAND), apn=cfg._APN, legacyattach=False)
            while not lte.isattached() and (utime.ticks_ms() < attachment_timeout):
                utime.sleep_ms(10)

            if lte.isattached():
                status = NBIOT_ATTACHED
                attachment_duration = utime.ticks_ms() - start_attachment_duration
                logging.debug('Modem attached')

                # printout/gather some information before activating PDP
                # check registation status
                reg_data = lte.send_at_cmd('AT+CEREG?').split('\r\n')[1].split(',')
                logging.debug('Registration Status: {}, RAT type selected: {}'.format(reg_data[1], reg_data[-1]))
                # get PDP context status
                pdp_data = lte.send_at_cmd('AT+CGCONTRDP=1').split('\r\n')[1].split(',')
                logging.debug('IP/Subnet: {}, Primary DNS: {}'.format(pdp_data[3], pdp_data[5]))
                # signal quality
                rssi_tmp = int(lte.send_at_cmd('AT+CSQ').split('\r\n')[1].split(',')[0].split(' ')[-1])
                if(rssi_tmp >= 0 and rssi_tmp <= 31):
                    rssi = -113 + rssi_tmp * 2

                lte.send_at_cmd('AT+CESQ')
                cesq_data = lte.send_at_cmd('AT+CESQ').split('\r\n')[1].split(',')
                rsrq_tmp = int(cesq_data[-2])
                rsrp_tmp = int(cesq_data[-1])
                if(rsrq_tmp >= 0 and rsrq_tmp <= 34):
                    rsrq = -20 + rsrq_tmp * 0.5
                if(rsrp_tmp >= 0 and rsrp_tmp <= 97):
                    rsrp = -141 + rsrp_tmp

                logging.debug('Signal Quality - RSSI/RSRP/RSRQ: {}, {}, {}'.format(rssi, rsrp, rsrq))

                # ready to connect
                if dataStateOn:
                    logging.debug('Entering Data State. Modem connecting...')
                    start_connection_duration = utime.ticks_ms()
                    connection_timeout = start_connection_duration + cfg._MAX_CONNECTION_ATTEMPT_TIME_SEC * 1000
                    lte.connect()
                    while not lte.isconnected() and utime.ticks_ms() < connection_timeout:
                        utime.sleep_ms(10)

                    if lte.isconnected():
                        status = NBIOT_CONNECTED
                        connection_duration = utime.ticks_ms() - start_connection_duration
                        logging.debug('Modem connected')
                        device_info.set_led_color('yellow')
                else:
                    # when using AT commands we don't need to explicitly enter data mode
                    status = NBIOT_CONNECTED
            else:
                logging.debug('Unable to attach in {} sec'.format(cfg._MAX_ATTACHMENT_ATTEMPT_TIME_SEC))
    except Exception as e:
        logging.exception(e, "Outer Exception: {}".format(e))

    return (status, activation_duration, attachment_duration, connection_duration, rssi, rsrp, rsrq)


def sendATsocket(data, host, port):
    global lte
    import microATsocket as socket
    try:
        # create socket instance providing the instance of the LTE modem
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        sock.setModemInstance(lte)
        # set that the incoming/outgoing data are simple ASCII characters
        sock.setMessageFormat(sock.SOCKET_MESSAGE_FORMAT.SOCKET_MESSAGE_ASCII)
        # send data to specific IP
        logging.debug(sock.sendto(data, (host, port)))
        utime.sleep_ms(2000)
        # close socket
        sock.close()
    except Exception as e:
        logging.exception(e, "SendAT Socket Exception: ")


def deactivate():
    """ Actions implemented when turning off lte modem, before deep sleep """

    deactivation_status = False
    start_time_deactivation = utime.ticks_ms()

    try:
        logging.debug('Modem disconnecting...')
        LTE().disconnect()

        logging.debug('Modem deinitializing...')
        LTE().deinit(dettach=True, reset=True)
        # LTE().send_at_cmd('AT+CFUN=0')
        deactivation_status = True
    except Exception as e:
        logging.exception(e, "Error in deactivation")

    return (deactivation_status, utime.ticks_ms() - start_time_deactivation)


def sendAtCommand(command, max_tries=1):
    response = ""
    status = False

    for x in range(max_tries):
        logging.debug(command)
        response = lte.send_at_cmd(command).strip()
        logging.debug(response)
        status = (response.find("OK") != -1)
        if status:

            break
        elif max_tries > 1:
            utime.sleep_ms(500)

    return (response, status)
