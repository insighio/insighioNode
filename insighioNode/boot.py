##################################################################
# check performance

# # boot.py -- run on boot-up
from utime import time_ns
import uos

test_load_start = time_ns()
import utils

loadtime = time_ns() - test_load_start

# use normal files (not flags) to check file system performance

if not utils.existsFile("/perfOk") and "esp32s3" in uos.uname().machine.lower().split(" ")[0]:
    from machine import Pin
    from neopixel import NeoPixel

    Pin(47, Pin.OUT).on()
    _led_neopixel = NeoPixel(Pin(21, Pin.OUT), 1)

    color_index = loadtime % 3
    color = 0x252525
    if color_index == 0:
        color = 0x250000
    elif color_index == 1:
        color = 0x002500
    elif color_index == 2:
        color = 0x000025

    _led_neopixel[0] = (
        (color & 0xFF0000) >> 16,
        (color & 0x00FF00) >> 8,
        (color & 0x0000FF),
    )
    _led_neopixel.write()

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

    Pin(47, Pin.OUT).off()

    from machine import reset

    reset()
else:
    print("[boot]: performance ok")

import sys

sys.path.clear()
sys.path.append("/lib")
sys.path.append(".frozen")
sys.path.append("")

##################################################################
# setup data paritition
from esp32 import Partition

p = Partition.find(Partition.TYPE_DATA, label="data")
if len(p) > 0:
    p = p[0]

try:
    if p:
        uos.mount(p, "/data")
        print("[boot] Mounted /data")

        utils.update_USE_DATA_DIR()
    else:
        print("[boot] Data partition not found")
except OSError:
    try:
        uos.VfsLfs2.mkfs(p)
        vfs = uos.VfsLfs2(p)
        uos.mount(vfs, "/data")
        print("[boot] Created + Mounted /data")
        utils.update_USE_DATA_DIR()
    except OSError:
        print("[boot] Failed mounting /data")

##################################################################
# check voltage

print("[boot] Checking Voltage")

from machine import Pin, ADC
from device_info import (
    get_main_version,
    _MAIN_VERSION_V1,
    bq_charger_exec,
    bq_charger_setup,
    bq_charger_get_is_charging,
    bq_charger_get_vbat_adc,
)

hw_version = get_main_version()

voltage = None
_UC_IO_BAT_MEAS_ON = 14 if hw_version == _MAIN_VERSION_V1 else None
_UC_IO_BAT_READ = 3 if hw_version == _MAIN_VERSION_V1 else None

try:
    bq_charger_exec(bq_charger_setup)
except Exception as e:
    print("[boot] No BQ charger detected")

_is_charging = True
_check_charging_state = True  # must be deactivated for devices always connected to USB charger

if _check_charging_state:
    _is_charging = bq_charger_exec(bq_charger_get_is_charging)

if not _is_charging:
    from gpio_handler import set_pin_value, get_input_voltage
    from utime import sleep_ms

    ##################################################################
    # if not charging, check battery voltage
    import utils

    voltage_flag_file = "/voltage_low"
    low_voltage_flag_exists = utils.existsFlagFile(voltage_flag_file)

    if hw_version == _MAIN_VERSION_V1:
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
        if hw_version == _MAIN_VERSION_V1:
            voltage = get_input_voltage(_UC_IO_BAT_READ, 2, ADC.ATTN_11DB)
        else:
            voltage = bq_charger_exec(bq_charger_get_vbat_adc)

        if voltage < VOLTAGE_LOW:
            voltage_low = True
        elif voltage >= VOLTAGE_LOW and voltage < VOLTAGE_MIN_OPERATING and low_voltage_flag_exists:
            voltage_mid = True
        else:
            voltage_ok = True
            break
        check_cnt += 1
    print("[boot] batt voltage: {}".format(voltage))

    if hw_version == _MAIN_VERSION_V1:
        set_pin_value(_UC_IO_BAT_MEAS_ON, 0)

    ##################################################################
    # execute deepsleep if needed
    if voltage_ok and low_voltage_flag_exists:
        utils.deleteFlagFile(voltage_flag_file)
        print("[boot] Battery recovered")
    elif voltage_mid:
        print("[boot] Low voltage, sleeping for an hour")
        from machine import deepsleep

        deepsleep(3600000)
    elif voltage_low:
        print("[boot] Low voltage, sleeping for a day")
        utils.writeToFlagFile(voltage_flag_file, "charging")
        from machine import deepsleep

        deepsleep(86400000)
    else:
        print("[boot] Battery not charging: {}mV".format(voltage))
else:
    print("[boot] device charging")

print("[boot] Voltage OK")

##################################################################
