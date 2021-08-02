import struct
import utime
import device_info
import logging
from . import lora_custom_encoding
from networking import lora
from external.kpn_senml.senml_unit import SenmlSecondaryUnits


def connect(cfg):
    # network connectivity & transmission
    logging.info("Joining network...")
    (joinOk, join_duration) = lora.join(cfg, lora.set_keys(cfg))
    results = {}
    results["status"] = {"value": joinOk}

    # if network statistics are enabled
    if cfg._MEAS_NETWORK_STAT_ENABLE:
        results["lora_join_duration"] = {"unit": SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND, "value": join_duration}

    return results


def disconnect():
    pass


def create_message_cbor(device_id, measurements):
    from external.kpn_senml.senml_pack_cbor import SenmlPackCbor
    from external.kpn_senml.senml_record import SenmlRecord
    from external.kpn_senml.senml_unit import SenmlUnits
    from external.kpn_senml.senml_unit import SenmlSecondaryUnits
    print("Device ID in readable form: {}".format(device_id))
    (_DEVICE_ID, _LORA_MAC) = device_info.get_device_id()

    message = SenmlPackCbor(_LORA_MAC)

    for key in measurements:
        if "unit" in measurements[key]:
            message.add(SenmlRecord(key, unit=measurements[key]["unit"], value=measurements[key]["value"]))
        else:
            message.add(SenmlRecord(key, value=measurements[key]["value"]))

    return message.to_cbor()


def create_message(device_id, measurements):
    return lora_custom_encoding.create_message(device_id, measurements)


def send_message(cfg, message):
    logging.info("Sending byte packet of {} bytes length".format(len(message)))
    lora.send(cfg, message)


def checkAndApplyOTA(cfg):
    pass
