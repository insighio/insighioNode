# setup init

import utime
import machine
import device_info
from . import demo_utils
import gc
import logging
from external.kpn_senml.senml_unit import SenmlUnits
from external.kpn_senml.senml_unit import SenmlSecondaryUnits

# The demo_config.py is autogenerated by webui
# it is the concatenation of the template configurations in template folder.
from . import demo_config as cfg

demo_utils.device_init()

# Operations for compatibility with older configurations
# default temperature unit: Celsius
if not hasattr(cfg, '_MEAS_TEMP_UNIT_IS_CELSIUS'):
    cfg._MEAS_TEMP_UNIT_IS_CELSIUS = True

start_time = utime.ticks_ms()

# initializations
device_info.set_defaults(heartbeat=False, wifi_on_boot=False, wdt_on_boot=False, wdt_on_boot_timeout_sec=cfg._WD_PERIOD, bt_on_boot=False)
device_info.set_led_color('blue')
_DEVICE_ID = device_info.get_device_id()[0]
cfg.device_id = _DEVICE_ID
logging.info("Device ID in readable form: {}".format(_DEVICE_ID))

# wachdog reset
demo_utils.watchdog_reset()

# get measurements
measurements = demo_utils.get_measurements(cfg)

logging.debug("Measurements before network: ")
logging.debug(str(measurements))

# connect to network
if cfg.network == "lora":
    from . import lora as network
elif cfg.network == "cellular":
    from . import cellular as network
    try:
        if cfg._MEAS_GPS_ENABLE:
            network.get_gps_position(cfg, measurements)  # may be it needs relocation
    except Exception as e:
        logging.exception(e, "GPS Exception:")

elif cfg.network == "wifi":
    from . import wifi as network

try:
    device_info.set_led_color('red')
    logging.info("Connecting to network over: " + cfg.network)
    connection_results = network.connect(cfg)
    measurements.update(connection_results)

    if ("status" in measurements) and (measurements["status"]["value"] is True):
        logging.info("Network [" + cfg.network + "] connected")
        # value no longer needed
        del measurements["status"]
        device_info.set_led_color('green')

        # create packet
        measurements["uptime"] = {"unit": SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND, "value": utime.ticks_ms() - start_time}
        message = network.create_message(cfg.device_id, measurements)

        # send packet
        network.send_message(cfg, message)

        # transport finished
        utime.sleep_ms(1000)
    else:
        logging.info("Network [" + cfg.network + "] not connected")

    # disconnect
    network.disconnect()
except Exception as e:
    logging.exception(e, "Main Exception:")

# deinit
device_info.set_led_color('white')

demo_utils.device_deinit()

# Finalization Actions
gc.collect()
logging.info("Getting into deep sleep...")

#############
### Time controlled by Web UI defined period
###
#machine.deepsleep(cfg._DEEP_SLEEP_PERIOD_SEC * 1000)


#############
### Time controlled by fixed timestamps 5:30 & 21:30
###

### RTC tuple format
###2021, 7, 8, 3, 16, 8, 45, 890003
### yy, MM, dd, DD, hh, mm, ss
from machine import RTC
time_tuple = RTC().datetime()
logging.info("current time: " + str(time_tuple))

MORNING_MEAS = 19800
EVENING_MEAS = 77400
DAY_SECONDS = 86400

def get_seconds_till_next_slot(current_seconds_of_day):
    # 5:30 => 19800 seconds
    if current_seconds_of_day < MORNING_MEAS:
        return MORNING_MEAS - current_seconds_of_day
    elif current_seconds_of_day < EVENING_MEAS:
        return EVENING_MEAS - current_seconds_of_day
    else:
        return DAY_SECONDS - current_seconds_of_day + MORNING_MEAS


seconds_of_day = (time_tuple[4] * 3600 + time_tuple[5] * 60 + time_tuple[6])
# seconds_of_day = (seconds_of_day + 3 * 3600) % DAY_SECONDS  # temp timezone fix

seconds_to_wait = get_seconds_till_next_slot(seconds_of_day)
MIN_WAIT_THRESHOLD = 900  # 15 minutes
if seconds_to_wait <= MIN_WAIT_THRESHOLD:
    seconds_to_wait = get_seconds_till_next_slot(seconds_of_day + seconds_to_wait + 1)  # go to next slot

RTC_DRIFT_CORRECTION = 1.011
logging.info("will wake up again in {} hours ({} seconds) <before correction>".format(seconds_to_wait / 3600, seconds_to_wait))

seconds_to_wait = int(seconds_to_wait * RTC_DRIFT_CORRECTION)

logging.info("will wake up again in {} hours ({} seconds) <after correction>".format(seconds_to_wait / 3600, seconds_to_wait))

machine.deepsleep(seconds_to_wait * 1000)  # +0.01% is RTC correction
