# main.py -- put your code here!
import sys
import device_info
import logging

if device_info.is_esp32():
    import machine
    machine.freq(240000000)

#logging.setLevel(logging.INFO)
logging.setLevel(logging.DEBUG)

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
if rstCause == 0 or rstCause == 1 or not demo_config_exists:
    logging.info("Starting Web server")
    from web_server import WebServer
    server = WebServer()
    server.start(50000)
    del server
    del sys.modules["web_server"]
    import gc
    gc.collect()

import apps.demo_console.demo_scenario
