_CONST_BOARD_TYPE_DEFAULT = "default"
_CONST_BOARD_TYPE_SDI_12 = "sdi12"
_CONST_BOARD_TYPE_ESP_GEN_1 = "ins_esp_gen_1"
_CONST_BOARD_TYPE_ESP_GEN_SHIELD_1 = "ins_esp_gen_s1"
_CONST_BOARD_TYPE_ESP_GEN_SHIELD_2_S3 = "ins_esp_gen_s2_s3"
_CONST_BOARD_TYPE_ESP_GEN_SHIELD_SDI12 = "ins_esp_gen_sdi12"

_CONST_SENSOR_SI7021 = 'si7021'
_CONST_SENSOR_SHT40 = 'SHT40'

_CONST_MEAS_DISABLED = "disabled"

_BOARD_TYPE = "<selected-board>"

""" System-related configuration options """
_DEEP_SLEEP_PERIOD_SEC = <period>  # tx period in secs
_BATCH_UPLOAD_MESSAGE_BUFFER = <batch-upload-buffer-size>
_SCHEDULED_TIMESTAMP_A_SECOND = <scheduled-time-a>
_SCHEDULED_TIMESTAMP_B_SECOND = <scheduled-time-b>
_ALWAYS_ON_CONNECTION = <always-on-connection>
_FORCE_ALWAYS_ON_CONNECTION = <force-always-on-connection>
_ALWAYS_ON_PERIOD = <always-on-period>

""" Explicit Key-Value Pairs """
_MEAS_KEYVALUE=<meas-keyvalue>

''' measurements that are controlled by boolean values '''
_MEAS_BATTERY_STAT_ENABLE = <meas-battery-stat>
_MEAS_BOARD_SENSE_ENABLE = <meas-board-sense>
_MEAS_BOARD_STAT_ENABLE = <meas-board-stat>
_MEAS_NETWORK_STAT_ENABLE = <meas-network-stat>
_MEAS_TEMP_UNIT_IS_CELSIUS = <meas-temp-unit>

_MEAS_GPS_ENABLE = <meas-gps-enabled>
_MEAS_GPS_TIMEOUT = <meas-gps-timeout>
_MEAS_GPS_SATELLITE_FIX_NUM = <meas-gps-sat-num>

_CHECK_FOR_OTA = <system-enable-ota>

_NOTIFICATION_LED_ENABLED = <meas-led-enabled>

""" System configuration options """
_WD_PERIOD = 120 # watchdog time for rebooting in seconds
