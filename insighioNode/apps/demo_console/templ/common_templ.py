_CONST_SHIELD_ACCELEROMETER = "accel"
_CONST_SHIELD_ADVIND = "advind"
_CONST_SHIELD_DIG_ANALOG = "dig_analog"
_CONST_SHIELD_SCALE = "scale"
_CONST_SHIELD_ENVIRO = "enviro"
_CONST_RADIO_SHIELD_LORA = "hoperf"
_CONST_RADIO_SHIELD_ASTROCAST = "astrocast"

_CONST_SENSOR_SI7021 = 'si7021'
_CONST_SENSOR_SHT40 = 'sht40'

_CONST_MEAS_DISABLED = "disabled"

_DEPRECATED_BOARD_TYPE = "<selected-board>"

""" System-related configuration options """
_DEEP_SLEEP_PERIOD_SEC = <period>  # tx period in secs
_LIGHT_SLEEP_ON = <light-sleep-on>
_LIGHT_SLEEP_NETWORK_ACTIVE = <light-sleep-network-active>
_LIGHT_SLEEP_DEACTIVATE_ON_BATTERY = <light-sleep-deactivate-on-battery>
_BATCH_UPLOAD_MESSAGE_BUFFER = <batch-upload-buffer-size>
_SCHEDULED_TIMESTAMP_A_SECOND = <scheduled-time-a>
_SCHEDULED_TIMESTAMP_B_SECOND = <scheduled-time-b>


""" Explicit Key-Value Pairs """
_MEAS_KEYVALUE=<meas-keyvalue>

""" Explicit Key-Value Pairs """
_MEAS_NAME_MAPPING=<meas-name-mapping>

""" Explicit Key-Value Pairs """
_MEAS_NAME_EXT_MAPPING=<meas-name-ext-mapping>

''' measurements that are controlled by boolean values '''
_MEAS_BATTERY_STAT_ENABLE = <meas-battery-stat>
_MEAS_BOARD_SENSE_ENABLE = <meas-board-sense>
_MEAS_BOARD_STAT_ENABLE = <meas-board-stat>
_MEAS_NETWORK_STAT_ENABLE = <meas-network-stat>
_MEAS_TEMP_UNIT_IS_CELSIUS = <meas-temp-unit>

_MEAS_GPS_ENABLE = <meas-gps-enabled>
_MEAS_GPS_TIMEOUT = <meas-gps-timeout>
_MEAS_GPS_SATELLITE_FIX_NUM = <meas-gps-sat-num>
_MEAS_GPS_NO_FIX_NO_UPLOAD = <meas-gps-no-fix-no-upload>
_MEAS_GPS_ONLY_ON_BOOT = <meas-gps-only-on-boot>

_CHECK_FOR_OTA = <system-enable-ota>

_NOTIFICATION_LED_ENABLED = <meas-led-enabled>

""" System configuration options """
_WD_PERIOD = 120 # watchdog time for rebooting in seconds

_STORE_MEASUREMENT_IF_FAILED_CONNECTION=<store-meas-if-failed-conn>

_SYSTEM_SETTINGS = '<system-settings>'
