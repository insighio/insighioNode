##################################################################
# check performance

# # boot.py -- run on boot-up
from machine import Pin
from neopixel import NeoPixel

Pin(47, Pin.OUT).on()
_led_neopixel = NeoPixel(Pin(21, Pin.OUT), 1)

from utime import time_ns
test_load_start = time_ns()
import utils
loadtime = time_ns() - test_load_start

color = loadtime << 8
_led_neopixel[0] = (
    (color & 0xFF0000) >> 16,
    (color & 0x00FF00) >> 8,
    (color & 0x0000FF),
)
_led_neopixel.write()

#use normal files (not flags) to check file system performance

if not utils.existsFile("/perfOk"):
    print("Module load duration {}ms".format(loadtime))
    prevtime = utils.readFromFile("/loadtesting")
    try:
        prevtime = int(prevtime)
    except:
        prevtime = None

    if prevtime is not None and prevtime > loadtime:
        print("======== drop detected ========")
        utils.writeToFile("/perfOk", "ok")
        utils.deleteFile("/loadtesting")
    else:
        utils.writeToFile("/loadtesting", "{}".format(loadtime))
    from machine import deepsleep
    deepsleep(1)
else:
    print("[boot]: performance ok")

Pin(47, Pin.OUT).off()


##################################################################
# check voltage

print("[boot] Checking Voltage")

import uos
from machine import SoftI2C, Pin, ADC, deepsleep

voltage = None
i2c = None
_is_esp32s3 = "esp32s3" in uos.uname().machine.lower()
_UC_IO_BAT_MEAS_ON = 14 if _is_esp32s3 else 27
_UC_IO_BAT_READ = 3 if _is_esp32s3 else 36

bq_addr = 0x6B

##################################################################
# initialize BQ charger setup
try:
    i2c = SoftI2C(scl=Pin(38), sda=Pin(39))  # cfg._UC_IO_I2C_SCL, cfg._UC_IO_I2C_SDA
    #setup fast charing
    i2c.writeto_mem(bq_addr, 5, b"\x84")
    i2c.writeto_mem(bq_addr, 0, b"\x22")
except Exception as e:
    print("[boot] No BQ charger detected")

_is_charging = True
_check_charging_state = True # must be deactivated for devices always conneced to USB charger

if _check_charging_state:
    try:
        val = i2c.readfrom_mem(bq_addr, 8, 1)
        _is_charging = (int.from_bytes(val, "big") & 0x4) > 0
    except Exception as e:
        print("[boot] can not check charging state")

if not _is_charging:
    from gpio_handler import set_pin_value, get_input_voltage
    from utime import sleep_ms

    ##################################################################
    # if not charging, check battery voltage
    import utils
    voltage_flag_file = "/voltage_low"
    low_voltage_flag_exists = utils.existsFlagFile(voltage_flag_file)

    ##################################################################
    # # set charging off
    try:
        if i2c:
            i2c.writeto_mem(bq_addr, 1, b"\x0B")
    except Exception as e:
        print("[boot] can not close charging")

    ##################################################################
    # check voltage
    set_pin_value(_UC_IO_BAT_MEAS_ON, 1)

    check_cnt_max = 30
    check_cnt = 0

    voltage_low = False
    voltage_mid = False
    voltage_ok = False

    VOLTAGE_LOW = 3500
    VOLTAGE_MIN_OPERATING = 3600

    while check_cnt < check_cnt_max:
        sleep_ms(100)
        voltage = get_input_voltage(_UC_IO_BAT_READ, 2, ADC.ATTN_11DB)

        if voltage<VOLTAGE_LOW:
            voltage_low = True
        elif voltage>=VOLTAGE_LOW and voltage<VOLTAGE_MIN_OPERATING and low_voltage_flag_exists:
            voltage_mid = True
        else:
            voltage_ok = True
            break
        check_cnt += 1
    print("[boot] batt voltage: {}".format(voltage))

    set_pin_value(_UC_IO_BAT_MEAS_ON, 0)

    ##################################################################
    # set charging on

    try:
        if i2c:
            # set charging on
            i2c.writeto_mem(bq_addr, 1, b"\x1B")
    except Exception as e:
        print("[boot] can not open charging")

    ##################################################################
    # execute deepsleep if needed
    if voltage_ok and low_voltage_flag_exists:
        utils.deleteFlagFile(voltage_flag_file)
    elif voltage_mid:
        print('Low voltage, sleeping for an hour');
        deepsleep(3600000)
    elif voltage_low:
        print('Low voltage, sleeping for a day');
        utils.writeToFlagFile(voltage_flag_file, "charging")
        deepsleep(86400000)
else:
    print("[boot] device charging")

print("[boot] Voltage OK")

##################################################################
# setup data paritition
from esp32 import Partition
p = Partition.find(Partition.TYPE_DATA, label='data')
if len(p) > 0 :
    p = p[0]

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

##################################################################
