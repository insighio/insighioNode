import sys
sys.path.clear()
sys.path.append('/lib')
sys.path.append('.frozen')
sys.path.append('')

import utime
import logging

#logging.setLevel(logging.ERROR)
logging.setLevel(logging.DEBUG)
logging.debug("start timestamp: " + str(utime.ticks_ms()))

# main.py -- put your code here!
import device_info
device_info.bq_charger_exec(device_info.bq_charger_setup)

device_info.set_defaults(heartbeat=False, wifi_on_boot=False, wdt_on_boot=True, wdt_on_boot_timeout_sec=120, bt_on_boot=False)

demo_config_exists = False
try:
    import apps.demo_console.demo_config as cfg
    demo_config_exists = True
except Exception as e:
    logging.info("Device never configured.")
    pass

rstCause = device_info.get_reset_cause()
logging.info("Reset cause: " + str(rstCause))
if (rstCause == 0 or rstCause == 1 or not demo_config_exists) and device_info.get_hw_module_verison() != "esp32s2" and device_info.get_hw_module_verison() != "esp8266":
    logging.info("Starting Web server")
    gc.collect()
    import web_server
    print(".", end='')
    print(".", end='')
    web_server.start(120000 if demo_config_exists else -1)
    import sys
    del sys.modules["web_server"]
    import gc
    gc.collect()

import apps.demo_console.scenario as scenario
scenario.execute()
