import network

import sys
from external import tinyweb

import device_info
import utime
import utils
import machine
import logging
import ure
import uasyncio

insighioSettings = None
wlan = None
app = None

def populateAvailableNets():
    available_nets = []
    logging.info("Initializing WiFi APs in range")
    wlan = None
    try:
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        nets = wlan.scan()
        wlan.active(False)
        nets = nets[:min(10, len(nets))]
    except Exception as e:
        logging.exception(e, "WiFi scan failed. Will provide empty SSID list")
        nets = []

    for net in nets:
        tmpObj = {}
        tmpObj["ssid"] = net[0].decode('UTF-8')
        tmpObj["rssi"] = net[3]
        available_nets.append(tmpObj)
    return available_nets

ssidCustom = "insigh-" + device_info.get_device_id()[0][-4:]
logging.info("SSID: " + ssidCustom)
logging.info("Original device id: " + device_info.get_device_id()[0])

class DevID():
    def get(self, data):
        logging.debug("[web-server][GET]: /devid")
        return {"id": device_info.get_device_id()[0]}, 200

class Settings():
    def get(self, data):
        global insighioSettings

        logging.debug("[web-server][GET]: /settings, params: [{}]".format(data))

        if not insighioSettings:
            insighioSettings = {}
            from www import configuration_handler
            try:
                insighioSettings = configuration_handler.get_config_values()
            except Exception as e:
                logging.exception(e, "Unable to retrieve old configuration")

            insighioSettings["hw_module"] = device_info.get_hw_module_verison()
            insighioSettings["board_mac"] = device_info.get_device_id()[0]

        if data.get("update_wifi_list") == '1':
            insighioSettings["wifiAvailableNets"] = populateAvailableNets()
        else:
            insighioSettings["wifiAvailableNets"] = []

        import ujson
        res = None
        try:
            res = ujson.dumps(insighioSettings, separators=(',', ':'))
        except:
            pass

        if res is None:
            try:
                res = ujson.dumps(insighioSettings)
            except:
                pass

        if res is not None:
            res_bytes = res.encode('utf-8')
            logging.debug("Settings: " + res)
        return res_bytes, 200

class RawWeightIdle():
    def get(self, data):
        logging.debug("[web-server][GET]: /raw-weight-idle")

        from sensors import hx711
        # if data and data["board"] == "old_esp_cyclefi":
        #     raw_val = hx711.get_reading_raw_idle_value(21, 22, 23, None)
        # else:
        raw_val = hx711.get_reading_raw_idle_value(4, 33, 12, 25)
        logging.debug("raw val about to return: " + str(raw_val))
        return {"raw": raw_val}, 200

# class RawWeight:
#     def get(self, data):
#         logging.debug("[web-server][GET]: /raw-weight")
#         from sensors import hx711
#         # if data and data["board"] == "old_esp_cyclefi":
#         #     raw_val = hx711.get_reading(21, 22, 23, None, None, None, True)
#         # else:
#         raw_val = hx711.get_reading(4, 33, 12, None, None, 25, True)
#         logging.debug("raw weight about to return: " + str(raw_val))
#         return {"raw": raw_val}, 200

class Config:
    def post(self, data):
        print("received config data: {}".format(data))
        logging.debug("about to save queryString: " + data["queryString"])

        import utils
        utils.writeToFile("/configLog", data["queryString"])

        try:
            from www import configuration_handler
            configuration_handler.apply_configuration(data["queryParams"])
            return {}, 200
        except Exception as e:
            logging.exception(e, "Error applying configuration")
            return {}, 500

async def server_loop(timeoutMs):
    purple = 0x4c004c
    device_info.set_led_color(purple)

    device_info.wdt_reset()

    # Main program loop until keyboard interrupt,
    try:
        start_time = utime.ticks_ms()
        end_time = start_time + timeoutMs
        # 5 minutes timeout if timeoutMs is > -1 and someone has connected to the wifi
        # self.wlan.isconnected() is confirmed to be NOT supported by firmware 1.18
        end_time_when_connected = start_time + 600000

        print("webserver: timeoutMs: {}, start_time: {}, end_time: {}, end_time_when_connected: {}".format(timeoutMs, start_time, end_time, end_time_when_connected))

        is_connected  = False
        keep_active_after_connection = False
        now = 0
        cnt = 0
        while True:
            is_connected = wlan.isconnected()
            # if is_connected:
            #     print("_", end='')
            # else:
            #     print(".", end='')

            if is_connected:
                keep_active_after_connection = True

            now = utime.ticks_ms()
            if (timeoutMs <= 0
                or (not keep_active_after_connection and now < end_time)
                    or (keep_active_after_connection and now < end_time_when_connected)):
               pass
            else:
                break

            if cnt % 10 == 0:
                device_info.wdt_reset()
                device_info.set_led_color(purple)
            else:
                if not is_connected:
                    device_info.set_led_color('black')

            cnt += 1
            yield from  uasyncio.sleep_ms(100)
    except KeyboardInterrupt:
        pass

def start(timeoutMs=120000):
    global wlan
    global app
    logging.info('\n\n** Init WLAN mode and WAP2')
    device_info.wdt_reset()
    wlan = network.WLAN(network.AP_IF)
    wlan.active(True)
    wlan.config(essid=ssidCustom)  # set the ESSID of the access point
    wlan.config(password='insighiodev')
    wlan.config(authmode=3)  # 3 -- WPA2-PSK
    wlan.config(max_clients=1)  # set how many clients can connect to the network

    device_info.wdt_reset()

    app = tinyweb.webserver(3, 6, 16, False)

    ############################################################################
    # callback registration
    # Index page
    @app.route('/')
    async def index(req, resp):
        # Just send file
        logging.debug("[web-server]: /")
        await resp.send_file('www/index.html')

    @app.route('/<fn>')
    async def httpfiles(req, resp, fn):
        # Just send file
        logging.debug("[web-server]: /{}".format(fn))
        await resp.send_file('www/{}'.format(fn))

    @app.route('/js/<fn>')
    async def files_js(req, resp, fn):
        logging.debug("[web-server]: /js/{}".format(fn))
        await resp.send_file('www/js/{}'.format(fn),
                             content_type='application/javascript')
        # await resp.send_file('www/js/{}.gz'.format(fn),
        #                      content_type='application/javascript',
        #                      content_encoding='gzip')

    # The same for css files - e.g.
    # Raw version of bootstrap.min.css is about 146k, compare to gzipped version - 20k
    @app.route('/css/<fn>')
    async def files_css(req, resp, fn):
        logging.debug("[web-server]: /css/{}".format(fn))
        await resp.send_file('www/css/{}.gz'.format(fn),
                             content_type='text/css',
                             content_encoding='gzip')

    # Images
    @app.route('/img/<fn>')
    async def files_images(req, resp, fn):
        logging.debug("[web-server]: /img/{}".format(fn))
        await resp.send_file('www/img/{}'.format(fn),
                             content_type='image/png')

    @app.route('/reboot', methods=['POST'])
    async def reboot(req, resp) :
        logging.debug("[web-server]: /reboot")
        resp.code = 200
        resp.add_access_control_headers()
        await resp._send_headers()
        await resp.send("")

        import machine
        import utime

        start_time = utime.ticks_ms()
        WAIT_UNTIL_REBOOT_MSEC = 3000
        while (utime.ticks_ms()-start_time < WAIT_UNTIL_REBOOT_MSEC):
            await uasyncio.sleep_ms(1000)
        machine.reset()

    app.add_resource(Settings, '/settings')
    app.add_resource(RawWeightIdle, '/raw-weight-idle')
    #app.add_resource(RawWeight, '/raw-weight')
    app.add_resource(Config, '/save-config')
    app.add_resource(DevID, '/devid')

    ##################################################################import network

    logging.info("Web UI started")
    app.run(host='192.168.4.1', port=80, loop_forever=False)

    try:
        app.loop.run_until_complete(server_loop(timeoutMs))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.exception(e, "web server exception")
    finally:
        app.loop.close()

    from sensors import hx711
    hx711.deinit_instance()

    device_info.set_led_color('black')

    try:
        app.shutdown()

    except Exception as e:
        logging.exception(e, "failed to shutdown web server properly")

    device_info.set_led_color('black')

    wlan.active(False)
    logging.info('Bye\n')
