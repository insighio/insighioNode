import machine

""" Measurement configuration options """
_UC_IO_BAT_MEAS_ON = 21
_UC_IO_BAT_READ = 10

""" Battery Voltage configuration """
_BAT_VDIV = 2
_BAT_ATT = machine.ADC.ATTN_11DB

''' Parameters for i2c sensors '''
_UC_IO_I2C_SDA = 34
_UC_IO_I2C_SCL = 33

_UC_IO_ONB_SNSR_ON = 35
_UC_IO_RGB_DIN = 36
_UC_RGB_VDD = 37

_UC_INTERNAL_TEMP_HUM_SENSOR = _CONST_SENSOR_SHT40

""" External Sensors configuration """
_UC_IO_SENSOR_SWITCH_ON = 12
_UC_IO_ANALOG_DIGITAL_P1 = 1
_UC_IO_ANALOG_DIGITAL_P2 = 2
_UC_IO_ANALOG_DIGITAL_P3 = 3


""" Modem/GPS PIN configuration """
_UC_IO_RADIO_ON = 13
_UC_IO_PWRKEY = 14
_UC_UART_MODEM_TX = 15
_UC_UART_MODEM_RX = 16
