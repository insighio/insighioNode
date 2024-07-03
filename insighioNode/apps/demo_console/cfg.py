import logging
import ujson
import utils

is_config_valid = False
is_temp_config = False
user_settings = {}
device_settings = {}
protocol_config_instance = None

_SETTINGS_FIELD = '_settings_field'

_tmp_config_file_path = "/apps/tmp_config.json"
_user_config_file_path = "/apps/user_config.json"
_device_config_file_path = "/apps/device_config.json"

################################################
# load json files

def init():
    global is_config_valid
    global is_temp_config
    global user_settings
    global device_settings
    global protocol_config_instance

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

# board # hw-module
# protocol #
# shield-sensor
# shield-radio

################################################
# auxilary functions

_tmp_obj = None
_tmp_field = None
_tmp_subobj = None

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

def has(key, category=None):
    global _tmp_obj
    global _tmp_field
    global _tmp_subobj

    if category is None:
        return _has(user_settings, key)
    else:
        _tmp_obj = None
        _tmp_field = None
        if _has(device_settings, category):
            _tmp_obj = _get(device_settings, category)
            _tmp_field = _get(user_settings, _get(_tmp_obj, '_settings_field'))
            _tmp_subobj = _get(_tmp_obj, _tmp_field)
            return _has(_tmp_subobj, key):
    return False

def get(key, category=None):
    global _tmp_obj
    global _tmp_field
    global _tmp_subobj

    if category is None:
        return _get(user_settings, key)
    else:
        _tmp_obj = None
        _tmp_field = None
        if _has(device_settings, category):
            _tmp_obj = _get(device_settings, category)
            _tmp_field = _get(user_settings, _get(_tmp_obj, '_settings_field'))
            _tmp_subobj = _get(_tmp_obj, _tmp_field)
            return _get(_tmp_subobj, key):
    return None


def set(key, value):
    global user_settings
    user_settings[key] = value
    return True


def get_protocol_config():
    global protocol_config_instance

    if protocol_config_instance is not None:
        return protocol_config_instance

    protocol = get("protocol")
    ipversion = get("ipversion")

    if protocol == "coap":
        from protocols import coap_client
        from protocols import coap_config

        protocol_config_instance = coap_config.CoAPConfig()

    elif protocol == "mqtt":
        from protocols import mqtt_client
        from protocols import mqtt_config

        protocol_config_instance = mqtt_config.MQTTConfig()

    protocol_config_instance.server_port = get("server-port", "protocol")
    protocol_config_instance.use_custom_socket = False

    if ipversion == "IPV6":
        protocol_config_instance.server_ip = get("server-ipv6", "protocol")
    else:
        protocol_config_instance.server_ip = get("server-ipv4", "protocol")


def is_temp():
    return is_temp_config
