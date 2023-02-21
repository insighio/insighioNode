import machine

""" Measurement configuration options """
_UC_IO_BAT_MEAS_ON = 27
_UC_IO_BAT_READ = 36

""" Battery Voltage configuration """
_BAT_VDIV = 2
_BAT_ATT = machine.ADC.ATTN_11DB

''' external Sensor related parameters '''
_UC_IO_SENSOR_SWITCH_ON = 25

''' Parameters for i2c sensors '''
_UC_IO_I2C_SDA = 21
_UC_IO_I2C_SCL = 22

''' Pins for Sensair Sunrise sensor '''
_SENSAIR_EN_PIN_NUM = 33
_SENSAIR_nRDY_PIN_NUM = 4

_UC_INTERNAL_TEMP_HUM_SENSOR = _CONST_SENSOR_SHT40

""" Load Regulator configuration """
_UC_IO_LOAD_PWR_SAVE_OFF = None

""" External Sensors configuration """
#_UC_IO_SENSOR_GND_ON = 12

""" Modem/GPS PIN configuration """
_UC_IO_RADIO_ON = 26
_UC_IO_PWRKEY = 23
_UC_UART_MODEM_TX = 19
_UC_UART_MODEM_RX = 18
_UC_UART_GPS_TX = 13
_UC_UART_GPS_RX = 14

""" const i2c addresses """
_I2C_BQ_ADDRESS = 0x6B
