import logging
import ujson
import utils

from dictionary_utils import _get, _has

is_config_valid = False
is_temp_config = False
user_settings = {}
device_settings = {}
config_instance = None

_CONFIG_FILE_PATH_TMP_USER = "/apps/tmp_user_config.json"
_CONFIG_FILE_PATH_USER = "/apps/user_config.json"
_CONFIG_FILE_PATH_DEVICE = "/apps/device_config.json"

################################################
# load json files


def init():
    global is_config_valid
    global is_temp_config
    global user_settings
    global device_settings
    global config_instance

    is_config_valid = False
    is_temp_config = False
    user_settings = {}
    device_settings = {}
    config_instance = None

    try:
        if utils.existsFile(_CONFIG_FILE_PATH_TMP_USER):
            user_settings = ujson.loads(utils.readFromFile(_CONFIG_FILE_PATH_TMP_USER))
            is_temp_config = True
            is_config_valid = True
            logging.info("[cfg] loaded config: [temp]")
    except Exception as e:
        pass

    if not is_temp_config:
        try:
            if utils.existsFile(_CONFIG_FILE_PATH_USER):
                user_settings = ujson.loads(utils.readFromFile(_CONFIG_FILE_PATH_USER))
                logging.info("[cfg] loaded config: [normal]")
                is_config_valid = True
        except Exception as e:
            pass

    if not is_config_valid:
        user_settings = {}
        logging.info("[cfg] loaded config: [fallback]")
        return False

    try:
        device_settings = ujson.loads(utils.readFromFile(_CONFIG_FILE_PATH_DEVICE))
        logging.info("[cfg] loaded device config")
        is_config_valid = True
    except Exception as e:
        logging.exception(e, "Unable to retrieve old configuration")
        is_config_valid = False

    if is_config_valid:

        config_instance = Config(user_settings, device_settings)
        logging.info("[cfg] config instance created")
        return True
    return False


def is_temp_config():
    # global is_temp_config
    return is_temp_config


def get_config():
    global config_instance
    if config_instance is None:
        init()
    return config_instance


################################################
# auxiliary functions


class Config:
    def __init__(self, user_settings, device_settings):
        self.user_settings = user_settings
        self.device_settings = device_settings
        self.protocol_config_instance = None
        self.category_setup = {"board": "esp32s3", "protocol": "mqtt", "shield-sensor": "", "radio": ""}
        self.protocol_config_instance = None

    def __str__(self):
        return ujson.dumps(self.__dict__, indent=4, ensure_ascii=False)

    def set_category_setup(self, category, value):
        if category in self.category_setup:
            self.category_setup[category] = value
        else:
            logging.warning(f"Category '{category}' not recognized in category setup.")

    def has(self, key, category=None):
        if category is None:
            return _has(self.user_settings, key)
        else:
            return (
                _has(self.category_setup, category) and _has(self.device_settings, category) and _has(self.device_settings[category], key)
            )

    def get(self, key, category=None):
        if category is None:
            return _get(user_settings, key)
        elif self.has(key, category):
            return _get(self.device_settings[category], key)
        else:
            return None

    def set(self, key, value):
        global user_settings
        user_settings[key] = value
        return True

    def get_protocol_config(self):
        if self.protocol_config_instance is not None:
            return self.protocol_config_instance

        protocol = self.get("protocol")
        ipversion = self.get("ipversion")

        if protocol == "coap":
            from protocols import coap_config

            self.protocol_config_instance = coap_config.CoAPConfig()
        elif protocol == "mqtt":
            from protocols import mqtt_config

            self.protocol_config_instance = mqtt_config.MQTTConfig()

        self.protocol_config_instance.server_port = self.get("server-port", "protocol")
        self.protocol_config_instance.use_custom_socket = False

        if ipversion == "IPV6":
            self.protocol_config_instance.server_ip = self.get("server-ipv6", "protocol")
        else:
            self.protocol_config_instance.server_ip = self.get("server-ipv4", "protocol")
