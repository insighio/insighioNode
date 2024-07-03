import gc
import utils
import ure
import logging

_config_is_valid = False

app_name = None
app_path = None
rootFolder = None
config_file = None


def getModulePathFromFile(file_path):
    if file_path is None:
        return None
    module_path = file_path.replace(".py", "")
    module_path = module_path.replace("/", ".")
    if module_path.startswith("."):
        module_path = module_path[1:]
    return module_path


def setApplicationName(newName="demo_console"):
    global app_name
    global app_path
    global rootFolder
    global config_file
    global _config_is_valid
    app_name = newName
    rootFolder = "/"

    prev_config_file = config_file
    app_path = "{}apps/{}".format(rootFolder, newName)
    config_file = "{}apps/{}/demo_config.py".format(rootFolder, app_name)

    if prev_config_file != config_file:
        logging.info("Reloading configuration modules")
        import sys

        try:
            prev_module_path = getModulePathFromFile(prev_config_file)
            if prev_module_path:
                logging.info("removing old module: {}".format(prev_module_path))
                del sys.modules[prev_module_path]

            new_module_path = getModulePathFromFile(config_file)
            logging.info("loading module: {}".format(new_module_path))
            exec("import {} as cfg".format(new_module_path))
            _config_is_valid = True
        except Exception as e:
            logging.exception(e, "error reloading configuration module")
            _config_is_valid = False


setApplicationName("demo_console")

configDict = {
    "_APN": "cell_apn",
    "lora-app-eui": "lora_app_eui",
    "lora-app-key": "lora_app_key",
    "_BAND": "cell_band",
    "batch-upload-buffer-size": "batch_upload_buffer_size",
    "_BOARD_TYPE": "selected_board",
    "cell-tech": "cell_tech",
    "system-enable-ota": "system_enable_ota",
    "period": "period",
    "lora-dev-eui": "lora_dev_eui",
    "ipversion": "ipversion",
    "_LORA_ADR": "lora_adr",
    "_LORA_CONFIRMED": "lora_confirmed",
    "_LORA_DR": "lora_dr",
    "_LORA_REGION": "lora_region",
    "_LORA_TX_RETRIES": "lora_retries",
    "meas-sensor-a-d-p1": "meas_sensor_a_d_p1",
    "meas-sensor-a-d-p1_TRANSFORMATION": "meas_sensor_a_d_p1_t",
    "meas-sensor-a-d-p2": "meas_sensor_a_d_p2",
    "meas-sensor-a-d-p2_TRANSFORMATION": "meas_sensor_a_d_p2_t",
    "meas-sensor-a-d-p3": "meas_sensor_a_d_p3",
    "meas-sensor-a-d-p3_TRANSFORMATION": "meas_sensor_a_d_p3_t",
    "meas-battery-stat": "meas_battery_stat",
    "meas-board-sense": "meas_board_sense",
    "meas-board-stat": "meas_board_stat",
    "meas-gps-enabled": "meas_gps_enabled",
    "meas-gps-sat-num": "meas_gps_sat_num",
    "meas-gps-timeout": "meas_gps_timeout",
    "meas-i2c-1": "meas_i2c_1",
    "meas-i2c-2": "meas_i2c_2",
    "meas-keyvalue": "meas_keyvalue",
    "meas-name-mapping": "meas_name_mapping",
    "meas-name-ext-mapping": "meas_name_ext_mapping",
    "meas-network-stat": "meas_network_stat",
    "meas-scale-enabled": "meas_scale_enabled",
    "meas-temp-unit": "meas_temp_unit",
    "meas-led-enabled": "meas_led_enabled",
    "_SELECTED_SHIELD": "selected_shield",
    "scheduled-time-a": "scheduled_time_a",
    "scheduled-time-b": "scheduled_time_b",
    "meas-sdi-1_ADDRESS": "meas_sdi_1_address",
    "meas-sdi-1_ENABLED": "meas_sdi_1_enabled",
    "meas-sdi-1_LOCATION": "meas_sdi_1_loc",
    "meas-sdi-2_ADDRESS": "meas_sdi_2_address",
    "meas-sdi-2_ENABLED": "meas_sdi_2_enabled",
    "meas-sdi-2_LOCATION": "meas_sdi_2_loc",
    "meas-sdi-3_ADDRESS": "meas_sdi_3_address",
    "meas-sdi-3_ENABLED": "meas_sdi_3_enabled",
    "meas-sdi-3_LOCATION": "meas_sdi_3_loc",
    "meas-sdi-4_ADDRESS": "meas_sdi_4_address",
    "meas-sdi-4_ENABLED": "meas_sdi_4_enabled",
    "meas-sdi-4_LOCATION": "meas_sdi_4_loc",
    "meas-sdi-5_ADDRESS": "meas_sdi_5_address",
    "meas-sdi-5_ENABLED": "meas_sdi_5_enabled",
    "meas-sdi-5_LOCATION": "meas_sdi_5_loc",
    "meas-sdi-6_ADDRESS": "meas_sdi_6_address",
    "meas-sdi-6_ENABLED": "meas_sdi_6_enabled",
    "meas-sdi-6_LOCATION": "meas_sdi_6_loc",
    "meas-sdi-7_ADDRESS": "meas_sdi_7_address",
    "meas-sdi-7_ENABLED": "meas_sdi_7_enabled",
    "meas-sdi-7_LOCATION": "meas_sdi_7_loc",
    "meas-sdi-8_ADDRESS": "meas_sdi_8_address",
    "meas-sdi-8_ENABLED": "meas_sdi_8_enabled",
    "meas-sdi-8_LOCATION": "meas_sdi_8_loc",
    "meas-sdi-9_ADDRESS": "meas_sdi_9_address",
    "meas-sdi-9_ENABLED": "meas_sdi_9_enabled",
    "meas-sdi-9_LOCATION": "meas_sdi_9_loc",
    "meas-sdi-10_ADDRESS": "meas_sdi_10_address",
    "meas-sdi-10_ENABLED": "meas_sdi_10_enabled",
    "meas-sdi-10_LOCATION": "meas_sdi_10_loc",
    "meas-sdi-warmup-time": "meas_sdi_warmup_time",
    "meas-scale-offset": "meas_scale_offset",
    "meas-scale-scale": "meas_scale_scale",
    "protocol": "protocol",
    "network": "network",
    "always-on-connection": "always_on_connection",
    "force-always-on-connection": "force_always_on_connection",
    "always-on-period": "always_on_period",
    "meas-gps-no-fix-no-upload": "meas_gps_no_fix_no_upload",
    "store-meas-if-failed-conn": "store_meas_if_failed_conn",
    "meas-4-20-snsr-1_ENABLE": "meas_4_20_snsr_1_enable",
    "meas-4-20-snsr-1_FORMULA": "meas_4_20_snsr_1_formula",
    "meas-4-20-snsr-2_ENABLE": "meas_4_20_snsr_2_enable",
    "meas-4-20-snsr-2_FORMULA": "meas_4_20_snsr_2_formula",
    "sat-astro-devkit-en": "sat_astro_devkit_en",
    "sat-astro-devkit-ssid": "sat_astro_devkit_ssid",
    "sat-astro-devkit-pass": "sat_astro_devkit_pass",
    "sat-astro-devkit-token": "sat_astro_devkit_token",
    "meas-scale-monitoring-enabled": "meas_scale_monitoring_enabled",
    "meas-pcnt-1-enable": "meas_pcnt_1_enable",
    "_PCNT_1_COUNT_ON_RISING": "meas_pcnt_1_cnt_on_rising",
    "meas-pcnt-1-high-freq": "meas_pcnt_1_high_freq",
    "meas-pcnt-1-formula": "meas_pcnt_1_formula",
    "_WIFI_SSID": "wifi_ssid",
    "_WIFI_PASS": "wifi_pass",
    "_SELECTED_SHIELD": "selected_shield",
    "meas-gps-only-on-boot": "meas_gps_only_on_boot",
}

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
        configKeyValues["insighio_channel"] = proto_config.message_channel_id
        configKeyValues["insighio_control_channel"] = proto_config.control_channel_id
        configKeyValues["insighio_id"] = proto_config.thing_id
        configKeyValues["insighio_key"] = proto_config.thing_token
    except:
        configKeyValues["insighio_channel"] = ""
        configKeyValues["insighio_control_channel"] = ""
        configKeyValues["insighio_id"] = ""
        configKeyValues["insighio_key"] = ""

    try:
        ssid = list(cfg._CONF_NETS.keys())[0]
        configKeyValues["wifi_ssid"] = ssid
        configKeyValues["wifi_pass"] = cfg._CONF_NETS[ssid]["pwd"]
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
    newConfig = get_URI_param()
    utils.writeToFlagFile("/configLog", "new")


def get_file_config(fileName, keyValuePairs):
    gc.collect()
    logging.debug("Getting file config: {}".format(fileName))
    contents = utils.readFromFile(fileName)
    for param in keyValuePairs:
        contents = contents.replace("<" + param + ">", keyValuePairs[param])
    return ure.sub(r"\"?<[a-z\-0-9]+>\"?", "None", contents)


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


def apply_configuration(keyValuePairDictionary, config_file_explicit=config_file):
    gc.collect()

    utils.copyFile(config_file_explicit, config_file_explicit + ".prev")

    # fix naming of keys to use '-' instead of '_'
    # unfortunatelly it is technical burden from old implementations, to be fixed in future release
    for param in keyValuePairDictionary:
        val = keyValuePairDictionary[param]
        key = param
        if "_" in param:
            key = param.replace("_", "-")
            print("changing key [{}] to [{}]".format(param, key))
            del keyValuePairDictionary[param]

        keyValuePairDictionary[key] = fixValue(val)

    gc.collect()

    operation = ""
    import device_info

    board = device_info.get_hw_module_version()
    shield = ""
    for param in keyValuePairDictionary:
        if param == "network":
            operation = keyValuePairDictionary[param]
        elif param == "selected-shield":
            shield = keyValuePairDictionary[param]

    contents = get_file_config(app_path + "/templ/common_templ.py", keyValuePairDictionary)

    # set project configuration content
    if board == device_info._CONST_ESP32 or board == device_info._CONST_ESP32_WROOM:
        contents += get_file_config(app_path + "/templ/device_ins_esp32_templ.py", keyValuePairDictionary)
    elif board == device_info._CONST_ESP32S3:
        contents += get_file_config(app_path + "/templ/device_ins_esp32s3_templ.py", keyValuePairDictionary)
    else:
        print("[ERROR]: device not supported: {}".format(board))

    contents += get_file_config(app_path + "/templ/device_i2c_analog_config_templ.py", keyValuePairDictionary)
    if shield == "advind":
        contents += get_file_config(app_path + "/templ/shield_advind_templ.py", keyValuePairDictionary)
        contents += get_file_config(app_path + "/templ/device_advind_config_templ.py", keyValuePairDictionary)
    elif shield == "dig_analog":
        contents += get_file_config(app_path + "/templ/shield_i2c_dig_analog_templ.py", keyValuePairDictionary)
    elif shield == "scale":
        if board == device_info._CONST_ESP32 or board == device_info._CONST_ESP32_WROOM:
            contents += get_file_config(app_path + "/templ/shield_esp32_scale.py", keyValuePairDictionary)
        elif board == device_info._CONST_ESP32S3:
            contents += get_file_config(app_path + "/templ/shield_esp32s3_scale.py", keyValuePairDictionary)
        contents += get_file_config(app_path + "/templ/device_scale_config.py", keyValuePairDictionary)

    contents += "\n"

    if operation == "wifi":
        contents += "\n" + get_file_config(app_path + "/templ/wifi_config_templ.py", keyValuePairDictionary)
        contents += "\n" + get_file_config(app_path + "/templ/protocol_config_templ.py", keyValuePairDictionary)
    elif operation == "cellular":
        contents += "\n" + get_file_config(app_path + "/templ/cellular_config_templ.py", keyValuePairDictionary)
        contents += "\n" + get_file_config(app_path + "/templ/protocol_config_templ.py", keyValuePairDictionary)
    elif operation == "lora":
        contents += "\n" + get_file_config(app_path + "/templ/shield_lora_templ.py", keyValuePairDictionary)
        contents += "\n" + get_file_config(app_path + "/templ/lora_config_templ.py", keyValuePairDictionary)
    elif operation == "satellite":
        contents += "\n" + get_file_config(app_path + "/templ/satellite_config_templ.py", keyValuePairDictionary)

    # create new
    utils.writeToFile(config_file_explicit, contents)

    utils.clearCachedStates()

    gc.collect()
