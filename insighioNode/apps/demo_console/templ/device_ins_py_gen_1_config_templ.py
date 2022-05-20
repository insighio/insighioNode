
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

""" Load Regulator configuration """
_UC_IO_LOAD_PWR_SAVE_OFF = 'P4'

""" External Sensors configuration """
_UC_IO_ANALOG_DIGITAL_P1 = 'P20'
_UC_IO_ANALOG_DIGITAL_P2 = 'P19'
_UC_IO_ANALOG_P1 = 'P18'
_UC_IO_ANALOG_P2 = 'P17'
