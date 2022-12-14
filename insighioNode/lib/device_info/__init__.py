""" Module for getting various type of information from device """
import gc
import machine
import uos
import sys
import ubinascii
import logging
import utime

wdt = None
wdt_timeout = None

_led_enabled = True
_led_pin_vdd = 37
_led_pin_din = 36
_led_pin_pwr = None
_led_neopixel = None

color_map = {}
color_map['blue'] = 0x0000F0
color_map['red'] = 0xF00000
color_map['yellow'] = 0xFFFF00
color_map['green'] = 0xF0F000
color_map['white'] = 0xFFFFFF
color_map['black'] = 0x000000

uos_version_data = uos.uname()
machine_data = uos_version_data.machine
firmware_data = uos_version_data.version.split(" ")[0].split("-")
firmware_data[0] = firmware_data[0][1:] # "from 'v1.18' to '1.18'"

def is_wdt_enabled():
    return wdt is not None


def get_hw_module_verison():
    hw_info = machine_data
    hw_info = hw_info.lower()
    if "esp32s2" in hw_info or "esp32-s2" in hw_info:
        return "esp32s2"
    elif "esp32s3" in hw_info or "esp32-s3" in hw_info:
        return "esp32s3"
    elif "esp32" in hw_info:
        return "esp32"
    elif "esp8266" in hw_info:
        return "esp8266"
    return "other"


def supports_13bit_adc():
    return get_hw_module_verison() == "esp32s2"


def get_device_root_folder():
    return '/'


def get_firmware_version():
    major = None
    minor = None
    patch = None
    commit = None

    major_minor = firmware_data[0].split(".")

    try:
        major = int(major_minor[0])
        if len(major_minor) > 1:
            minor = int(major_minor[1])
        if len(firmware_data) > 1:
            patch = int(firmware_data[1])
        if len(firmware_data) > 2:
            commit = int(firmware_data[2])
    except:
        pass

    return (major, minor, patch, commit)


def get_reset_cause():
    """ Returns device reset cause in integer format.
       Possible Values --> 0: PWRON_RESET, 1: HARD_RESET, 2: WDT_RESET, 3: DEEPSLEEP_RESET, 4: SOFT_RESET
    """
    return machine.reset_cause()


def get_device_id():
    """ Returns a device id based on machine unique id in readable format and raw format """
    # this seems to be the same with WiFi STA MAC given by WLAN().mac()[0]
    return (ubinascii.hexlify(machine.unique_id()).decode('utf-8'), machine.unique_id())


def _try_get_lora_mac_bytes(force_init_region=False):
    mac = None
    return mac


def get_lora_mac():
    """ Returns a device id based on lora mac in readable format and in raw format """
    return (None, None)


def get_lte_ids():
    """ Returns a tuple of lte-related ids (imei,iccid,imsi,modem version, lte_fw_version) in readable format """
    # valid only for lte compatible devices
    if sys.platform in _LTE_COMPATIBLE_PLATFORMS:
        from network import LTE
        lte = LTE()
        # IMEI and ICCID are exposed directly by the Pycom LTE API, for others we need to parse AT commands
        imsi = lte.send_at_cmd('AT+CIMI').split('\r\n')[1].split(',')[-1]
        modem_version = lte.send_at_cmd('ATI1').split('\r\n')[1]
        lte_fw_version = lte.send_at_cmd('ATI1').split('\r\n')[2]
        return (lte.imei(), lte.iccid(), imsi, modem_version, lte_fw_version)
    else:
        return (None, None, None, None, None)


def set_defaults(heartbeat=False, wifi_on_boot=True, wdt_on_boot=False, wdt_on_boot_timeout_sec=120, bt_on_boot=False):
    """ Sets basic configuration of board """
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

    if(wdt_on_boot):
        wdt = machine.WDT(timeout=(wdt_on_boot_timeout_sec * 1000))
        wdt_timeout = wdt_on_boot_timeout_sec


    if get_hw_module_verison() == "esp32s3":
        set_led_enabled(True, 47, 21)
    elif get_hw_module_verison() == "esp32s2":
        set_led_enabled(True, 37, 36)
    else:
        set_led_enabled(False)


def set_led_enabled(led_enabled, led_pin_vdd=37, led_pin_din=36):
    global _led_pin_pwr
    global _led_neopixel

    try:
        _led_pin_pwr = machine.Pin(led_pin_vdd, machine.Pin.OUT)

        if not led_enabled:
            _led_pin_pwr.off()
            return
    except Exception as e:
        pass

    if not led_enabled:
        _led_neopixel = None
    else:
        try:
            from neopixel import NeoPixel
            pin_din = machine.Pin(led_pin_din, machine.Pin.OUT)
            _led_neopixel = NeoPixel(pin_din, 1)
        except Exception as e:
            _led_neopixel = None
            pass


def set_led_color(color):
    if not _led_neopixel:
        return

    """ Sets led color """
    color_hex = None
    try:
        color_hex = color_map[color]
    except Exception as e:
        pass

    if color_hex is None:
        color_hex = color

    if sys.platform != 'esp32':
        try:
            pycom.rgbled(color_hex)
        except Exception as e:
            pass
    else:
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
            _led_neopixel[0] = ((color_hex & 0xFF0000) >> 16, (color_hex & 0x00FF00) >> 8, (color_hex & 0x0000FF))
            _led_neopixel.write()
        except Exception as e:
            pass


def blink_led(color):
    device_info.set_led_color(color)
    utime.sleep_ms(100)
    device_info.set_led_color('black')


def wdt_reset():
    if wdt:
        wdt.feed()


def get_heap_memory():
    """ Returns heap memory in bytes (allocated, free) """
    return(gc.mem_alloc(), gc.mem_free())


def get_cpu_temp(unit_in_celsius=True):
    """ Returns CPU temperature in degrees of Celsius """
    temp = None
    import esp32
    temp = esp32.raw_temperature()

    if unit_in_celsius:
        return (temp - 32) / 1.8
    else:
        return temp

def get_free_flash():
    import uos
    (f_bsize, _, f_blocks, f_bfree, _, _, _, _, _, _) = uos.statvfs(get_device_root_folder())
    freesize = f_bsize * f_bfree
    return freesize

def bq_charger_exec(bq_func):
    from machine import SoftI2C, Pin
    status = False
    try:
        p_snsr = Pin(12, Pin.OUT) #cfg._UC_IO_SENSOR_GND_ON
        p_snsr.on()
        i2c = SoftI2C(scl=Pin(38), sda=Pin(39)) #cfg._UC_IO_I2C_SCL, cfg._UC_IO_I2C_SDA
        status = bq_func(i2c, 0x6B) #cfg._I2C_BQ_ADDRESS
    except Exception as e:
        logging.error("No BQ charger detected")
    try:
        p_snsr.off()
    except Exception as e:
        pass
    return status

def bq_charger_setup(i2c, bq_addr):
    i2c.writeto_mem(bq_addr, 5, b'\x84')
    i2c.writeto_mem(bq_addr, 0, b'\x22')

def bq_charger_set_charging_on(i2c, bq_addr):
    i2c.writeto_mem(bq_addr, 1, b'\x3B')

def bq_charger_set_charging_off(i2c, bq_addr):
    i2c.writeto_mem(bq_addr, 1, b'\x2B')

def bq_charger_is_on_external_power(i2c, bq_addr):
    val = i2c.readfrom_mem(bq_addr, 8, 1)
    logging.debug("BQ charger state: {}".format(ubinascii.hexlify(val)))
    power_good = (int.from_bytes(val, "big") & 0x4) > 0
    is_charging = True  # val & 0x30
    return is_charging and power_good
