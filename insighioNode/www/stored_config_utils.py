import logging

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
"_MEAS_ANALOG_P1": "meas_sensor_a_p1",
"_MEAS_ANALOG_P1_TRANSFORMATION": "meas_sensor_a_p1_t",
"_MEAS_ANALOG_P2": "meas_sensor_a_p2",
"_MEAS_ANALOG_P2_TRANSFORMATION": "meas_sensor_a_p2_t",
"_MEAS_BATTERY_STAT_ENABLE": "meas_battery_stat",
"_MEAS_BOARD_SENSE_ENABLE": "meas_board_sense",
"_MEAS_BOARD_STAT_ENABLE": "meas_board_stat",
"_MEAS_GPS_ENABLE": "meas_gps_enabled",
"_MEAS_GPS_SATELLITE_FIX_NUM": "meas_gps_sat_num",
"_MEAS_GPS_TIMEOUT": "meas_gps_timeout",
"_MEAS_I2C_1": "meas_i2c_1",
"_MEAS_I2C_2": "meas_i2c_2",
"_MEAS_KEYVALUE": "meas_keyvalue",
"_MEAS_NETWORK_STAT_ENABLE": "meas_network_stat",
"_MEAS_SCALE_ENABLED": "meas_scale_enabled",
"_MEAS_TEMP_UNIT_IS_CELSIUS": "meas_temp_unit",
"_NOTIFICATION_LED_ENABLED": "meas_led_enabled",
"_SCHEDULED_TIMESTAMP_A_SECOND": "scheduled_time_a",
"_SCHEDULED_TIMESTAMP_B_SECOND": "scheduled_time_b",
"_SDI12_SENSOR_1_ADDRESS": "meas_sdi_1_address",
"_SDI12_SENSOR_1_ENABLED": "meas_sdi_1_enabled",
"_SDI12_SENSOR_2_ADDRESS": "meas_sdi_2_address",
"_SDI12_SENSOR_2_ENABLED": "meas_sdi_2_enabled",
"_SDI12_WARM_UP_TIME_MSEC": "meas_sdi_warmup_time",
"_UC_IO_SCALE_OFFSET": "meas_scale_offset",
"_UC_IO_SCALE_SCALE": "meas_scale_scale",
"protocol": "protocol"
}

NoneType = type(None)

def get_config_values():
    configKeyValues = dict()

    logging.debug("Loading local configuration...")

    try:
        import apps.demo_console.demo_config as cfg
    except:
        return configKeyValues

    for key in dir(cfg):
        try:
            webUIKey = configDict[key]
        except:
            continue

        value = getattr(cfg, key)
        if isinstance(value, (int, float, str)):
            configKeyValues[webUIKey] = str(value)
        elif isinstance(value, bool):
            configKeyValues[webUIKey] = str(value).lower()
        elif isinstance(value, NoneType):
            configKeyValues[webUIKey] = "undefined"
        elif isinstance(value, dict):
            import ujson
            configKeyValues[webUIKey] = ujson.dumps(value)

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
        pass

    try:
        if hasattr(cfg, "_CONF_NETS"):
            ssid = list(cfg._CONF_NETS.keys())[0]
            configKeyValues["wifi_ssid"] = ssid
            configKeyValues["wifi_pass"] = cfg._CONF_NETS[ssid]['pwd']
        else:
            configKeyValues["wifi_ssid"] = ""
            configKeyValues["wifi_pass"] = ""
    except:
        pass

    logging.debug("Marking all unused configuration variables")

    # for any value that has not been set by the config
    # fill with empty values
    for key in configDict.keys():
        sec_key = configDict[key]
        try:
            configKeyValues[sec_key]
        except KeyError:
            configKeyValues[sec_key] = "undefined"

    logging.debug("Configuration loading done.")

    return configKeyValues
