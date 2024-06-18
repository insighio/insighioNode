import logging
import ujson
import utils

is_config_valid = False
is_temp_config = False
user_settings = {}
device_settings = {}

_tmp_config_file_path = "/apps/tmp_config.json"
_user_config_file_path = "/apps/user_config.json"
_device_config_file_path = "/apps/device_config.json"

################################################
# load json files
try:
    if utlis.existsFile(_tmp_config_file_path):
        user_settings = ujson.loads(utils.readFromFile(_tmp_config_file_path))
        is_temp_config = True
        is_config_valid = True
        logging.info("[cfg] loaded config: [temp]")
except Exception as e:
    pass

if not is_temp_config:
    try:
        if utils.existsFile(_user_config_file_path):
            user_settings = ujson.loads(utils.readFromFile(_user_config_file_path))
            logging.info("[cfg] loaded config: [normal]")
            is_config_valid = True
    except Exception as e:
        pass

if not is_config_valid:
    user_settings = {}
    logging.info("[cfg] loaded config: [fallback]")

try:
    device_settings = ujson.loads(utils.readFromFile("/apps/device_config.json"))
    logging.info("[cfg] loaded device config")
except Exception as e:
    logging.exception(e, "Unable to retrieve old configuration")

################################################
# auxilary functions

def has(key):
    return hasattr(_cfg, key)


def get(key, category="user"):
    return getattr(_cfg, key) if hasattr(_cfg, key) else None


def set(key, value):
    setattr(_cfg, key, value)
    return True


def get_protocol_config():
    pass
    # protocol_config_instance = None
    #
    #
    # def get_protocol_config():
    #     global protocol_config_instance
    #     if protocol_config_instance is not None:
    #         return protocol_config_instance
    #
    #     if protocol == "coap":
    #         from protocols import coap_client
    #         from protocols import coap_config
    #
    #         protocol_config = coap_config.CoAPConfig()
    #         protocol_config.server_port = 5683
    #         protocol_config.use_custom_socket = ipversion == "IPV6"
    #     elif protocol == "mqtt":
    #         from protocols import mqtt_client
    #         from protocols import mqtt_config
    #
    #         protocol_config = mqtt_config.MQTTConfig()
    #         protocol_config.server_port = 1884  # only for mqtt
    #         protocol_config.use_custom_socket = False
    #     else:
    #         print("Not supported transport protocol. Choose between CoAP and MQTT")
    #         return None
    #
    #     if ipversion == "IPV6":
    #         protocol_config.server_ip = "2001:41d0:701:1100:0:0:0:2060"
    #     else:
    #         protocol_config.server_ip = "console.insigh.io"
    #
    #     """ console.insigh.io security keys """
    #     protocol_config.message_channel_id = "<insighio-channel>"
    #     protocol_config.control_channel_id = "<insighio-control-channel>"
    #     protocol_config.thing_id = "<insighio-id>"
    #     protocol_config.thing_token = "<insighio-key>"
    #     protocol_config_instance = protocol_config
    #     return protocol_config


def get_cfg_module():
    return _cfg

def is_temp():
    return is_temp_config
