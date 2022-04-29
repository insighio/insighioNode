import logging

configDict = dict()
configDict["_APN"] = "cell_apn"
configDict["_APP_EUI"] = "lora_app_eui"
configDict["_APP_KEY"] = "lora_app_key"
configDict["_BAND"] = "cell_band"
configDict["_BATCH_UPLOAD_MESSAGE_BUFFER"] = "batch_upload_buffer_size"
configDict["_BOARD_TYPE"] = "selected_board"
configDict["_CELLULAR_TECHNOLOGY"] = "cell_tech"
configDict["_CHECK_FOR_OTA"] = "system_enable_ota"
configDict["_DEEP_SLEEP_PERIOD_SEC"] = "period"
configDict["_DEV_EUI"] = "lora_dev_eui"
configDict["_IP_VERSION"] = "ipversion"
configDict["_LORA_ADR"] = "lora_adr"
configDict["_LORA_CONFIRMED"] = "lora_confirmed"
configDict["_LORA_DR"] = "lora_dr"
configDict["_LORA_REGION"] = "lora_region"
configDict["_LORA_TX_RETRIES"] = "lora_retries"
configDict["_MEAS_ANALOG_DIGITAL_P1"] = "meas_sensor_a_d_p1"
configDict["_MEAS_ANALOG_DIGITAL_P1_TRANSFORMATION"] = "meas_sensor_a_d_p1_t"
configDict["_MEAS_ANALOG_DIGITAL_P2"] = "meas_sensor_a_d_p2"
configDict["_MEAS_ANALOG_DIGITAL_P2_TRANSFORMATION"] = "meas_sensor_a_d_p2_t"
configDict["_MEAS_ANALOG_P1"] = "meas_sensor_a_p1"
configDict["_MEAS_ANALOG_P1_TRANSFORMATION"] = "meas_sensor_a_p1_t"
configDict["_MEAS_ANALOG_P2"] = "meas_sensor_a_p2"
configDict["_MEAS_ANALOG_P2_TRANSFORMATION"] = "meas_sensor_a_p2_t"
configDict["_MEAS_BATTERY_STAT_ENABLE"] = "meas_battery_stat"
configDict["_MEAS_BOARD_SENSE_ENABLE"] = "meas_board_sense"
configDict["_MEAS_BOARD_STAT_ENABLE"] = "meas_board_stat"
configDict["_MEAS_GPS_ENABLE"] = "meas_gps_enabled"
configDict["_MEAS_GPS_SATELLITE_FIX_NUM"] = "meas_gps_sat_num"
configDict["_MEAS_GPS_TIMEOUT"] = "meas_gps_timeout"
configDict["_MEAS_I2C_1"] = "meas_i2c_1"
configDict["_MEAS_I2C_2"] = "meas_i2c_2"
configDict["_MEAS_KEYVALUE"]="meas_keyvalue"
configDict["_MEAS_NETWORK_STAT_ENABLE"] = "meas_network_stat"
configDict["_MEAS_SCALE_ENABLED"] = "meas_scale_enabled"
configDict["_MEAS_TEMP_UNIT_IS_CELSIUS"] = "meas_temp_unit"
configDict["_NOTIFICATION_LED_ENABLED"] = "meas_led_enabled"
configDict["_SCHEDULED_TIMESTAMP_A_SECOND"] = "scheduled_time_a"
configDict["_SCHEDULED_TIMESTAMP_B_SECOND"] = "scheduled_time_b"
configDict["_SDI12_SENSOR_1_ADDRESS"] = "meas_sdi_1_address"
configDict["_SDI12_SENSOR_1_ENABLED"] = "meas_sdi_1_enabled"
configDict["_SDI12_SENSOR_2_ADDRESS"] = "meas_sdi_2_address"
configDict["_SDI12_SENSOR_2_ENABLED"] = "meas_sdi_2_enabled"
configDict["_SDI12_WARM_UP_TIME_MSEC"] = "meas_sdi_warmup_time"
configDict["_UC_IO_SCALE_OFFSET"] = "meas_scale_offset"
configDict["_UC_IO_SCALE_SCALE"] = "meas_scale_scale"
configDict["protocol"] = "protocol"

NoneType = type(None)

def get_config_values():
    configKeyValues = dict()
    try:
        import apps.demo_console.demo_config as cfg
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
        configKeyValues["insighio_channel"] = proto_config.message_channel_id
        configKeyValues["insighio_control_channel"] = proto_config.control_channel_id
        configKeyValues["insighio_id"] = proto_config.thing_id
        configKeyValues["insighio_key"] = proto_config.thing_token
    except:
        pass

    try:
        if hasattr(cfg, "_CONF_NETS"):
            ssid = list(cfg._CONF_NETS.keys())[0]
            configKeyValues["wifi_ssid"] = ssid
            configKeyValues["wifi_pass"] = cfg._CONF_NETS[ssid]['pwd']
    except:
        pass

    return configKeyValues
