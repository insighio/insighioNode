# boot.py -- run on boot-up

print("[boot] Checking Voltage")

import uos
from gpio_handler import set_pin_value, get_input_voltage
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
    print("[boot] No BQ charger detected")

try:
    if i2c:
        # set charging off
        i2c.writeto_mem(bq_addr, 1, b"\x2B")
except Exception as e:
    print("[boot] can not close charging")

set_pin_value(_UC_IO_BAT_MEAS_ON, 1)
sleep_ms(100)
voltage = get_input_voltage(_UC_IO_BAT_READ, 2, ADC.ATTN_11DB)
print("[boot] batt voltage: {}".format(voltage))
set_pin_value(_UC_IO_BAT_MEAS_ON, 0)

try:
    if i2c:
        # set charging on
        i2c.writeto_mem(bq_addr, 1, b"\x3B")
except Exception as e:
    print("[boot] can not open charging")

if voltage < 3300:
    print("[boot] Low voltage, sleeping for an hour")
    deepsleep(3600000)

print("[boot] Voltage OK")

# setup data paritition
from esp32 import Partition
p = Partition.find(Partition.TYPE_DATA, label='data')[0]

try:
    if p:
        uos.mount(p, "/data")
        print("[boot] Mounted /data")
    else:
        print("[boot] Data partition not found")
except OSError:
    try:
        uos.VfsLfs2.mkfs(p)
        vfs = uos.VfsLfs2(p)
        uos.mount(vfs, '/data')
        print("[boot] Created + Mounted /data")
    except OSError:
        print("[boot] Failed mounting /data")
