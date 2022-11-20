import machine

""" System configuration options """
_WD_PERIOD = 120 # watchdog time for rebooting in seconds

""" Measurement configuration options """
_UC_IO_BAT_MEAS_ON = 14
_UC_IO_BAT_READ = 3

""" Battery Voltage configuration """
_BAT_VDIV = 2
_BAT_ATT = machine.ADC.ATTN_11DB

''' Parameters for i2c sensors '''
_UC_IO_I2C_SDA = 39
_UC_IO_I2C_SCL = 38

_UC_IO_RGB_DIN = 21
_UC_RGB_VDD = 47

_UC_INTERNAL_TEMP_HUM_SENSOR = _CONST_SENSOR_SHT40

""" External Sensors configuration """
_UC_IO_SENSOR_GND_ON = 12

""" Modem/GPS PIN configuration """
_UC_IO_RADIO_ON = 13
_UC_IO_PWRKEY = 10
_UC_UART_MODEM_TX = 35
_UC_UART_MODEM_RX = 36

""" const i2c addresses """
_I2C_BQ_ADDRESS = 0x6B
