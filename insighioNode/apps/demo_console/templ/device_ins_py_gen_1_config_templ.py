""" System configuration options """
_WD_PERIOD = 120 # watchdog time for rebooting in seconds
_BOARD_TYPE = "<selected-board>"
_CONST_BOARD_TYPE_DEFAULT = "default"
_CONST_BOARD_TYPE_SDI_12 = "sdi12"
_CONST_BOARD_TYPE_ESP_GEN_1 = "ins_esp_gen_1"

""" Measurement configuration options """
_UC_IO_BAT_MEAS_ON = 'P23'
_UC_IO_CHARGER_OFF = 'P22'
_UC_IO_WATCHDOG_RESET = 'P21'
_UC_IO_BAT_READ = 'P13'
_UC_IO_CUR_READ = 'P14'

""" Battery Voltage configuration """
_BAT_VDIV = 11
_BAT_ATT = 0
""" Current Sensor configuration """
_CUR_VDIV = 1
_CUR_ATT = 3
_CUR_GAIN = 100
_CUR_RSENSE = 0.08
_CUR_VREF_mV = 0

''' external Sensor related parameters '''
_UC_IO_SENSOR_SWITCH_ON = 'P11'

''' Parameters for i2c sensors '''
_UC_IO_I2C_SDA = 'P9'
_UC_IO_I2C_SCL = 'P10'

_UC_INTERNAL_TEMP_HUM_SENSOR = _CONST_SENSOR_SI7021

''' measurements that are controlled by boolean values '''
_MEAS_BATTERY_STAT_ENABLE = <meas-battery-stat>
_MEAS_BOARD_SENSE_ENABLE = <meas-board-sense>
_MEAS_BOARD_STAT_ENABLE = <meas-board-stat>
_MEAS_NETWORK_STAT_ENABLE = <meas-network-stat>
_MEAS_TEMP_UNIT_IS_CELSIUS = <meas-temp-unit>

_CONST_MEAS_DISABLED = "disabled"
