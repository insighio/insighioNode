import network

import sys
from external import tinyweb

import device_info
from utime import ticks_ms
import logging
import uasyncio

insighioSettings = None
wlan = None
app = None

hw_version = device_info.get_hw_module_version()


def populateAvailableNets():
    available_nets = []
    logging.info("Initializing WiFi APs in range")
    wlan = None
    try:
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        nets = wlan.scan()
        wlan.active(False)
        nets = nets[: min(10, len(nets))]
    except Exception as e:
        logging.exception(e, "WiFi scan failed. Will provide empty SSID list")
        nets = []

    for net in nets:
        tmpObj = {}
        tmpObj["ssid"] = net[0].decode("UTF-8")
        tmpObj["rssi"] = net[3]
        available_nets.append(tmpObj)
    return available_nets


ssidCustom = "insigh-" + device_info.get_device_id()[0][-4:]
logging.info("SSID: " + ssidCustom)
logging.info("Original device id: " + device_info.get_device_id()[0])


class DevID:
    def get(self, data):
        logging.debug("[web-server][GET]: /devid")
        return {
            "id": device_info.get_device_id()[0],
            "hw_module": device_info.get_hw_module_version(),
        }, 200


class Settings:
    def get(self, data):
        global insighioSettings

        logging.debug("[web-server][GET]: /settings, params: [{}]".format(data))

        if not insighioSettings:
            insighioSettings = {}
            from utils import configuration_handler

            try:
                insighioSettings = configuration_handler.get_config_values(False)
            except Exception as e:
                logging.exception(e, "Unable to retrieve old configuration")

            insighioSettings["hw_module"] = hw_version
            insighioSettings["board_mac"] = device_info.get_device_id()[0]

        if data.get("update_wifi_list") == "1":
            insighioSettings["wifiAvailableNets"] = populateAvailableNets()
        else:
            insighioSettings["wifiAvailableNets"] = []

        import ujson

        res = None
        try:
            res = ujson.dumps(insighioSettings, separators=(",", ":"))
        except:
            pass

        if res is None:
            try:
                res = ujson.dumps(insighioSettings)
            except:
                pass

        if res is not None:
            res_bytes = res.encode("utf-8")
            logging.debug("Settings: " + res)
        return res_bytes, 200


class RawWeightIdle:
    def get(self, data):
        logging.debug("[web-server][GET]: /raw-weight-idle")

        from sensors import hx711

        txpower_save = None
        try:
            txpower_save = wlan.config("txpower")
            logging.debug("wlan.config(txpower): {}".format(txpower_save))
            wlan.config(txpower=5)
        except:
            logging.error("txpower not supported")

        if hw_version == device_info._CONST_ESP32 or hw_version == device_info._CONST_ESP32_WROOM:
            raw_val = hx711.get_reading(4, 33, 12, None, None, 25, True)
        elif hw_version == device_info._CONST_ESP32S3:
            raw_val = hx711.get_reading(5, 4, 8, None, None, 6, True)

        if txpower_save is not None:
            wlan.config(txpower=txpower_save)

        logging.debug("raw val about to return: " + str(raw_val))
        return {"raw": raw_val}, 200


class Config:
    def convert_params_to_string(self, data):
        queryString = ""
        try:
            for key in data["queryParams"].keys():
                if key in data["encodedParams"]:
                    queryString += "{}={}&".format(key, data["encodedParams"][key])
                else:
                    queryString += "{}={}&".format(key, data["queryParams"][key])
            if queryString != "":
                queryString = queryString[0:-1]
        except Exception as e:
            logging.exception(e, "convert_params_to_string")
        return queryString

    def post(self, data):
        print("received config data: {}".format(data))

        import utils

        logging.debug("about to save queryParams: {}".format(data["queryParams"]))
        utils.writeToFile("/configLog", self.convert_params_to_string(data))

        try:
            from utils import configuration_handler

            configuration_handler.apply_configuration(data["queryParams"])
            return {}, 200
        except Exception as e:
            logging.exception(e, "Error applying configuration")
            return {}, 500


class ConfigTemp:
    def post(self, data):
        print("[temp] received config data: {}".format(data))

        import utils

        try:
            from utils import configuration_handler

            configuration_handler.apply_configuration(data["queryParams"], "/apps/demo_temp_config.py")
            return {}, 200
        except Exception as e:
            logging.exception(e, "Error applying configuration")
            return {}, 500


class DeviceMeasurements:
    def get(self, data):
        try:
            from sensors import hx711

            hx711.deinit_instance()

            import sys

            try:
                del sys.modules["apps.demo_console.demo_config"]
            except:
                pass

            try:
                del sys.modules["apps.demo_temp_config"]
            except:
                pass

            try:
                del sys.modules["apps.demo_console.scenario_utils"]
            except:
                pass

            try:
                del sys.modules["apps.demo_console.scenario_advind_utils"]
            except:
                pass

            try:
                del sys.modules["apps.demo_console.message_buffer"]
            except:
                pass

            try:
                del sys.modules["apps.demo_console.dictionary_utils"]
            except:
                pass

            try:
                del sys.modules["apps.demo_console"]
            except:
                pass

            try:
                del sys.modules["apps"]
            except:
                pass

            # logging.debug("modules: {}".format(sys.modules))
            # logging.debug("globals: {}".format(globals()))

            from apps.demo_console import scenario_utils

            res = scenario_utils.get_measurements()

            # in case a temp config has been generated and webserver timesout before
            # deleting it
            try:
                import uos

                uos.rename("/apps/demo_temp_config.py", "/apps/demo_temp_config_web_config.py")
            except:
                pass

            return res, 200
        except Exception as e:
            logging.exception(e, "Error applying configuration")
            return {}, 500


class WiFiList:
    def get(self, data):
        result = {}
        result["wifiAvailableNets"] = populateAvailableNets()
        import ujson

        res = None
        try:
            res = ujson.dumps(result, separators=(",", ":"))
        except:
            pass

        if res is None:
            try:
                res = ujson.dumps(result)
            except:
                pass

        if res is not None:
            res_bytes = res.encode("utf-8")
            logging.debug("wifi list: " + res)
        return res_bytes, 200


async def server_loop(server_instance, timeoutMs):
    server_instance.run(host="192.168.4.1", port=80, loop_forever=False)
    logging.info("Web UI started")

    purple = 0x4C004C
    device_info.set_led_color(purple)

    device_info.wdt_reset()

    # Main program loop until keyboard interrupt,
    try:
        start_time = ticks_ms()
        end_time = start_time + timeoutMs
        # 5 minutes timeout if timeoutMs is > -1 and someone has connected to the wifi
        # self.wlan.isconnected() is confirmed to be NOT supported by firmware 1.18
        end_time_when_connected = start_time + 600000

        print(
            "webserver: timeoutMs: {}, start_time: {}, end_time: {}, end_time_when_connected: {}".format(
                timeoutMs, start_time, end_time, end_time_when_connected
            )
        )

        is_connected = False
        keep_active_after_connection = False
        now = 0
        cnt = 0
        while 1:
            is_connected = wlan.isconnected()
            # if is_connected:
            #     print("_", end='')
            # else:
            #     print(".", end='')

            if is_connected:
                keep_active_after_connection = True

            now = ticks_ms()
            if (
                timeoutMs <= 0
                or (not keep_active_after_connection and now < end_time)
                or (keep_active_after_connection and now < end_time_when_connected)
            ):
                pass
            else:
                break

            if cnt % 10 == 0:
                device_info.wdt_reset()
                device_info.set_led_color(purple)
            else:
                if not is_connected:
                    device_info.set_led_color("black")

            cnt += 1
            await uasyncio.sleep_ms(100)
    except KeyboardInterrupt:
        pass


def start(timeoutMs=120000):
    global wlan
    global app
    logging.info("\n\n** Init WLAN mode and WAP2")
    device_info.wdt_reset()
    wlan = network.WLAN(network.AP_IF)
    wlan.active(True)
    wlan.config(essid=ssidCustom)  # set the ESSID of the access point
    wlan.config(password="insighiodev")
    wlan.config(authmode=3)  # 3 -- WPA2-PSK
    wlan.config(max_clients=1)  # set how many clients can connect to the network

    device_info.wdt_reset()

    app = tinyweb.webserver(10, 6, 16, False)

    ############################################################################
    # callback registration
    # Index page
    @app.route("/")
    async def index(req, resp):
        # Just send file
        logging.debug("[web-server]: /")
        await resp.send_file("www/index.html")

    @app.route("/<fn>")
    async def httpfiles(req, resp, fn):
        # Just send file
        logging.debug("[web-server]: /{}".format(fn))
        await resp.send_file("www/{}".format(fn))

    @app.route("/js/<fn>")
    async def files_js(req, resp, fn):
        logging.debug("[web-server]: /js/{}".format(fn))
        await resp.send_file("www/js/{}".format(fn), content_type="application/javascript")
        # await resp.send_file('www/js/{}.gz'.format(fn),
        #                      content_type='application/javascript',
        #                      content_encoding='gzip')

    # The same for css files - e.g.
    # Raw version of bootstrap.min.css is about 146k, compare to gzipped version - 20k
    @app.route("/css/<fn>")
    async def files_css(req, resp, fn):
        logging.debug("[web-server]: /css/{}".format(fn))
        await resp.send_file("www/css/{}.gz".format(fn), content_type="text/css", content_encoding="gzip")

    # Images
    @app.route("/img/<fn>")
    async def files_images(req, resp, fn):
        logging.debug("[web-server]: /img/{}".format(fn))
        await resp.send_file("www/img/{}".format(fn), content_type="image/png")

    @app.route("/reboot", methods=["POST"])
    async def reboot(req, resp):
        logging.debug("[web-server]: /reboot")
        resp.code = 200
        resp.add_access_control_headers()
        await resp._send_headers()
        await resp.send("")

        import machine

        machine.reset()

    app.add_resource(Settings, "/settings")
    app.add_resource(RawWeightIdle, "/raw-weight-idle")
    # app.add_resource(RawWeight, '/raw-weight')
    app.add_resource(Config, "/save-config")
    app.add_resource(ConfigTemp, "/save-config-temp")
    app.add_resource(DevID, "/devid")
    app.add_resource(WiFiList, "/update_wifi_list")
    app.add_resource(DeviceMeasurements, "/device_measurements")

    ##################################################################import network

    try:
        uasyncio.run(server_loop(app, timeoutMs))
    except Exception as e:
        logging.exception(e, "web server exception")
    finally:
        uasyncio.get_running_loop().close()

    from sensors import hx711

    hx711.deinit_instance()

    device_info.set_led_color("black")

    try:
        app.shutdown()

    except Exception as e:
        logging.exception(e, "failed to shutdown web server properly")

    device_info.set_led_color("black")

    wlan.active(False)
    logging.info("Bye\n")
