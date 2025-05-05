_SELECTED_SHIELD = _CONST_SHIELD_ENVIRO

""" SDI-12 """

_UC_IO_RCV_OUT = 9
_UC_IO_DRV_ON = 11
_UC_IO_RCV_ON = 42
_UC_IO_DRV_IN = 41
_UC_IO_SNSR_REG_ON = 8

_UC_IO_EXPANDER_ADDR = 0x20

""" Modbus """

_UC_IO_MODBUS_DRV_IN = 1
_UC_IO_MODBUS_RCV_ON = 2
_UC_IO_MODBUS_RCV_OUT = 17
_UC_IO_MODBUS_DRV_ON = 37


""" ADS """
_UC_IO_ADS_ADDR = 0x48
_ADS_GAIN = 2  # 0 : 6.144V # 2/3x | 1 : 4.096V # 1x | 2 : 2.048V # 2x | 3 : 1.024V # 4x | 4 : 0.512V # 8x | 5 : 0.256V # 16x
_ADS_RATE = 1  # 0 :  128/8 | 1 :  250/16 | 2 :  490/32 | 3 :  920/64 | 4 :  1600/128 | 5 :  2400/250 | 6 :  3300/475 | 7 :  - /860

# needs revisiting

""" Pulse counter """
UC_IO_DGTL_SNSR_READ = 2

""" Chip ID """
_I2C_CHIP_ID_ADDRESS = 0x54

# prettier-ignore-start

_MEAS_SDI12 = '<meas-sdi12>'
_MEAS_MODBUS = '<meas-modbus>'
_MEAS_ADC = '<meas-adc>'
_MEAS_PULSECOUNTER = '<meas-pulseCounter>'

# prettier-ignore-end
