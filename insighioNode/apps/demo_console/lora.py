import device_info
import logging
from . import lora_custom_encoding
from networking import lora
from external.kpn_senml.senml_unit import SenmlSecondaryUnits


def init(cfg):
    lora.set_pins(None, cfg.get("_UC_UART_MODEM_TX"), cfg.get("_UC_UART_MODEM_RX"), cfg.get("_UC_LORA_RESET"))
    is_connected = lora.is_connected()
    logging.info("Lora is connected: {}".format(is_connected))


def deinit():
    pass


def updateSignalQuality(cfg, measurements):
    if not cfg.get("meas-network-stat"):
        return
    pass


def update_hw_ids(measurements, is_senml=True, is_json=False):
    pass


def connect(cfg):
    # network connectivity & transmission
    logging.info("Joining network...")
    (joinOk, join_duration) = lora.join(cfg, lora.set_keys(cfg))
    results = {}
    results["status"] = {"value": joinOk}

    # if network statistics are enabled
    if cfg.get("meas-network-stat"):
        results["lora_join_duration"] = {"unit": SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND, "value": join_duration}

    return results


def is_connected():
    return lora.is_connected()


def disconnect():
    logging.info("about to power off modem")
    lora.deinit()


## commented out the cbor to keep it in source code and omit it to deployments
# def create_message_cbor(device_id, measurements):
#     from external.kpn_senml.senml_pack_cbor import SenmlPackCbor
#     from external.kpn_senml.senml_record import SenmlRecord
#     from external.kpn_senml.senml_unit import SenmlUnits
#     from external.kpn_senml.senml_unit import SenmlSecondaryUnits
#
#     print("Device ID in readable form: {}".format(device_id))
#     (_DEVICE_ID, _LORA_MAC) = device_info.get_device_id()
#
#     message = SenmlPackCbor(_LORA_MAC)
#
#     for key in measurements:
#         if "unit" in measurements[key]:
#             message.add(SenmlRecord(key, unit=measurements[key]["unit"], value=measurements[key]["value"]))
#         else:
#             message.add(SenmlRecord(key, value=measurements[key]["value"]))
#
#     return message.to_cbor()


def create_message(device_id, measurements):
    return lora_custom_encoding.create_message(device_id, measurements)


def send_message(cfg, message, explicit_channel_name=None):
    logging.info("Sending byte packet of {} bytes length".format(len(message)))
    return lora.send(cfg, message)


def send_control_message(cfg, message, subtopic):
    logging.error("Config message not yet supported for LoRA")


def check_and_apply_ota(cfg):
    logging.error("OTA not yet supported for LoRA")
    pass
