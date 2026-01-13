import logging
from networking import wifi
from external.kpn_senml.senml_pack_json import SenmlPackJson
from external.kpn_senml.senml_record import SenmlRecord
from external.kpn_senml.senml_unit import SenmlSecondaryUnits
import _thread

transfer_client = None
mutex = _thread.allocate_lock()


def init(cfg):
    pass


def deinit():
    logging.info("Deactivating WiFi...")
    wifi.deactivate()


def updateSignalQuality(cfg, measurements):
    if not cfg.get("_MEAS_NETWORK_STAT_ENABLE"):
        return
    pass


def update_hw_ids(measurements, is_senml=True, is_json=False):
    pass


def connect(cfg, explicit_protocol=None):
    with mutex:
        (connOk, connDur, scanDur, wifiChannel, wifiRssi) = wifi.connect(
            cfg.get("_CONF_NETS"), cfg.get("_MAX_CONNECTION_ATTEMPT_TIME_SEC"), force_no_scan=True
        )
        results = {}
        results["status"] = {"value": connOk}
        # if network statistics are enabled
        if cfg.get("_MEAS_NETWORK_STAT_ENABLE"):
            results["wifi_conn_duration"] = {"unit": SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND, "value": connDur}
            results["wifi_channel"] = {"value": wifiChannel}
            results["wifi_rssi"] = {"unit": SenmlSecondaryUnits.SENML_SEC_UNIT_DECIBEL_MILLIWATT, "value": wifiRssi}

        if connOk:
            requested_protocol = explicit_protocol if explicit_protocol is not None else cfg.get("protocol")
            logging.debug(
                "Protocol: config: {}, explicit: {}, selected: {}".format(cfg.get("protocol"), explicit_protocol, requested_protocol)
            )

            from . import transfer_protocol

            global transfer_client
            if requested_protocol == "mqtt":
                transfer_client = transfer_protocol.TransferProtocolMQTT(cfg)
                transfer_client.protocol_config.client_name = "{}_wifi_mqtt".format(cfg.get("device_id"))
                transferClientStatus = transfer_client.connect()
                results["status"]["value"] = results["status"]["value"] and transferClientStatus
            elif requested_protocol == "coap":
                transfer_client = transfer_protocol.TransferProtocolCoAP(cfg)
                transfer_client.protocol_config.client_name = "{}_wifi_coap".format(cfg.get("device_id"))
                transferClientStatus = transfer_client.connect()
                results["status"]["value"] = results["status"]["value"] and transferClientStatus
            else:
                transfer_client = None

        return results


def is_connected():
    with mutex:
        return wifi and transfer_client and transfer_client.is_connected() and wifi.is_connected()


def disconnect():
    global transfer_client
    with mutex:
        if transfer_client is not None:
            transfer_client.disconnect()
            transfer_client = None


def create_message(device_id, measurements):
    message = SenmlPackJson((device_id + "-") if device_id is not None else None)

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


def send_message(cfg, message, explicit_channel_name=None):
    with mutex:
        if transfer_client is not None:
            return transfer_client.send_packet(message, explicit_channel_name)
    return None


def send_control_message(cfg, message, subtopic):
    with mutex:
        if transfer_client is not None:
            return transfer_client.send_control_packet(message, subtopic)
    return None


def send_config_message(cfg, message):
    if transfer_client is not None:
        return send_control_message(
            cfg,
            '[{"n":"config","vs":"' + message + '"}]',
            "/configResponse",
        )
    return None


def check_and_apply_ota(cfg):
    with mutex:
        if transfer_client is not None:
            from . import ota

            ota.checkAndApply(transfer_client)
