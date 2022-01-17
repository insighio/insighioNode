# setup init

import utime
start_time = utime.ticks_ms()

import logging
import machine
import device_info
from . import demo_utils
import gc


def getUptime(timeOffset=None):
    uptime = utime.ticks_ms()
    if timeOffset is not None:
        uptime -= timeOffset
    if not device_info.is_esp32():
        uptime -= start_time
    return uptime


def execute():
    # The demo_config.py is autogenerated by webui
    # it is the concatenation of the template configurations in template folder.
    from . import demo_config as cfg
    demo_utils.device_init()

    # Operations for compatibility with older configurations
    # default temperature unit: Celsius
    if demo_utils.get_config('_MEAS_TEMP_UNIT_IS_CELSIUS') is None:
        cfg._MEAS_TEMP_UNIT_IS_CELSIUS = True

    # initializations
    device_info.set_defaults(heartbeat=False, wifi_on_boot=False, wdt_on_boot=False, wdt_on_boot_timeout_sec=demo_utils.get_config("_WD_PERIOD"), bt_on_boot=False)
    device_info.set_led_color('blue')
    _DEVICE_ID = device_info.get_device_id()[0]
    cfg.device_id = _DEVICE_ID
    logging.info("Device ID in readable form: {}".format(_DEVICE_ID))

    # wachdog reset
    demo_utils.watchdog_reset()

    timeDiffAfterNTP = None
    measurements = {}

    buffered_upload_enabled = demo_utils.get_config("_BATCH_UPLOAD_MESSAGE_BUFFER") is not None
    execute_connetion_procedure = not buffered_upload_enabled

    # if RTC is invalid, force network connection
    if buffered_upload_enabled and utime.gmtime()[0] < 2021:
        execute_connetion_procedure = True

    # get measurements
    measurements = demo_utils.get_measurements(cfg)

    logging.debug("printing measurements so far: " + str(measurements))

    # if the RTC is OK, timestamp message
    if buffered_upload_enabled and not execute_connetion_procedure:
        from . import message_buffer
        message_buffer.timestamp_measurements(measurements)
        execute_connetion_procedure = not message_buffer.store_measurement_if_needed(measurements)

    if execute_connetion_procedure:
        from external.kpn_senml.senml_unit import SenmlSecondaryUnits

        # connect to network
        if cfg.network == "lora":
            from . import lora as network
        elif cfg.network == "wifi":
            from . import wifi as network
        elif cfg.network == "cellular":
            from . import cellular as network

        try:
            if demo_utils.get_config("_MEAS_GPS_ENABLE"):
                from . import cellular as network_gps
                network_gps.get_gps_position(cfg, measurements)  # may be it needs relocation
        except Exception as e:
            logging.exception(e, "GPS Exception:")

        try:
            device_info.set_led_color('red')
            logging.info("Connecting to network over: " + cfg.network)
            connection_results = network.connect(cfg)
            if "timeDiffAfterNTP" in connection_results:
                timeDiffAfterNTP = connection_results["timeDiffAfterNTP"]
                del connection_results["timeDiffAfterNTP"]
            logging.info("Local time after data connection: {}".format(utime.gmtime()))
            measurements.update(connection_results)
        except Exception as e:
            logging.exception(e, "Exception during connection:")

        try:
            if ("status" in measurements) and (measurements["status"]["value"] is True):
                logging.info("Network [" + cfg.network + "] connected")
                # value no longer needed
                del measurements["status"]
                device_info.set_led_color('green')

                # create packet
                # utime.ticks_ms() is being reset after each deepsleep
                measurements["uptime"] = {"unit": SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND, "value": getUptime(timeDiffAfterNTP)}
                measurements["reset_cause"] = {"value": device_info.get_reset_cause()}
                message = network.create_message(cfg.device_id, measurements)

                # send packet
                network.send_message(cfg, message)

                if buffered_upload_enabled:
                    from . import message_buffer
                    message_buffer.parse_stored_measurements_and_upload(network)

                if demo_utils.get_config("_CHECK_FOR_OTA"):
                    network.checkAndApplyOTA(cfg)
            else:
                logging.info("Network [" + cfg.network + "] not connected")
        except Exception as e:
            logging.exception(e, "Exception while sending data:")

        try:
            # disconnect
            network.disconnect()
        except Exception as e:
            logging.exception(e, "Exception during disconenction:")

    # deinit
    device_info.set_led_color('white')

    demo_utils.device_deinit()

    # Finalization Actions
    gc.collect()

    if(demo_utils.get_config("_DEEP_SLEEP_PERIOD_SEC") is not None):
        # utime.ticks_ms() is being reset after each deepsleep
        uptime = getUptime(timeDiffAfterNTP)
        logging.debug("end timestamp: " + str(uptime))
        logging.info("Getting into deep sleep...")

        #############
        ### Time controlled by Web UI defined period
        ###
        sleep_period = demo_utils.get_config("_DEEP_SLEEP_PERIOD_SEC")
        sleep_period = sleep_period if sleep_period is not None else 600  # default 10 minute sleep
        remaining_milliseconds = sleep_period * 1000 - uptime
        if remaining_milliseconds < 0:
            remaining_milliseconds = 1000  # dummy wait 1 sec before waking up again
        sleep_period = remaining_milliseconds % 86400000  # if sleep period is longer than a day, keep the 24h period as max
        machine.deepsleep(sleep_period)
    elif(demo_utils.get_config("_SCHEDULED_TIMESTAMP_A_SECOND") is not None and demo_utils.get_config("_SCHEDULED_TIMESTAMP_B_SECOND") is not None):
        ### RTC tuple format
        ###2021, 7, 8, 3, 16, 8, 45, 890003
        ### yy, MM, dd, DD, hh, mm, ss
        from machine import RTC
        if device_info.is_esp32():
            time_tuple = RTC().datetime()
        else:
            time_tuple = RTC().now()
        logging.info("current time: " + str(time_tuple))

        MORNING_MEAS = demo_utils.get_config("_SCHEDULED_TIMESTAMP_A_SECOND")
        EVENING_MEAS = demo_utils.get_config("_SCHEDULED_TIMESTAMP_B_SECOND")

        if MORNING_MEAS > EVENING_MEAS:
            MORNING_MEAS = demo_utils.get_config("_SCHEDULED_TIMESTAMP_B_SECOND")
            EVENING_MEAS = demo_utils.get_config("_SCHEDULED_TIMESTAMP_A_SECOND")

        DAY_SECONDS = 86400

        def get_seconds_till_next_slot(current_seconds_of_day):
            # 5:30 => 19800 seconds
            if current_seconds_of_day < MORNING_MEAS:
                return MORNING_MEAS - current_seconds_of_day
            elif current_seconds_of_day < EVENING_MEAS:
                return EVENING_MEAS - current_seconds_of_day
            else:
                return DAY_SECONDS - current_seconds_of_day + MORNING_MEAS

        if device_info.is_esp32():
            seconds_of_day = (time_tuple[4] * 3600 + time_tuple[5] * 60 + time_tuple[6])
        else:
            seconds_of_day = (time_tuple[3] * 3600 + time_tuple[4] * 60 + time_tuple[5])
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
