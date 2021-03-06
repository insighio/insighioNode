import device_info
import logging
from networking import wifi
from external.kpn_senml.senml_pack_json import SenmlPackJson
from external.kpn_senml.senml_record import SenmlRecord
from external.kpn_senml.senml_unit import SenmlUnits
from external.kpn_senml.senml_unit import SenmlSecondaryUnits

transfer_client = None

def init(cfg):
    pass

def updateSignalQuality(cfg, measurements):
    if not cfg._MEAS_NETWORK_STAT_ENABLE:
        return
    pass

def connect(cfg):
    (connOk, connDur, scanDur, wifiChannel, wifiRssi) = wifi.connect(cfg._CONF_NETS, cfg._MAX_CONNECTION_ATTEMPT_TIME_SEC, force_no_scan=True)
    results = {}
    results["status"] = {"value": connOk}
    # if network statistics are enabled
    if cfg._MEAS_NETWORK_STAT_ENABLE:
        results["wifi_conn_duration"] = {"unit": SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND, "value": connDur}
        results["wifi_scan_duration"] = {"unit": SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND, "value": scanDur}
        results["wifi_channel"] = {"value": wifiChannel}
        results["wifi_rssi"] = {"unit": SenmlSecondaryUnits.SENML_SEC_UNIT_DECIBEL_MILLIWATT, "value": wifiRssi}

    if device_info.is_esp32():
        import ntptime
        from machine import RTC
        logging.info("time before sync: " + str(RTC().datetime()))
        ntptime.host = "pool.ntp.org"
        cnt = 0
        max_tries = 10
        while cnt < max_tries:
            try:
                ntptime.settime()
                logging.info("time set")
                break
            except:
                logging.info("time failed")
                pass
            cnt += 1
        logging.info("time after sync: " + str(RTC().datetime()))
    else:
        import utime
        uptimeBeforeNtp = utime.ticks_ms()
        wifi.update_time_ntp()
        timeDiff = utime.ticks_ms() - uptimeBeforeNtp
        results["timeDiffAfterNTP"] = timeDiff

    if connOk:
        from . import transfer_protocol
        global transfer_client
        if cfg.protocol == 'coap':
            transfer_client = transfer_protocol.TransferProtocolCoAP(cfg)
        elif cfg.protocol == 'mqtt':
            transfer_client = transfer_protocol.TransferProtocolMQTT(cfg)
        else:
            transfer_client = None
        transfer_client.connect()

    return results


def is_connected():
    return wifi and transfer_client and transfer_client.is_connected() and wifi.is_connected()


def disconnect():
    global transfer_client
    if transfer_client is not None:
        transfer_client.disconnect()
        transfer_client = None

    logging.info("Deactivating WiFi: {}".format(wifi.deactivate()))


def create_message(device_id, measurements):
    message = SenmlPackJson((device_id + '-') if device_id is not None else None)

    if "dt" in measurements:
        message.base_time = measurements["dt"]["value"]

    for key in measurements:
        if isinstance(measurements[key], dict):
            if "unit" in measurements[key]:
                message.add(SenmlRecord(key, unit=measurements[key]["unit"], value=measurements[key]["value"]))
            elif key != "dt":
                message.add(SenmlRecord(key, value=measurements[key]["value"]))
        elif measurements[key] is not None:
            message.add(SenmlRecord(key, value=measurements[key]))

    return message.to_json()


def send_message(cfg, message):
    if transfer_client is not None:
        return transfer_client.send_packet(message)
    return None


def send_control_message(cfg, message, subtopic):
    if transfer_client is not None:
        return transfer_client.send_control_packet(message, subtopic)
    return None

def check_and_apply_ota(cfg):
    if transfer_client is not None:
        from . import ota
        ota.checkAndApply(transfer_client)
