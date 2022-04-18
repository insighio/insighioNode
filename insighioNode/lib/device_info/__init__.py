""" Module for getting various type of information from device """
import gc
import machine
import os
import sys
import ubinascii
import logging
import utime

wdt = None
_led_enabled = True
_led_pin_vdd = 37
_led_pin_din = 36

color_map = {}
color_map['blue'] = 0x0000F0
color_map['red'] = 0xF00000
color_map['yellow'] = 0xFFFF00
color_map['green'] = 0xF0F000
color_map['white'] = 0xFFFFFF
color_map['black'] = 0x000000


def is_esp32():
    return sys.platform == 'esp32' or 'esp8266'


def get_hw_module_verison():
    hw_info = str(os.uname())
    hw_info = hw_info.lower()
    if "esp32s2" in hw_info or "esp32-s2" in hw_info:
        return "esp32s2"
    elif "esp32" in hw_info:
        return "esp32"
    elif "esp8266" in hw_info:
        return "esp8266"
    return "other"


def supports_13bit_adc():
    return get_hw_module_verison() == "esp32s2"


if not is_esp32():
    import pycom
    _LORA_COMPATIBLE_PLATFORMS = ["LoPy", "FiPy", "LoPy4"]
    _LTE_COMPATIBLE_PLATFORMS = ["GPy", "FiPy"]


def get_device_root_folder():
    return '/' if is_esp32() else '/flash/'


def get_device_fw():
    """ Returns device fw (release, version) """
    return (os.uname()[2], os.uname()[3])


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
    try:
        from network import LoRa
        lora = None
        if force_init_region:
            lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)
            utime.sleep_ms(250)
        else:
            lora = LoRa(mode=LoRa.LORAWAN)
        mac = lora.mac()
    except Exception as e:
        logging.exception(e, "_try_get_lora_mac_bytes")

    return mac


def get_lora_mac():
    """ Returns a device id based on lora mac in readable format and in raw format """
    # valid only for lora compatible devices
    if not is_esp32() and sys.platform in _LORA_COMPATIBLE_PLATFORMS:
        mac = _try_get_lora_mac_bytes()

        if mac is None:
            mac = _try_get_lora_mac_bytes(True)

        if mac is not None:
            return (ubinascii.hexlify(mac).upper().decode('utf-8'), mac)

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
    wdt = None
    if is_esp32():
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
    else:
        try:
            import pycom
            pycom.heartbeat(heartbeat)
            # disable/enable wifi on boot
            pycom.wifi_on_boot(wifi_on_boot)
            # setup watchdog
            pycom.wdt_on_boot(wdt_on_boot)
            pycom.wdt_on_boot_timeout(wdt_on_boot_timeout_sec * 1000)  # reboots after X ms if no wdt.feed
            pycom.pybytes_on_boot(False)
            if(wdt_on_boot):
                wdt = machine.WDT(wdt_on_boot_timeout_sec * 1000)
        except Exception as e:
            pass

        # bluetooth disable if requested
        if not bt_on_boot:
            try:
                from network import Bluetooth
                Bluetooth().deinit()
            except Exception as e:
                pass
        # print("Bluetooth disabled")

    # garbage collection
    # TODO: review why the next line existed
    # gc.disable()


def set_led_enabled(led_enabled, led_pin_vdd=37, led_pin_din=36):
    global _led_enabled
    global _led_pin_vdd
    global _led_pin_din
    _led_enabled = led_enabled
    _led_pin_vdd = led_pin_vdd
    _led_pin_din = led_pin_din


def set_led_color(color):
    if not _led_enabled:
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
            pin_pwr = machine.Pin(_led_pin_vdd, machine.Pin.OUT)

            if color == 0:
                pin_pwr.off()
                return

            pin_pwr.on()
        except Exception as e:
            pass

        # try setting led's data (for ESP32S2), if called to simple ESP32, it will through exception
        # thus it will ignore call.
        try:
            from neopixel import NeoPixel
            pin_din = machine.Pin(_led_pin_din, machine.Pin.OUT)
            np = NeoPixel(pin_din, 1)

            np[0] = ((color_hex & 0xFF0000) >> 16, (color_hex & 0x00FF00) >> 8, (color_hex & 0x0000FF))
            np.write()
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
    if is_esp32():
        import esp32
        temp = esp32.raw_temperature()
    else:
        temp = machine.temperature()

    if unit_in_celsius:
        return (temp - 32) / 1.8
    else:
        return temp
