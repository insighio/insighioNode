import utime
import logging

#logging.setLevel(logging.INFO)
logging.setLevel(logging.DEBUG)
logging.debug("start timestamp: " + str(utime.ticks_ms()))

# main.py -- put your code here!
import sys
import device_info

import machine
if device_info.get_hw_module_verison() == "esp8266":
    machine.freq(160000000)
else:
    machine.freq(240000000)

if device_info.get_hw_module_verison() == "esp32s2":
    import _thread
    import time

    def testThread():
        while True:
            print(".", end='')
            utime.sleep_ms(500)

    _thread.start_new_thread(testThread, ())

demo_config_exists = False
try:
    import apps.demo_console.demo_config as cfg
    demo_config_exists = True
except Exception as e:
    sys.print_exception(e)
    logging.info("Device never configured.")
    pass

rstCause = device_info.get_reset_cause()
logging.info("Reset cause: " + str(rstCause))
if (rstCause == 0 or rstCause == 1 or not demo_config_exists) and device_info.get_hw_module_verison() != "esp32s2" and device_info.get_hw_module_verison() != "esp8266":
    logging.info("Starting Web server")
    from web_server import WebServer
    print(".", end='')
    server = WebServer()
    print(".", end='')
    server.start(60000 if demo_config_exists else -1)
    del server
    del sys.modules["web_server"]
    import gc
    gc.collect()

import apps.demo_console.demo_scenario as scenario
scenario.execute()
