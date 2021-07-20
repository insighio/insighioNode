import machine

""" System configuration options """
_WD_PERIOD = 120 # watchdog time for rebooting in seconds

_BOARD_TYPE = _CONST_BOARD_TYPE_ESP_GEN_1

""" Measurement configuration options """
_UC_IO_BAT_MEAS_ON = 27
# UC_IO_CHARGER_OFF = 'P22'
# UC_IO_WATCHDOG_RESET = 'P21'
_UC_IO_BAT_READ = 36
# _UC_IO_CUR_READ = 'P14'

""" Battery Voltage configuration """
_BAT_VDIV = 2
_BAT_ATT = machine.ADC.ATTN_11DB
# """ Current Sensor configuration """
# _CUR_VDIV = 1
# _CUR_ATT = 3
# _CUR_GAIN = 100
# _CUR_RSENSE = 0.08
# _CUR_VREF_mV = 0

''' external Sensor related parameters '''
_UC_IO_SENSOR_SWITCH_ON = 25

''' Parameters for i2c sensors '''
_UC_IO_I2C_SDA = 21
_UC_IO_I2C_SCL = 22

_UC_INTERNAL_TEMP_HUM_SENSOR = _CONST_SENSOR_SHT40

""" Load Regulator configuration """
_UC_IO_LOAD_PWR_SAVE_OFF = 'P4'

""" External Sensors configuration """
_UC_IO_ANALOG_DIGITAL_P1 = 32
_UC_IO_SCALE_CLOCK_PIN = 33
_UC_IO_SCALE_DATA_PIN = 4
_UC_IO_SCALE_SPI_PIN = 12

_UC_IO_SCALE_OFFSET = <meas-scale-offset>
_UC_IO_SCALE_SCALE = <meas-scale-scale>

''' measurements that are controlled by boolean values '''
_MEAS_BATTERY_STAT_ENABLE = <meas-battery-stat>
_MEAS_BOARD_SENSE_ENABLE = <meas-board-sense>
_MEAS_BOARD_STAT_ENABLE = <meas-board-stat>
_MEAS_NETWORK_STAT_ENABLE = <meas-network-stat>
_MEAS_TEMP_UNIT_IS_CELSIUS = <meas-temp-unit>
_MEAS_GPS_ENABLE = <meas-gps-enabled>
_MEAS_SCALE_ENABLED = <meas-scale-enabled>
