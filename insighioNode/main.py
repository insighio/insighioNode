import sys

sys.path.clear()
sys.path.append("/lib")
sys.path.append(".frozen")
sys.path.append("")

from utime import ticks_ms
import logging

# logging.setLevel(logging.ERROR)
logging.setLevel(logging.DEBUG)
logging.debug("start timestamp: " + str(ticks_ms()))

# main.py -- put your code here!
import device_info

device_info.bq_charger_exec(device_info.bq_charger_setup)

device_info.initialize_led()
device_info.blink_led(0x252525)

# from apps.demo_console import scenario_pcnt_ulp
# scenario_pcnt_ulp.start()

cfg_instance = None
cfg_is_valid = False
try:
    from apps import cfg
    cfg_is_valid = cfg.init()
    cfg_instance = cfg.get_config()
except Exception as e:
    logging.exception(e, "Device never configured.")
    pass

if cfg_is_valid and cfg_instance:
    if cfg_instance.has("system-settings"):
        try:
            import json

            _system_settings = cfg_instance.get("system-settings")

            if _system_settings and "loggingLevel" in _system_settings:
                try:
                    logging.setLevelByName(_system_settings["loggingLevel"])
                except Exception as e:
                    logging.exception(e, "Error setting logging level")
                    pass
        except Exception as e:
            logging.exception(e, "Error loading system settings")

    if cfg_instance.has("meas-led-enabled"):
        try:
            device_info.set_led_enabled(cfg.meas-led-enabled)
        except:
            pass

rstCause = device_info.get_reset_cause()
logging.info("Reset cause: " + str(rstCause))

ENABLE_BOOTSTRAP = False
if rstCause == 0 or rstCause == 1 or not cfg_is_valid:
    if ENABLE_BOOTSTRAP and not cfg_is_valid:
        logging.info("Trying to get device auth from bootstrap")
        import apps.demo_console.scenario as scenario

        scenario.executeBootstrap()

    logging.info("Starting Web server")
    gc.collect()
    try:
        import web_server

        web_server.start(120000 if cfg_is_valid else -1)
        del sys.modules["web_server"]
    except:
        pass
    gc.collect()

# in case a temp config has been generated and webserver timeout occurs before
# deleting it
try:
    import uos

    uos.remove("/apps/demo_temp_config.py")
except:
    pass

import apps.demo_console.scenario as scenario

scenario.execute()
