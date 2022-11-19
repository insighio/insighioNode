import struct
import utime
import device_info
import logging
from apps.demo_console import lora_custom_encoding
from networking import satellite
from external.kpn_senml.senml_unit import SenmlSecondaryUnits

def init(cfg):
    satellite.set_pins(cfg._UC_UART_MODEM_TX, cfg._UC_UART_MODEM_RX)
    is_alive = satellite.is_alive()
    logging.info("satellite modem is alive: {}".format(is_alive))

def updateSignalQuality(cfg, measurements):
    pass

def connect(cfg):
    return True

def is_connected():
    return True

# def create_message_cbor(device_id, measurements):
#     from external.kpn_senml.senml_pack_cbor import SenmlPackCbor
#     from external.kpn_senml.senml_record import SenmlRecord
#     from external.kpn_senml.senml_unit import SenmlUnits
#     from external.kpn_senml.senml_unit import SenmlSecondaryUnits
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

def send_message(cfg, message):
    logging.info("Sending byte packet of {} bytes length".format(len(message)))
    satellite.send(cfg, message)

def send_control_message(cfg, message, subtopic):
    logging.error("Config message not yet supported for satellite")

def check_and_apply_ota(cfg):
    logging.error("OTA not yet supported for satellite")
    pass