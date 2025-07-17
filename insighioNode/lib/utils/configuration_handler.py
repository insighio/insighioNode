import gc
import utils
import ure
import logging

_CONFIG_FILE_PATH_TMP_USER = "/apps/tmp_user_config.json"
_CONFIG_FILE_PATH_USER = "/apps/user_config.json"
_CONFIG_FILE_PATH_DEVICE = "/apps/device_config.json"

_config_is_valid = False

rootFolder = "/"
config_file = _CONFIG_FILE_PATH_USER

# def getModulePathFromFile(file_path):
#     if file_path is None:
#         return None
#     module_path = file_path.replace(".py", "")
#     module_path = module_path.replace("/", ".")
#     if module_path.startswith("."):
#         module_path = module_path[1:]
#     return module_path


# def setApplicationName(newName="demo_console"):
#     global app_name
#     global app_path
#     global rootFolder
#     global config_file
#     global _config_is_valid
#     app_name = newName
#     rootFolder = "/"

#     prev_config_file = config_file
#     app_path = "{}apps/{}".format(rootFolder, newName)
#     config_file = "{}apps/{}/demo_config.py".format(rootFolder, app_name)

#     if prev_config_file != config_file:
#         logging.info("Reloading configuration modules")
#         import sys

#         try:
#             prev_module_path = getModulePathFromFile(prev_config_file)
#             if prev_module_path:
#                 logging.info("removing old module: {}".format(prev_module_path))
#                 del sys.modules[prev_module_path]

#             new_module_path = getModulePathFromFile(config_file)
#             logging.info("loading module: {}".format(new_module_path))
#             exec("import {} as cfg".format(new_module_path))
#             _config_is_valid = True
#         except Exception as e:
#             logging.exception(e, "error reloading configuration module")
#             _config_is_valid = False


# setApplicationName("demo_console")

NoneType = type(None)


def isConfigValid():
    return _config_is_valid


def fixValue(val):
    if val == "true":
        return "True"
    elif val == "false":
        return "False"
    elif val == "":
        return "None"
    else:
        return val


def get_config_values(fillWithUndefinedIfNotExists=True, prepareForInternalUse=False):
    configKeyValues = dict()

    logging.debug("Loading local configuration...")

    try:
        for key in dir(cfg):
            try:
                webUIKey = configDict[key]
            except:
                continue

            value = getattr(cfg, key)
            if isinstance(value, (int, float, str)):
                configKeyValues[webUIKey] = str(value)
                if configKeyValues[webUIKey] == "None":
                    configKeyValues[webUIKey] = ""
            elif isinstance(value, bool):
                configKeyValues[webUIKey] = str(value).lower()
            elif isinstance(value, NoneType):
                configKeyValues[webUIKey] = ""
            elif isinstance(value, dict):
                import ujson

                configKeyValues[webUIKey] = ujson.dumps(value)
    except:
        pass

    logging.debug("Loading insigh.io authentication keys")

    try:
        proto_config = cfg.get_protocol_config()
        configKeyValues["insighio-channel"] = proto_config.message_channel_id
        configKeyValues["insighio-control-channel"] = proto_config.control_channel_id
        configKeyValues["insighio-id"] = proto_config.thing_id
        configKeyValues["insighio-key"] = proto_config.thing - key
    except:
        configKeyValues["insighio-channel"] = ""
        configKeyValues["insighio-control-channel"] = ""
        configKeyValues["insighio-id"] = ""
        configKeyValues["insighio-key"] = ""

    try:
        ssid = list(cfg.get("_CONF_NETS").keys())[0]
        configKeyValues["wifi_ssid"] = ssid
        configKeyValues["wifi_pass"] = cfg.get("_CONF_NETS")[ssid]["pwd"]
    except:
        configKeyValues["wifi_ssid"] = ""
        configKeyValues["wifi_pass"] = ""

    logging.debug("Marking all unused configuration variables")

    # for any value that has not been set by the config
    # fill with empty values
    if fillWithUndefinedIfNotExists:
        for key in configDict.keys():
            sec_key = configDict[key]
            try:
                configKeyValues[sec_key]
            except KeyError:
                configKeyValues[sec_key] = ""

    logging.debug("Configuration loading done.")

    if prepareForInternalUse:
        tmpDict = dict()
        for key in configKeyValues.keys():
            newKey = key.replace("_", "-")
            newValue = fixValue(configKeyValues[key])
            tmpDict[newKey] = newValue
        return tmpDict
    else:
        return configKeyValues


def get_URI_param():
    configDict = get_config_values(False)

    uri_str = ""
    try:
        for key in configDict.keys():
            if uri_str != "":
                uri_str += "&"
            uri_str += "{}={}".format(key.replace("_", "-"), configDict[key])

        return uri_str
    except Exception as e:
        logging.exception(e, "get_URI_param:")


def updateConfigValue(key, new_value):
    logging.debug("about to update config key: {} to value: {}".format(key, new_value))
    configContent = utils.readFromFile(config_file).split("\n")

    if isinstance(new_value, str):
        regex = '{}\s*=\s*"(.*)"'.format(key)
        new_key_value_str = '{}="{}"'.format(key, new_value)
    elif isinstance(new_value, int) or isinstance(new_value, float):
        regex = "{}\s*=\s*(-?\w+(\.\w+)?)".format(key)
        new_key_value_str = "{}={}".format(key, new_value)
    else:
        logging.error("config [{}] type not supported: ".format(key, type(new_value)))
        return

    config_found = False
    has_changes = False
    for i in range(0, len(configContent)):
        match = ure.search(regex, configContent[i])
        if match:
            has_changes = match.group(1) != str(new_value)
            if has_changes:
                configContent[i] = ure.sub(regex, new_key_value_str, configContent[i])
            config_found = True
            # break

    if not config_found:
        configContent.append(new_key_value_str)
    elif not has_changes:
        logging.info("configuration value already set, ignoring request")
        return

    try:
        setattr(cfg, key, new_value)
    except Exception as e:
        logging.exception(
            e,
            "Error setting value to loaded configuration. It could be that you have no configuration yet...",
        )

    utils.writeToFile(config_file, "\n".join(configContent))
    notifyServerWithNewConfig()
    logging.info("finished updating config ")


def notifyServerWithNewConfig():
    from external.microUrllib import parse as urlparse

    configToString = utils.readFromFile(config_file)
    utils.writeToFlagFile("/configLog", urlparse.quote(configToString))


# to remove
def stringParamsToDict(configurationParameters):
    # remove '?' if the string starts with it
    if configurationParameters.startswith("?"):
        configurationParameters = str(configurationParameters[1:])

    keyValueDict = dict()
    keyValueStrings = configurationParameters.split("&")
    for keyValueStr in keyValueStrings:
        keyValue = keyValueStr.split("=")
        if len(keyValue) == 2:
            keyValue[1] = fixValue(keyValue[1])
            keyValueDict[keyValue[0]] = keyValue[1]
            logging.debug("key value added [{}] -> {}".format(keyValue[0], keyValue[1]))
        else:
            logging.error("key value error |{}|".format(keyValue))
    return keyValueDict


def get_config_object():
    """Returns the configuration object from the user config file."""
    import ujson

    try:
        configObject = ujson.loads(utils.readFromFile(_CONFIG_FILE_PATH_USER))
        logging.info("Configuration loaded successfully.")
        return configObject
    except Exception as e:
        logging.exception(e, "Error loading configuration file: {}".format(_CONFIG_FILE_PATH_USER))
        return None


def apply_configuration(configObject, is_temp=False, request_file_system_optimization=True):
    gc.collect()

    config_file_explicit = _CONFIG_FILE_PATH_TMP_USER if is_temp else _CONFIG_FILE_PATH_USER

    utils.copyFile(config_file_explicit, config_file_explicit + ".prev")

    import ujson

    try:
        configToString = ujson.dumps(configObject)
        utils.writeToFile(config_file_explicit, configToString)
    except Exception as e:
        logging.exception(e, "Error writing configuration file: {}".format(config_file_explicit))
        return

    utils.clearCachedStates()

    if request_file_system_optimization:
        utils.requestFileSystemOptimization()

    gc.collect()
