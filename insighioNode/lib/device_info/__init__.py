"""Module for getting various type of information from device"""

import gc
import machine
import uos
import ubinascii
import logging
from utime import sleep_ms

wdt = None
wdt_timeout = None

_led_pin_pwr = None
_led_neopixel = None

color_map = {}
color_map["blue"] = 0x0000F0
color_map["red"] = 0xF00000
color_map["yellow"] = 0xF0F000
color_map["green"] = 0x00F000
color_map["white"] = 0xFFFFFF
color_map["black"] = 0x000000

uos_version_data = uos.uname()
machine_data = uos_version_data.machine
firmware_data = uos_version_data.release.split(".")
firmware_commit_data = uos_version_data.version.split(" ")[0]

_CONST_ESP32 = "esp32"
_CONST_ESP32_WROOM = "esp32wroom"
_CONST_ESP32S2 = "esp32s2"
_CONST_ESP32S3 = "esp32s3"
_CONST_ESP8266 = "esp8266"

_CHARGER_VERSION_1 = "bq24297"
_CHARGER_VERSION_2 = "bq25622e"

_MAIN_VERSION_V1 = "v1"
_MAIN_VERSION_V2 = "v2"

_main_version = None
_bq_charger_version = None


def is_wdt_enabled():
    return wdt is not None


def get_hw_module_version():
    hw_info = machine_data
    hw_info = hw_info.lower()
    if _CONST_ESP32S2 in hw_info or "esp32-s2" in hw_info:
        return _CONST_ESP32S2
    elif _CONST_ESP32S3 in hw_info or "esp32-s3" in hw_info:
        return _CONST_ESP32S3
    elif _CONST_ESP32 in hw_info:
        if "spiram" in hw_info:
            return _CONST_ESP32
        else:
            return _CONST_ESP32_WROOM
    elif _CONST_ESP8266 in hw_info:
        return _CONST_ESP8266
    return "other"


# kept for compatibility
def get_hw_module_verison():
    return get_hw_module_version()


def supports_13bit_adc():
    return get_hw_module_verison() == "esp32s2"


def get_device_root_folder():
    return "/"


def get_firmware_version():
    major = None
    minor = None
    patch = None
    commit = firmware_commit_data

    try:
        major = int(firmware_data[0])
        if len(firmware_data) > 1:
            minor = int(firmware_data[1])
        if len(firmware_data) > 2:
            patch = int(firmware_data[2])
    except:
        pass

    return (major, minor, patch, commit)


def get_reset_cause():
    """Returns device reset cause in integer format.
    Possible Values --> 0: PWRON_RESET, 1: HARD_RESET, 2: WDT_RESET, 3: DEEPSLEEP_RESET, 4: SOFT_RESET
    """
    return machine.reset_cause()


def get_device_id():
    """Returns a device id based on machine unique id in readable format and raw format"""
    # this seems to be the same with WiFi STA MAC given by WLAN().mac()[0]
    return (ubinascii.hexlify(machine.unique_id()).decode("utf-8"), machine.unique_id())


def _try_get_lora_mac_bytes(force_init_region=False):
    mac = None
    return mac


def get_lora_mac():
    """Returns a device id based on lora mac in readable format and in raw format"""
    return (None, None)


def set_defaults(
    heartbeat=False,
    wifi_on_boot=True,
    wdt_on_boot=False,
    wdt_on_boot_timeout_sec=120,
    bt_on_boot=False,
):
    """Sets basic configuration of board"""
    # disable/enable heartbeat
    global wdt
    global wdt_timeout
    wdt = None

    import network

    wl = network.WLAN(network.STA_IF)
    wl.active(wifi_on_boot)

    if not wifi_on_boot:
        ap = network.WLAN(network.AP_IF)
        ap.active(False)

    try:
        from ubluetooth import BLE

        BLE().active(bt_on_boot)
    except:
        pass

    if wdt_on_boot:
        wdt = machine.WDT(timeout=(wdt_on_boot_timeout_sec * 1000))
        wdt_timeout = wdt_on_boot_timeout_sec


def initialize_led():
    if get_hw_module_verison() == "esp32s3":
        set_led_enabled(True, 47, 21)
    else:
        set_led_enabled(False)


def set_led_enabled(led_enabled, led_pin_vdd=47, led_pin_din=21):
    global _led_pin_pwr
    global _led_neopixel

    if not led_enabled:
        if _led_pin_pwr:
            _led_pin_pwr.off()
            _led_pin_pwr = None
        return

    try:
        _led_pin_pwr = machine.Pin(led_pin_vdd, machine.Pin.OUT)
    except Exception as e:
        logging.exception(e, "error setting up _led_pin_pwr")

    try:
        from neopixel import NeoPixel

        pin_din = machine.Pin(led_pin_din, machine.Pin.OUT)
        _led_neopixel = NeoPixel(pin_din, 1)
    except Exception as e:
        _led_neopixel = None
        logging.exception(e, "error setting up _led_neopixel")


def set_led_color(color):
    if not _led_neopixel or not _led_pin_pwr:
        return

    """ Sets led color """
    color_hex = None
    try:
        color_hex = color_map[color]
    except Exception as e:
        pass

    if color_hex is None:
        color_hex = color

    # try controlling led's power (for ESP32S2), if called to simple ESP32, it will through exception
    # thus it will ignore call.
    try:
        if color == 0:
            _led_pin_pwr.off()
            return

        _led_pin_pwr.on()
    except Exception as e:
        pass

    # try setting led's data (for ESP32S2), if called to simple ESP32, it will through exception
    # thus it will ignore call.
    try:
        _led_neopixel[0] = (
            (color_hex & 0xFF0000) >> 16,
            (color_hex & 0x00FF00) >> 8,
            (color_hex & 0x0000FF),
        )
        _led_neopixel.write()
    except Exception as e:
        pass


def blink_led(color):
    set_led_color(color)
    sleep_ms(100)
    set_led_color(0x000000)


def wdt_reset():
    if wdt:
        wdt.feed()


def get_heap_memory():
    """Returns heap memory in bytes (allocated, free)"""
    return (gc.mem_alloc(), gc.mem_free())


def get_free_flash(partition_path="/"):
    import uos

    f_bsize, _, f_blocks, f_bfree, _, _, _, _, _, _ = uos.statvfs(partition_path)
    freesize = f_bsize * f_bfree
    return freesize


def bq_charger_exec(bq_func, *args, **kwargs):
    from machine import SoftI2C, Pin

    status = False
    try:
        i2c = SoftI2C(scl=Pin(38), sda=Pin(39))  # cfg._UC_IO_I2C_SCL, cfg._UC_IO_I2C_SDA
        status = bq_func(i2c, 0x6B, *args, **kwargs)  # cfg._I2C_BQ_ADDRESS
    except Exception as e:
        logging.exception(e, "No BQ charger detected")
    return status


def bq_charger_identify(i2c, bq_addr):
    global _bq_charger_version
    if _bq_charger_version is not None:
        return _bq_charger_version

    try:
        val = _bq_read_u8(i2c, bq_addr, 0x38)
        if val & 0x18 == 0x18:
            _bq_charger_version = _CHARGER_VERSION_2
            return _bq_charger_version
    except Exception:
        pass

    try:
        # bq24297 part number is in REG0A[7:5] and equals 0b011.
        val = _bq_read_u8(i2c, bq_addr, 0x0A)
        if ((val >> 5) & 0x07) == 0x03:
            _bq_charger_version = _CHARGER_VERSION_1
            return _bq_charger_version
    except Exception as e:
        logging.exception(e, "No BQ charger detected")

    return None


def _bq_read_u8(i2c, bq_addr, reg):
    return int.from_bytes(i2c.readfrom_mem(bq_addr, reg, 1), "big")


def _bq_write_u8(i2c, bq_addr, reg, value):
    i2c.writeto_mem(bq_addr, reg, bytes((value & 0xFF,)))


def _bq_write_u16(i2c, bq_addr, reg, value):
    # BQ25622E uses consecutive little-endian register pairs (LSB at reg, MSB at reg+1).
    i2c.writeto_mem(bq_addr, reg, bytes((value & 0xFF, (value >> 8) & 0xFF)))


def _bq_read_u16(i2c, bq_addr, reg):
    raw = i2c.readfrom_mem(bq_addr, reg, 2)
    return (raw[1] << 8) | raw[0]


def _bq_twos_complement(val, bits):
    sign = 1 << (bits - 1)
    return val - (1 << bits) if (val & sign) else val


def _bq_decode_adc_u16_le(raw_u16, lsb_bit, width, signed, lsb_scale):
    raw = (raw_u16 >> lsb_bit) & ((1 << width) - 1)
    if signed:
        raw = _bq_twos_complement(raw, width)
    return raw * lsb_scale


def _bq_update_bits(i2c, bq_addr, reg, mask, value):
    curr = _bq_read_u8(i2c, bq_addr, reg)
    new_val = (curr & (~mask & 0xFF)) | (value & mask)
    _bq_write_u8(i2c, bq_addr, reg, new_val)
    return new_val


def _bq_get_version(i2c, bq_addr):
    version = bq_charger_identify(i2c, bq_addr)
    if version is None:
        return _CHARGER_VERSION_1
    return version


def _bq_set_vbat_mv(i2c, bq_addr, target_mv):
    version = _bq_get_version(i2c, bq_addr)

    # bq24297: REG04[7:2], 16mV step, 3504mV offset.
    if version == _CHARGER_VERSION_1:
        step_mv = 16
        base_mv = 3504
        code = int((target_mv - base_mv) / step_mv)
        if code < 0:
            code = 0
        if code > 0x3F:
            code = 0x3F
        _bq_update_bits(i2c, bq_addr, 0x04, 0xFC, code << 2)
        return

    # bq25622e: REG04[11:3], Little-endian register pair.
    accepted_mV = target_mv
    if accepted_mV < 3500:
        accepted_mV = 3500
    if accepted_mV > 4200:
        accepted_mV = 4200

    code = hex(accepted_mV)
    _bq_write_u16(i2c, bq_addr, 0x04, code << 3)


def bq_charger_setup(i2c, bq_addr):
    logging.debug("Battery: initialization")
    version = _bq_get_version(i2c, bq_addr)

    if version == _CHARGER_VERSION_1:
        # Disable watchdog to keep host register configuration active.
        _bq_update_bits(i2c, bq_addr, 0x05, 0x30, 0x00)

        # Preserve the previous bq24297 fast-charge current default.
        _bq_write_u8(i2c, bq_addr, 0x02, 0x20)
    else:
        REG0x16_Charger_Control_1 = 0x16
        # DISABLE WATCHDOG or else current will be halved every 50s!!!!!!!!!
        _bq_write_u8(i2c, bq_addr, REG0x16_Charger_Control_1, 0xA0)

        _bq_write_u16(i2c, bq_addr, 0x02, 0x0100)

        # Enable ADC (by default it is disabled: 0x30)
        REG0x26_ADC_Control = 0x26
        _bq_write_u8(i2c, bq_addr, REG0x26_ADC_Control, 0x80)


def bq_charger_set_max_charge_3950_mv(i2c, bq_addr):
    logging.debug("Battery: max charge 3952mV")
    _bq_set_vbat_mv(i2c, bq_addr, 3952)


def bq_charger_set_max_charge_4200_mv(i2c, bq_addr):
    logging.debug("Battery: max charge 4208mV")
    _bq_set_vbat_mv(i2c, bq_addr, 4208)


def bq_charger_set_charging_on(i2c, bq_addr):
    if _bq_get_version(i2c, bq_addr) != _CHARGER_VERSION_2:
        logging.debug("Battery: settings charge on")
        _bq_update_bits(i2c, bq_addr, 0x01, 0x10, 0x10)
    else:
        logging.debug("Battery: settings charge on")
        _bq_update_bits(i2c, bq_addr, 0x16, 0x20, 0x20)


def bq_charger_set_charging_off(i2c, bq_addr):
    if _bq_get_version(i2c, bq_addr) != _CHARGER_VERSION_2:
        logging.debug("Battery: settings charge off")
        _bq_update_bits(i2c, bq_addr, 0x01, 0x10, 0x00)
    else:
        logging.debug("Battery: settings charge off")
        _bq_update_bits(i2c, bq_addr, 0x16, 0x20, 0x00)


def bq_charger_get_is_charging_on(i2c, bq_addr):
    if _bq_get_version(i2c, bq_addr) != _CHARGER_VERSION_2:
        val = _bq_read_u8(i2c, bq_addr, 0x01)
        logging.debug("BQ charger is charging on: {}".format(hex(val)))
        return (val & 0x10) > 0
    else:
        val = _bq_read_u8(i2c, bq_addr, 0x16)
        logging.debug("BQ charger is charging on: {}".format(hex(val)))
        return (val & 0x20) > 0


def bq_charger_get_is_charging(i2c, bq_addr):
    if _bq_get_version(i2c, bq_addr) != _CHARGER_VERSION_2:
        val = _bq_read_u8(i2c, bq_addr, 0x08)
        logging.debug("BQ charger state: {}".format(hex(val)))
        is_charging = (val & 0x30) > 0
        return is_charging
    else:
        REG0x1E_Charger_Status_1 = 0x1E
        val = _bq_read_u8(i2c, bq_addr, REG0x1E_Charger_Status_1)
        logging.debug("BQ charger state: {}".format(hex(val)))
        return (val & 0x18) > 0


def bq_charger_set_hiz_mode_on(i2c, bq_addr):
    if _bq_get_version(i2c, bq_addr) != _CHARGER_VERSION_2:
        logging.debug("Battery: settings Hi-Z mode on")
        _bq_update_bits(i2c, bq_addr, 0x00, 0x80, 0x80)
    else:
        logging.debug("Battery: settings Hi-Z mode on")
        _bq_update_bits(i2c, bq_addr, 0x16, 0x10, 0x10)


def bq_charger_set_hiz_mode_off(i2c, bq_addr):
    if _bq_get_version(i2c, bq_addr) != _CHARGER_VERSION_2:
        logging.debug("Battery: settings Hi-Z mode off")
        _bq_update_bits(i2c, bq_addr, 0x00, 0x80, 0x00)
    else:
        logging.debug("Battery: settings Hi-Z mode off")
        _bq_update_bits(i2c, bq_addr, 0x16, 0x10, 0x00)


def bq_charger_get_regs(i2c, bq_addr):
    version = _bq_get_version(i2c, bq_addr)
    regs = []
    max_reg = 0x0C if version == _CHARGER_VERSION_2 else 0x08
    for i in range(0, max_reg + 1):
        v = i2c.readfrom_mem(bq_addr, i, 1)
        regs.append(v)

    return regs


def bq_charger_set_regs(i2c, bq_addr, regs):
    for i in range(0, len(regs)):
        i2c.writeto_mem(bq_addr, i, regs[i])


def bq_charger_is_on_external_power(i2c, bq_addr):
    if _bq_get_version(i2c, bq_addr) != _CHARGER_VERSION_2:
        val = _bq_read_u8(i2c, bq_addr, 0x08)
        logging.debug("BQ charger state: {}".format(hex(val)))
        power_good = (val & 0x4) > 0
        # is_charging = True  # this is the proper, though for some reason it does not work: (int.from_bytes(val, "big") & 0x30) > 0
        is_charging = (val & 0x30) > 0
        return is_charging and power_good
    else:
        REG0x1E_Charger_Status_1 = 0x1E
        val = _bq_read_u8(i2c, bq_addr, REG0x1E_Charger_Status_1)
        logging.debug("BQ charger state: {}".format(hex(val)))
        return val & 0x18 > 0


def bq_charger_get_ibus_adc(i2c, bq_addr):
    if _bq_get_version(i2c, bq_addr) != _CHARGER_VERSION_2:
        return None
    # REG0x28/0x29: bits[15:1], signed, 2mA/LSB.
    raw = _bq_read_u16(i2c, bq_addr, 0x28)
    return _bq_decode_adc_u16_le(raw, lsb_bit=1, width=15, signed=True, lsb_scale=2.0)


def bq_charger_get_ibat_adc(i2c, bq_addr):
    if _bq_get_version(i2c, bq_addr) != _CHARGER_VERSION_2:
        return None
    # REG0x2A/0x2B: bits[15:2], signed, 4mA/LSB.
    raw = _bq_read_u16(i2c, bq_addr, 0x2A)
    return _bq_decode_adc_u16_le(raw, lsb_bit=2, width=14, signed=True, lsb_scale=4.0)


def bq_charger_get_vbus_adc(i2c, bq_addr):
    if _bq_get_version(i2c, bq_addr) != _CHARGER_VERSION_2:
        return None
    # REG0x2C/0x2D: bits[14:2], unsigned, 3.97mV/LSB.
    raw = _bq_read_u16(i2c, bq_addr, 0x2C)
    return _bq_decode_adc_u16_le(raw, lsb_bit=2, width=13, signed=False, lsb_scale=3.97)


def bq_charger_get_vbat_adc(i2c, bq_addr):
    if _bq_get_version(i2c, bq_addr) != _CHARGER_VERSION_2:
        return None
    # REG0x30/0x31: bits[12:1], unsigned, 1.99mV/LSB.
    raw = _bq_read_u16(i2c, bq_addr, 0x30)
    return _bq_decode_adc_u16_le(raw, lsb_bit=1, width=12, signed=False, lsb_scale=1.99)


def bq_charger_get_vsys_adc(i2c, bq_addr):
    if _bq_get_version(i2c, bq_addr) != _CHARGER_VERSION_2:
        return None
    # REG0x32/0x33: bits[12:1], unsigned, 1.99mV/LSB.
    raw = _bq_read_u16(i2c, bq_addr, 0x32)
    return _bq_decode_adc_u16_le(raw, lsb_bit=1, width=12, signed=False, lsb_scale=1.99)


def initialize_main_version():
    global _main_version
    if _main_version is not None:
        return

    charger_version = bq_charger_exec(bq_charger_identify)
    if charger_version == _CHARGER_VERSION_1:
        _main_version = _MAIN_VERSION_V1
    elif charger_version == _CHARGER_VERSION_2:
        _main_version = _MAIN_VERSION_V2
    else:
        logging.error("Unknown charger version: {}".format(charger_version))
        _main_version = _MAIN_VERSION_V1


def get_main_version():
    global _main_version
    if _main_version is None:
        initialize_main_version()
    return _main_version
