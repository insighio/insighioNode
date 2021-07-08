from networking import cellular
from external.kpn_senml.senml_pack_json import SenmlPackJson
from external.kpn_senml.senml_record import SenmlRecord
from external.kpn_senml.senml_unit import SenmlUnits
from external.kpn_senml.senml_unit import SenmlSecondaryUnits
import logging
import device_info


# network connection
def connect(cfg):
    logging.info("Connecting to cellular...")
    enableDataState = (cfg._IP_VERSION == "IP")
    results = {}

    if device_info.is_esp32():
        cellular.set_pins(cfg._UC_IO_RADIO_ON, cfg._UC_IO_PWRKEY, cfg._UC_UART_MODEM_TX, cfg._UC_UART_MODEM_RX)

    modem_instance = cellular.get_modem_instance()
    logging.debug("demo_console: cellular connect modem instance is None: " + str(modem_instance is None))
    if modem_instance is not None:
        (status, activation_duration, attachment_duration, connection_duration, rssi, rsrp, rsrq) = cellular.connect(cfg, dataStateOn=enableDataState)
        results["status"] = {"value": (status == cellular.MODEM_CONNECTED)}

        # if network statistics are enabled
        if cfg._MEAS_NETWORK_STAT_ENABLE:
            results["cell_act_duration"] = {"unit": SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND, "value": activation_duration}
            results["cell_att_duration"] = {"unit": SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND, "value": attachment_duration}
            results["cell_rssi"] = {"unit": SenmlSecondaryUnits.SENML_SEC_UNIT_DECIBEL_MILLIWATT, "value": rssi}
            results["cell_rsrp"] = {"unit": SenmlSecondaryUnits.SENML_SEC_UNIT_DECIBEL_MILLIWATT, "value": rsrp}
            results["cell_rsrq"] = {"unit": SenmlSecondaryUnits.SENML_SEC_UNIT_DECIBEL_MILLIWATT, "value": rsrq}
            if not cfg.protocol_config.use_custom_socket:
                results["cell_con_duration"] = {"unit": SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND, "value": connection_duration}

    return results


def create_message(device_id, measurements):
    message = SenmlPackJson(device_id + '-')

    for key in measurements:
        if "unit" in measurements[key]:
            message.add(SenmlRecord(key, unit=measurements[key]["unit"], value=measurements[key]["value"]))
        else:
            message.add(SenmlRecord(key, value=measurements[key]["value"]))

    return message.to_json()


def send_message(cfg, message):
    from . import transfer_protocol
    transfer_protocol.send_packet(cfg, message)


def disconnect():
    logging.info("Deactivate NB-IOT: {}".format(cellular.deactivate()))
