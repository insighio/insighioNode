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
    "_APP_EUI": "lora_app_eui",
    "_APP_KEY": "lora_app_key",
    "_BAND": "cell_band",
    "_BATCH_UPLOAD_MESSAGE_BUFFER": "batch_upload_buffer_size",
    "_BOARD_TYPE": "selected_board",
    "_CELLULAR_TECHNOLOGY": "cell_tech",
    "_CHECK_FOR_OTA": "system_enable_ota",
    "_DEEP_SLEEP_PERIOD_SEC": "period",
    "_DEV_EUI": "lora_dev_eui",
    "_IP_VERSION": "ipversion",
    "_LIGHT_SLEEP_DEACTIVATE_ON_BATTERY": "light_sleep_deactivate_on_battery",
    "_LIGHT_SLEEP_NETWORK_ACTIVE": "light_sleep_network_active",
    "_LIGHT_SLEEP_ON": "light_sleep_on",
    "_LORA_ADR": "lora_adr",
    "_LORA_CONFIRMED": "lora_confirmed",
    "_LORA_DR": "lora_dr",
    "_LORA_REGION": "lora_region",
    "_LORA_TX_RETRIES": "lora_retries",
    "_MEAS_ANALOG_DIGITAL_P1": "meas_sensor_a_d_p1",
    "_MEAS_ANALOG_DIGITAL_P1_TRANSFORMATION": "meas_sensor_a_d_p1_t",
    "_MEAS_ANALOG_DIGITAL_P2": "meas_sensor_a_d_p2",
    "_MEAS_ANALOG_DIGITAL_P2_TRANSFORMATION": "meas_sensor_a_d_p2_t",
    "_MEAS_ANALOG_DIGITAL_P3": "meas_sensor_a_d_p3",
    "_MEAS_ANALOG_DIGITAL_P3_TRANSFORMATION": "meas_sensor_a_d_p3_t",
    "_MEAS_BATTERY_STAT_ENABLE": "meas_battery_stat",
    "_MEAS_BOARD_SENSE_ENABLE": "meas_board_sense",
    "_MEAS_BOARD_STAT_ENABLE": "meas_board_stat",
    "_MEAS_GPS_ENABLE": "meas_gps_enabled",
    "_MEAS_GPS_SATELLITE_FIX_NUM": "meas_gps_sat_num",
    "_MEAS_GPS_TIMEOUT": "meas_gps_timeout",
    "_MEAS_I2C_1": "meas_i2c_1",
    "_MEAS_I2C_2": "meas_i2c_2",
    "_MEAS_KEYVALUE": "meas_keyvalue",
    "_MEAS_NAME_MAPPING": "meas_name_mapping",
    "_MEAS_NAME_EXT_MAPPING": "meas_name_ext_mapping",
    "_MEAS_NETWORK_STAT_ENABLE": "meas_network_stat",
    "_MEAS_SCALE_ENABLED": "meas_scale_enabled",
    "_MEAS_TEMP_UNIT_IS_CELSIUS": "meas_temp_unit",
    "_NOTIFICATION_LED_ENABLED": "meas_led_enabled",
    "_SELECTED_SHIELD": "selected_shield",
    "_SCHEDULED_TIMESTAMP_A_SECOND": "scheduled_time_a",
    "_SCHEDULED_TIMESTAMP_B_SECOND": "scheduled_time_b",
    "_SDI12_SENSOR_1_ADDRESS": "meas_sdi_1_address",
    "_SDI12_SENSOR_1_ENABLED": "meas_sdi_1_enabled",
    "_SDI12_SENSOR_1_LOCATION": "meas_sdi_1_loc",
    "_SDI12_SENSOR_2_ADDRESS": "meas_sdi_2_address",
    "_SDI12_SENSOR_2_ENABLED": "meas_sdi_2_enabled",
    "_SDI12_SENSOR_2_LOCATION": "meas_sdi_2_loc",
    "_SDI12_SENSOR_3_ADDRESS": "meas_sdi_3_address",
    "_SDI12_SENSOR_3_ENABLED": "meas_sdi_3_enabled",
    "_SDI12_SENSOR_3_LOCATION": "meas_sdi_3_loc",
    "_SDI12_SENSOR_4_ADDRESS": "meas_sdi_4_address",
    "_SDI12_SENSOR_4_ENABLED": "meas_sdi_4_enabled",
    "_SDI12_SENSOR_4_LOCATION": "meas_sdi_4_loc",
    "_SDI12_SENSOR_5_ADDRESS": "meas_sdi_5_address",
    "_SDI12_SENSOR_5_ENABLED": "meas_sdi_5_enabled",
    "_SDI12_SENSOR_5_LOCATION": "meas_sdi_5_loc",
    "_SDI12_SENSOR_6_ADDRESS": "meas_sdi_6_address",
    "_SDI12_SENSOR_6_ENABLED": "meas_sdi_6_enabled",
    "_SDI12_SENSOR_6_LOCATION": "meas_sdi_6_loc",
    "_SDI12_SENSOR_7_ADDRESS": "meas_sdi_7_address",
    "_SDI12_SENSOR_7_ENABLED": "meas_sdi_7_enabled",
    "_SDI12_SENSOR_7_LOCATION": "meas_sdi_7_loc",
    "_SDI12_SENSOR_8_ADDRESS": "meas_sdi_8_address",
    "_SDI12_SENSOR_8_ENABLED": "meas_sdi_8_enabled",
    "_SDI12_SENSOR_8_LOCATION": "meas_sdi_8_loc",
    "_SDI12_SENSOR_9_ADDRESS": "meas_sdi_9_address",
    "_SDI12_SENSOR_9_ENABLED": "meas_sdi_9_enabled",
    "_SDI12_SENSOR_9_LOCATION": "meas_sdi_9_loc",
    "_SDI12_SENSOR_10_ADDRESS": "meas_sdi_10_address",
    "_SDI12_SENSOR_10_ENABLED": "meas_sdi_10_enabled",
    "_SDI12_SENSOR_10_LOCATION": "meas_sdi_10_loc",
    "_SDI12_WARM_UP_TIME_MSEC": "meas_sdi_warmup_time",
    "_UC_IO_SCALE_OFFSET": "meas_scale_offset",
    "_UC_IO_SCALE_SCALE": "meas_scale_scale",
    "protocol": "protocol",
    "network": "network",
    "_ALWAYS_ON_CONNECTION": "always_on_connection",
    "_FORCE_ALWAYS_ON_CONNECTION": "force_always_on_connection",
    "_ALWAYS_ON_PERIOD": "always_on_period",
    "_MEAS_GPS_NO_FIX_NO_UPLOAD": "meas_gps_no_fix_no_upload",
    "_STORE_MEASUREMENT_IF_FAILED_CONNECTION": "store_meas_if_failed_conn",
    "_4_20_SNSR_1_ENABLE": "meas_4_20_snsr_1_enable",
    "_4_20_SNSR_1_FORMULA": "meas_4_20_snsr_1_formula",
    "_4_20_SNSR_2_ENABLE": "meas_4_20_snsr_2_enable",
    "_4_20_SNSR_2_FORMULA": "meas_4_20_snsr_2_formula",
    "_SATELLITE_ASTROCAST_DEVKIT_EN": "sat_astro_devkit_en",
    "_SATELLITE_ASTROCAST_DEVKIT_SSID": "sat_astro_devkit_ssid",
    "_SATELLITE_ASTROCAST_DEVKIT_PASS": "sat_astro_devkit_pass",
    "_SATELLITE_ASTROCAST_DEVKIT_TOKEN": "sat_astro_devkit_token",
    "_MEAS_SCALE_MONITORING_ENABLED": "meas_scale_monitoring_enabled",
    "_PCNT_1_ENABLE": "meas_pcnt_1_enable",
    "_PCNT_1_COUNT_ON_RISING": "meas_pcnt_1_cnt_on_rising",
    "_PCNT_1_HIGH_FREQ": "meas_pcnt_1_high_freq",
    "_PCNT_1_FORMULA": "meas_pcnt_1_formula",
    "_WIFI_SSID": "wifi_ssid",
    "_WIFI_PASS": "wifi_pass",
    "_MEAS_GPS_ONLY_ON_BOOT": "meas_gps_only_on_boot",
    "_MEAS_SDI12": "meas_sdi12",
    "_MEAS_MODBUS": "meas_modbus",
    "_MEAS_ADC": "meas_adc",
    "_MEAS_PULSECOUNTER": "meas_pulseCounter",
    "_SYSTEM_SETTINGS": "system_settings",
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
    utils.writeToFlagFile("/configLog", newConfig)


def get_file_config(fileName, keyValuePairs):
    gc.collect()
    logging.debug("Getting file config: {}".format(fileName))
    contents = utils.readFromFile(fileName)
    for param in keyValuePairs:
        # logging.debug("Replacing <{}> with {}, type: {}".format(param, keyValuePairs[param], type(keyValuePairs[param])))
        contents = contents.replace("<" + param + ">", keyValuePairs[param] if keyValuePairs[param] else "None")
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


def apply_configuration(keyValuePairDictionary, config_file_explicit=config_file, request_file_system_optimization=True):
    gc.collect()

    utils.copyFile(config_file_explicit, config_file_explicit + ".prev")

    # fix naming of keys to use '-' instead of '_'
    # unfortunately it is technical burden from old implementations, to be fixed in future release
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
    elif shield == "enviro":
        contents += get_file_config(app_path + "/templ/shield_enviro_templ.py", keyValuePairDictionary)
    #   contents += get_file_config(app_path + "/templ/device_enviro_config.py", keyValuePairDictionary)
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

    if request_file_system_optimization:
        utils.requestFileSystemOptimization()

    gc.collect()
