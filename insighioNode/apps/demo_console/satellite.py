import logging
from . import lora_custom_encoding
from networking import satellite


def init(cfg):
    satellite.set_pins(cfg.get("_UC_UART_MODEM_TX"), cfg.get("_UC_UART_MODEM_RX"))
    is_alive = satellite.is_alive()
    logging.info("satellite modem is alive: {}".format(is_alive))

    if cfg.get("_SATELLITE_ASTROCAST_DEVKIT_EN"):
        ssid = cfg.get("_SATELLITE_ASTROCAST_DEVKIT_SSID")
        password = cfg.get("_SATELLITE_ASTROCAST_DEVKIT_PASS")
        token = cfg.get("_SATELLITE_ASTROCAST_DEVKIT_TOKEN")
        logging.info("Setting DevKit wifi credentials and access token")
        res = satellite.get_modem_instance().modem_instance.wifi_configuration_write(ssid, password, token)
        logging.info("WiFi configuration setup result: {}".format(res))
        # satellite.get_modem_instance().modem_instance.configuration_save()


def deinit():
    pass


def updateSignalQuality(cfg, measurements):
    pass

def update_hw_ids(measurements, is_senml=True, is_json=False):
    pass


def connect(cfg):
    return True


def is_connected():
    return True


def disconnect():
    pass


# def create_message_cbor(device_id, measurements):
#     import struct
#     import utime
#     import device_info
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


def send_message(cfg, message, explicit_channel_name=None):
    logging.info("Sending byte packet of {} bytes length".format(len(message)))
    return satellite.send(cfg, message)


def send_control_message(cfg, message, subtopic):
    logging.error("Config message not yet supported for satellite")


def check_and_apply_ota(cfg):
    logging.error("OTA not yet supported for satellite")
    pass
