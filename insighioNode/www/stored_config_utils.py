import logging

configDict = dict()
configDict["_APN"] = "cell-apn"
configDict["_APP_EUI"] = "lora-app-eui"
configDict["_APP_KEY"] = "lora-app-key"
configDict["_BAND"] = "cell-band"
configDict["_BATCH_UPLOAD_MESSAGE_BUFFER"] = "batch-upload-buffer-size"
configDict["_BOARD_TYPE"] = "selected-board"
configDict["_CELLULAR_TECHNOLOGY"] = "cell-tech"
configDict["_CHECK_FOR_OTA"] = "system-enable-ota"
configDict["_DEEP_SLEEP_PERIOD_SEC"] = "period"
configDict["_DEV_EUI"] = "lora-dev-eui"
configDict["_IP_VERSION"] = "ipversion"
configDict["_LORA_ADR"] = "lora-adr"
configDict["_LORA_CONFIRMED"] = "lora-confirmed"
configDict["_LORA_DR"] = "lora-dr"
configDict["_LORA_REGION"] = "lora-region"
configDict["_LORA_TX_RETRIES"] = "lora-retries"
configDict["_MEAS_ANALOG_DIGITAL_P1"] = "meas-sensor-a-d-p1"
configDict["_MEAS_ANALOG_DIGITAL_P1_TRANSFORMATION"] = "meas-sensor-a-d-p1-t"
configDict["_MEAS_ANALOG_DIGITAL_P2"] = "meas-sensor-a-d-p2"
configDict["_MEAS_ANALOG_DIGITAL_P2_TRANSFORMATION"] = "meas-sensor-a-d-p2-t"
configDict["_MEAS_ANALOG_P1"] = "meas-sensor-a-p1"
configDict["_MEAS_ANALOG_P1_TRANSFORMATION"] = "meas-sensor-a-p1-t"
configDict["_MEAS_ANALOG_P2"] = "meas-sensor-a-p2"
configDict["_MEAS_ANALOG_P2_TRANSFORMATION"] = "meas-sensor-a-p2-t"
configDict["_MEAS_BATTERY_STAT_ENABLE"] = "meas-battery-stat"
configDict["_MEAS_BOARD_SENSE_ENABLE"] = "meas-board-sense"
configDict["_MEAS_BOARD_STAT_ENABLE"] = "meas-board-stat"
configDict["_MEAS_GPS_ENABLE"] = "meas-gps-enabled"
configDict["_MEAS_GPS_SATELLITE_FIX_NUM"] = "meas-gps-sat-num"
configDict["_MEAS_GPS_TIMEOUT"] = "meas-gps-timeout"
configDict["_MEAS_I2C_1"] = "meas-i2c-1"
configDict["_MEAS_I2C_2"] = "meas-i2c-2"
configDict["_MEAS_KEYVALUE"]="meas-keyvalue"
configDict["_MEAS_NETWORK_STAT_ENABLE"] = "meas-network-stat"
configDict["_MEAS_SCALE_ENABLED"] = "meas-scale-enabled"
configDict["_MEAS_TEMP_UNIT_IS_CELSIUS"] = "meas-temp-unit"
configDict["_NOTIFICATION_LED_ENABLED"] = "meas-led-enabled"
configDict["_SCHEDULED_TIMESTAMP_A_SECOND"] = "scheduled-time-a"
configDict["_SCHEDULED_TIMESTAMP_B_SECOND"] = "scheduled-time-b"
configDict["_SDI12_SENSOR_1_ADDRESS"] = "meas-sdi-1-address"
configDict["_SDI12_SENSOR_1_ENABLED"] = "meas-sdi-1-enabled"
configDict["_SDI12_SENSOR_2_ADDRESS"] = "meas-sdi-2-address"
configDict["_SDI12_SENSOR_2_ENABLED"] = "meas-sdi-2-enabled"
configDict["_SDI12_WARM_UP_TIME_MSEC"] = "meas-sdi-warmup-time"
configDict["_UC_IO_SCALE_OFFSET"] = "meas-scale-offset"
configDict["_UC_IO_SCALE_SCALE"] = "meas-scale-scale"
configDict["protocol"] = "protocol"

NoneType = type(None)

def get_config_values():
    configKeyValues = dict()
    try:
        #import apps.demo_console.demo_config as cfg
        import demo_config as cfg
    except:
        return configKeyValues

    for key in dir(cfg):
        try:
            webUIKey = configDict[key]
            logging.debug("Key [{}] accepted as [{}]".format(key, webUIKey))
        except:
            logging.debug("Key [{}] ignored".format(key))
            continue

        value = getattr(cfg, key)
        if not isinstance(value, (int, float, str, bool, NoneType, dict)):
            logging.debug("  value not of accepted type [{}], ignoring".format(type(value)))
        configKeyValues[webUIKey] = value

    try:
        proto_config = cfg.get_protocol_config()
        configKeyValues["insighio-channel"] = proto_config.message_channel_id
        configKeyValues["insighio-control-channel"] = proto_config.control_channel_id
        configKeyValues["insighio-id"] = proto_config.thing_id
        configKeyValues["insighio-key"] = proto_config.thing_token
    except:
        pass

    try:
        if hasattr(cfg, "_CONF_NETS"):
            ssid = list(cfg._CONF_NETS.keys())[0]
            configKeyValues["wifi-ssid"] = ssid
            configKeyValues["wifi-pass"] = cfg._CONF_NETS[ssid]['pwd']
    except:
        pass

    return configKeyValues
