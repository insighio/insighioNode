import machine

""" System configuration options """
_WD_PERIOD = 120 # watchdog time for rebooting in seconds

""" Measurement configuration options """
_UC_IO_BAT_MEAS_ON = 21
_UC_IO_BAT_READ = 10

""" Battery Voltage configuration """
_BAT_VDIV = 2
_BAT_ATT = machine.ADC.ATTN_11DB

''' Parameters for i2c sensors '''
_UC_IO_I2C_SDA = 34
_UC_IO_I2C_SCL = 33

_UC_INTERNAL_TEMP_HUM_SENSOR = _CONST_SENSOR_SHT40

""" Load Regulator configuration """
_UC_IO_LOAD_PWR_SAVE_OFF = None

""" External Sensors configuration """
_UC_IO_SENSOR_SWITCH_ON = 12
_UC_IO_ANALOG_DIGITAL_P1 = 4
_UC_IO_ANALOG_DIGITAL_P2 = 5

""" Modem/GPS PIN configuration """
_UC_IO_RADIO_ON = 13
_UC_IO_PWRKEY = 14
_UC_UART_MODEM_TX = 15
_UC_UART_MODEM_RX = 16

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
