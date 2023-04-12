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

device_info.initialize_led()
device_info.blink_led(0x252525)

demo_config_exists = False
try:
    import apps.demo_console.demo_config as cfg
    demo_config_exists = True
except Exception as e:
    logging.info("Device never configured.")
    pass

rstCause = device_info.get_reset_cause()
logging.info("Reset cause: " + str(rstCause))
if rstCause == 0 or rstCause == 1 or not demo_config_exists:
    logging.info("Starting Web server")
    gc.collect()
    import web_server
    web_server.start(120000 if demo_config_exists else -1)
    del sys.modules["web_server"]
    gc.collect()

import apps.demo_console.scenario as scenario
scenario.execute()
