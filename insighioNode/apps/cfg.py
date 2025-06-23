import logging
import ujson
import utils

# from .dictionary_utils import _get, _has

from utils.configuration_handler import _CONFIG_FILE_PATH_USER, _CONFIG_FILE_PATH_DEVICE, _CONFIG_FILE_PATH_TMP_USER
from device_info import get_device_id

is_config_valid = False
is_temp_config = False
user_settings = {}
device_settings = {}
config_instance = None


################################################
# load json files


def _has(obj, key):
    if not obj or not key:
        return False
    try:
        return key in obj
    except:
        return False


def _get(obj, key):
    if not obj or not key:
        return None
    try:
        return obj[key]
    except:
        return None


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
            user_settings["device-id"] = get_device_id()[0]
            is_temp_config = True
            is_config_valid = True
            logging.info("[cfg] loaded config: [temp]")
    except Exception as e:
        pass

    if not is_temp_config:
        try:
            if utils.existsFile(_CONFIG_FILE_PATH_USER):
                user_settings = ujson.loads(utils.readFromFile(_CONFIG_FILE_PATH_USER))
                user_settings["device-id"] = get_device_id()[0]
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
        import device_info

        config_instance = Config(user_settings, device_settings)
        config_instance.set_category_setup("board", device_info.get_hw_module_version())
        config_instance.set_category_setup("protocol", user_settings.get("protocol"))
        config_instance.set_category_setup("shield-sensor", user_settings.get("selected-shield"))
        config_instance.set_category_setup("network", user_settings.get("network"))
        config_instance.initialize()
        logging.info("[cfg] config instance created")
        return True
    return False


def is_valid():
    return is_config_valid


def is_temp():
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
        self.category_setup = {"board": "esp32s3", "protocol": "mqtt", "shield-sensor": "", "network": "wifi"}
        self.protocol_config_instance = None
        self.config = {}

    def __str__(self):
        return ujson.dumps(self.__dict__, indent=4, ensure_ascii=False)

    def set_category_setup(self, category, value):
        if category in self.category_setup:
            self.category_setup[category] = value
            logging.debug("setting cfg category [{}] -> {}".format(category, value))
        else:
            logging.error(f"Category '{category}' not recognized in category setup.")

    def initialize(self):
        self.config.update(self.user_settings)
        self.config.update(self.device_settings["common"])

        for category_key in self.category_setup:
            if category_key in self.device_settings:
                subcategory = self.category_setup[category_key]
                if subcategory in self.device_settings[category_key]:
                    self.config.update(self.device_settings[category_key][subcategory])

    def has(self, key):
        return _has(self.config, key)

    def get(self, key):
        return _get(self.config, key)

    def set(self, key, value):
        global user_settings
        self.config[key] = value
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

        self.protocol_config_instance.server_port = self.get("server-port")
        self.protocol_config_instance.use_custom_socket = False

        if ipversion == "IPV6":
            self.protocol_config_instance.server_ip = self.get("server-ipv6")
        else:
            self.protocol_config_instance.server_ip = self.get("server-ipv4")

        self.protocol_config_instance.thing_id = self.get("insighio-id")
        self.protocol_config_instance.thing_token = self.get("insighio-key")
        self.protocol_config_instance.message_channel_id = self.get("insighio-channel")
        self.protocol_config_instance.control_channel_id = self.get("insighio-control-channel")

        return self.protocol_config_instance


# Auxiliary functions
def has(key):
    global config_instance
    if config_instance is None:
        logging.error("Configuration instance is not initialized.")
        return False
    return config_instance.has(key)


def get(key):
    global config_instance
    if config_instance is None:
        logging.error("Configuration instance is not initialized.")
        return None
    return config_instance.get(key)


def set(key, value):
    global config_instance
    if config_instance is None:
        logging.error("Configuration instance is not initialized.")
        return False
    return config_instance.set(key, value)


def get_protocol_config():
    global config_instance
    if config_instance is None:
        logging.error("Configuration instance is not initialized.")
        return None
    return config_instance.get_protocol_config()
