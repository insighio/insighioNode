# boot.py -- run on boot-up

# if on battery, enable this for early low voltage detection.
#import gpio_handler
# #
print("---Checking Voltage")

from gpio_handler import set_pin_value, get_input_voltage
import machine
import uos
from machine import SoftI2C, Pin, ADC, deepsleep
from utime import sleep_ms

voltage = None
i2c = None
_is_esp32s3 = "esp32s3" in uos.uname().machine.lower()
_UC_IO_BAT_MEAS_ON = 14 if _is_esp32s3 else 27
_UC_IO_BAT_READ = 3 if _is_esp32s3 else 36

bq_addr = 0x6B

try:
    i2c = SoftI2C(scl=Pin(38), sda=Pin(39))  # cfg._UC_IO_I2C_SCL, cfg._UC_IO_I2C_SDA
    #setup fast charing
    i2c.writeto_mem(bq_addr, 5, b"\x84")
    i2c.writeto_mem(bq_addr, 0, b"\x22")
except Exception as e:
    print("No BQ charger detected")

try:
    if i2c:
        # set charging off
        i2c.writeto_mem(bq_addr, 1, b"\x2B")
except Exception as e:
    print("can not close charging")

set_pin_value(_UC_IO_BAT_MEAS_ON, 1)
sleep_ms(100)
voltage = get_input_voltage(_UC_IO_BAT_READ, 2, ADC.ATTN_11DB)
print("batt voltage: {}".format(voltage))
set_pin_value(_UC_IO_BAT_MEAS_ON, 0)

try:
    if i2c:
        # set charging on
        i2c.writeto_mem(bq_addr, 1, b"\x3B")
except Exception as e:
    logging.error("can not open charging")

if voltage < 3300:
    print("Low voltage, sleeping for an hour")
    deepsleep(3600000)

print("---Voltage OK")
