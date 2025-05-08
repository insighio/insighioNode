# setup init

from utime import ticks_ms, gmtime, sleep_ms, time

start_time = ticks_ms()

import logging

from . import cfg
from . import message_buffer
from . import scenario_utils
from .dictionary_utils import set_value_int
import device_info
import gc
import machine
import utils

# Globals
timeDiffAfterNTP = None
measurement_run_start_timestamp = None


def getUptime(timeOffset=None):
    uptime = ticks_ms()
    if timeOffset is not None:
        uptime -= timeOffset
    return uptime - start_time


def now():
    from machine import RTC

    return RTC().datetime()


def isLightSleepScenario():
    backward_compatibility_on = cfg.get("_ALWAYS_ON_CONNECTION") is not None and cfg.get("_FORCE_ALWAYS_ON_CONNECTION") is not None

    if backward_compatibility_on:
        return (cfg.get("_ALWAYS_ON_CONNECTION") and device_info.bq_charger_exec(device_info.bq_charger_is_on_external_power)) or cfg.get(
            "_FORCE_ALWAYS_ON_CONNECTION"
        )
    else:
        return cfg.get("_LIGHT_SLEEP_ON") and (
            not cfg.get("_LIGHT_SLEEP_DEACTIVATE_ON_BATTERY") or device_info.bq_charger_exec(device_info.bq_charger_is_on_external_power)
        )


def execute():
    logging.debug("-> executeDeviceInitialization...")
    executeDeviceInitialization()
    logging.debug("-> executeMeasureAndUploadLoop...")
    executeMeasureAndUploadLoop()
    logging.debug("-> executeDeviceDeinitialization...")
    executeDeviceDeinitialization()
    logging.debug("-> executeTimingConfiguration...")
    executeTimingConfiguration()


def executeBootstrap(useExistingConfiguration=False):
    logging.info("Executing bootstrap procedure, expecting wifi: ")

    if not useExistingConfiguration:
        executeDeviceInitialization()
        cfg.set("_CONF_NETS", {"deviceHotspot": {"pwd": "12345678"}})

        cfg.set("_MAX_CONNECTION_ATTEMPT_TIME_SEC", 20)
        cfg.set("_MEAS_NETWORK_STAT_ENABLE", False)
        cfg.set("protocol", None)

    from . import wifi as network

    network.init(cfg)  # ?
    logging.debug("Network modules loaded")

    connection_results = network.connect(cfg)
    is_connected = "status" in connection_results

    _DEVICE_ID = device_info.get_device_id()[0]
    cfg.set("device_id", _DEVICE_ID)
    cfg.set("_SECRET_KEY", "000000000000000000000")

    headers = {"Authorization": cfg.get("_SECRET_KEY"), "accept": "application/json"}
    URL_base = "console.insigh.io"
    URL_PATH = "/things/bootstrap/{}".format(_DEVICE_ID)
    url = "{}://{}{}".format("http" if device_info.get_hw_module_verison() == "esp32wroom" else "https", URL_base, URL_PATH)

    try:
        from utils import httpclient

        client = httpclient.HttpClient(headers)
        response = client.get(url)
        if response and response.status_code == 200:
            try:
                resp = response.content.decode("utf-8")
                if resp.startswith('"') and resp.endswith('"'):
                    resp = resp[1:-1]
                logging.debug("new configuration: " + resp)
                import json

                obj = json.loads(resp)
                logging.debug("loaded object: {}".format(obj))
                iid = obj["mainflux_id"]
                ikey = obj["mainflux_key"]
                iData = (
                    obj["mainflux_channels"][0]["id"]
                    if obj["mainflux_channels"][0]["name"] == "data"
                    else obj["mainflux_channels"][1]["id"]
                )
                iControl = (
                    obj["mainflux_channels"][1]["id"]
                    if obj["mainflux_channels"][1]["name"] == "control"
                    else obj["mainflux_channels"][0]["id"]
                )

                keyValueDict = dict()
                if useExistingConfiguration:
                    # check if configuration needs change
                    try:
                        protocol_config = cfg.get_protocol_config()
                        if (
                            protocol_config.message_channel_id == iData
                            and protocol_config.control_channel_id == iControl
                            and protocol_config.thing_id == iid
                            and protocol_config.thing_token == ikey
                        ):
                            logging.info("Bootstrap: no change")
                            return False
                        logging.info("New device keys detected, about to apply configuration")
                        from www import stored_config_utils

                        keyValueDict = stored_config_utils.get_config_values(False, True)
                        logging.debug("loaded keys: {}".format(keyValueDict))
                    except Exception as e:
                        logging.exception(e, "error while processing bootstrap data")
                        return False
                else:
                    keyValueDict["selected-board"] = (
                        "old_esp_abb_panel" if device_info.get_hw_module_verison() == "esp32wroom" else "ins_esp_abb_panel"
                    )
                    keyValueDict["network"] = "wifi"
                    keyValueDict["wifi-ssid"] = list(frozenset([key for key in cfg.get("_CONF_NETS")]))[0]
                    keyValueDict["wifi-pass"] = cfg.get("_CONF_NETS")[keyValueDict["wifi-ssid"]]["pwd"]
                    keyValueDict["protocol"] = "mqtt"
                    keyValueDict["system-enable-ota"] = "True"

                keyValueDict["insighio-id"] = iid
                keyValueDict["insighio-key"] = ikey
                keyValueDict["insighio-channel"] = iData
                keyValueDict["insighio-control-channel"] = iControl

                from utils import configuration_handler

                if "content" in obj:
                    keyValueDictContent = configuration_handler.stringParamsToDict(obj["content"])
                    if keyValueDictContent is not None:
                        keyValueDict.update(keyValueDictContent)

                logging.info("about to apply: {}".format(keyValueDict))
                configuration_handler.notifyServerWithNewConfig()
                configuration_handler.apply_configuration(keyValueDict)

                logging.info("about to reboot to apply new config")
                machine.reset()

                return resp
            except Exception as e:
                logging.exception(e, " error reading response")
    except Exception as e:
        logging.exception(e, "error trying to execute bootstrap HTTP GET")

    network.deinit()

    utils.deleteModule("utils.httpclient")

    logging.error("failed to execute bootstrap")
    return False


def executeDeviceInitialization():
    # The demo_config.py is autogenerated by webui
    # it is the concatenation of the template configurations in template folder.
    scenario_utils.device_init()

    # Operations for compatibility with older configurations
    # default temperature unit: Celsius
    if cfg.get("_MEAS_TEMP_UNIT_IS_CELSIUS") is None:
        cfg.set("_MEAS_TEMP_UNIT_IS_CELSIUS", True)

    # initializations
    device_info.set_defaults(
        heartbeat=False,
        wifi_on_boot=False,
        wdt_on_boot=False,
        wdt_on_boot_timeout_sec=cfg.get("_WD_PERIOD"),
        bt_on_boot=False,
    )

    device_info.set_led_color("blue")
    _DEVICE_ID = device_info.get_device_id()[0]
    cfg.set("device_id", _DEVICE_ID)
    logging.info("Device ID in readable form: {}".format(_DEVICE_ID))

    # wachdog reset
    device_info.wdt_reset()


def determine_message_buffering_and_network_connection_necessity():
    buffered_upload_enabled = cfg.get("_BATCH_UPLOAD_MESSAGE_BUFFER") is not None
    execute_connection_procedure = not buffered_upload_enabled

    # if RTC is invalid, force network connection
    if buffered_upload_enabled and gmtime()[0] < 2021:
        execute_connection_procedure = True
    return (buffered_upload_enabled, execute_connection_procedure)


def executeMeasureAndUploadLoop():
    global measurement_run_start_timestamp
    (
        buffered_upload_enabled,
        execute_connection_procedure,
    ) = determine_message_buffering_and_network_connection_necessity()

    is_first_run = True
    # None: connection not executed
    # False: connection failed
    # True: connection succeded
    connectAndUploadCompletedWithoutErrors = None

    light_sleep_on = isLightSleepScenario()
    light_sleep_on_period = cfg.get("_ALWAYS_ON_PERIOD")
    if light_sleep_on_period is None:
        light_sleep_on_period = cfg.get("_DEEP_SLEEP_PERIOD_SEC")

    if light_sleep_on_period:
        try:
            # set keepalive timing used for heartbeats in open connections
            proto_cfg_instance = cfg.get_protocol_config()
            proto_cfg_instance.keepalive = int(light_sleep_on_period * 1.5) if light_sleep_on else 0

            if cfg.get("_MEAS_GPS_ENABLE"):
                proto_cfg_instance.keepalive += cfg.get("_MEAS_GPS_TIMEOUT")
            logging.debug("keepalive period: " + str(proto_cfg_instance.keepalive))
        except:
            logging.debug("no protocol info, ignoring keepalive configuration")

    measurement_run_start_timestamp = ticks_ms()

    while 1:
        logging.info("Light sleep activated: " + str(light_sleep_on))
        device_info.wdt_reset()
        measurement_run_start_timestamp = ticks_ms()

        # get measurements
        logging.debug("Starting getting measurements...")
        measurements = scenario_utils.get_measurements(cfg)
        if is_first_run:
            set_value_int(measurements, "reset_cause", device_info.get_reset_cause())

        logging.debug("printing measurements so far: " + str(measurements))

        # if the RTC is OK, timestamp message
        if buffered_upload_enabled and not execute_connection_procedure:
            uptime = getUptime(timeDiffAfterNTP)

            from external.kpn_senml.senml_unit import SenmlSecondaryUnits

            set_value_int(
                measurements,
                "uptime",
                uptime if is_first_run else (uptime - measurement_run_start_timestamp),
                SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND,
            )
            measurementStored = scenario_utils.storeMeasurement(measurements, False)
            # if always on, do run connect and upload
            # else run connection only if measurement was not stored
            execute_connection_procedure = True if light_sleep_on else not measurementStored

        # connect (if needed) and upload message
        if execute_connection_procedure:
            hasGPSFix = executeGetGPSPosition(measurements, light_sleep_on)
            if not hasGPSFix and cfg.get("_MEAS_GPS_NO_FIX_NO_UPLOAD"):
                connectAndUploadCompletedWithoutErrors = False
            else:
                connectAndUploadCompletedWithoutErrors = executeConnectAndUpload(cfg, measurements, is_first_run, light_sleep_on)

        if is_first_run:
            # if it is always on, first connect to the network and then start threads,
            # to allow them to immediatelly upload events
            scenario_utils.executePostConnectionOperations()
        is_first_run = False

        # if not connectAndUploadCompletedWithoutErrors or not light_sleep_on or not light_sleep_on_period:
        if not light_sleep_on or not light_sleep_on_period:
            # abort measurement while loop
            logging.info(
                "exiting measurement loop, light_sleep_on: {}, light_sleep_on_period: {}".format(light_sleep_on, light_sleep_on_period)
            )
            break

        logging.debug("[light sleep]: continuing execution")
        time_to_sleep = 1

        # if connection procedure was executed
        logging.debug(
            "[light sleep]: active: {}, connected: {}".format(
                cfg.get("_LIGHT_SLEEP_NETWORK_ACTIVE"), connectAndUploadCompletedWithoutErrors
            )
        )
        if cfg.get("_LIGHT_SLEEP_NETWORK_ACTIVE") == False and connectAndUploadCompletedWithoutErrors:
            logging.debug("[light sleep]: disconnecting")
            executeNetworkDisconnect()
            device_info.set_led_color("black")
        else:
            logging.debug("[light sleep]: ignoring disconnection")

        time_to_sleep = light_sleep_on_period * 1000 - (ticks_ms() - measurement_run_start_timestamp)
        time_to_sleep = time_to_sleep if time_to_sleep > 0 else 0
        logging.info("[light sleep]: sleeping for: " + str(time_to_sleep) + " milliseconds")
        gc.collect()

        start_sleep_time = ticks_ms()
        end_sleep_time = start_sleep_time + time_to_sleep
        while ticks_ms() < end_sleep_time:
            device_info.wdt_reset()
            sleep_ms(100)
        light_sleep_on = isLightSleepScenario()

    # if connection procedure was executed
    if connectAndUploadCompletedWithoutErrors is not None:
        executeNetworkDisconnect()


def executeGetGPSPosition(measurements, light_sleep_on):
    from . import gps

    return gps.get_gps_position(cfg, measurements, light_sleep_on)


def executeConnectAndUpload(cfg, measurements, is_first_run, light_sleep_on):
    global timeDiffAfterNTP
    from external.kpn_senml.senml_unit import SenmlSecondaryUnits

    logging.debug("loading network modules...")
    # connect to network
    selected_network = cfg.get("network")
    if selected_network == "lora":
        from . import lora as network
    elif selected_network == "wifi":
        from . import wifi as network
    elif selected_network == "cellular":
        from . import cellular as network
    elif selected_network == "satellite":
        from . import satellite as network

    try:
        network.init(cfg)
    except:
        logging.error("Unsupported network selection: [{}]".format(selected_network))
        return

    logging.debug("Network modules loaded")

    if selected_network == "cellular":
        network.prepareForConnectAndUpload()

    message_sent = False
    is_connected = False
    try:
        if network.is_connected():
            connection_results = {}
            is_connected = True
        else:
            if not is_first_run:
                device_info.set_led_color("red")
                network.disconnect()
            logging.info("Connecting to network over: " + selected_network)
            connection_results = network.connect(cfg)

            is_connected = "status" in connection_results and connection_results["status"]["value"] is True
            if "status" in connection_results:
                del connection_results["status"]

            # merge results
            measurements = dict(list(measurements.items()) + list(connection_results.items()))

            logging.info("Local time after data connection: {}".format(gmtime()))

            if is_connected:
                notifyConnected(network)
    except Exception as e:
        is_connected = False
        connection_results = {}
        logging.exception(e, "Exception during connection:")

    # update radio info
    if cfg.get("_MEAS_NETWORK_STAT_ENABLE"):
        network.updateSignalQuality(cfg, measurements)

    uptime = getUptime(timeDiffAfterNTP)

    set_value_int(
        measurements,
        "uptime",
        uptime if is_first_run else (uptime - measurement_run_start_timestamp),
        SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND,
    )

    try:
        if is_first_run:
            logging.debug("Network [" + selected_network + "] connected: " + str(is_connected))

        if is_connected:
            device_info.set_led_color("green")

            if is_first_run:
                executeDeviceConfigurationUpload(cfg, network)

            # create packet
            message_sent = network.send_message(cfg, network.create_message(cfg.get("device_id"), measurements))
            logging.info("measurement sent: {}".format(message_sent))
            message_buffer.parse_stored_measurements_and_upload(network)

            if cfg.get("_CHECK_FOR_OTA") and (not light_sleep_on or (light_sleep_on and is_first_run)):
                network.check_and_apply_ota(cfg)
        else:
            logging.debug("Network [" + selected_network + "] connected: False")
            device_info.set_led_color("red")

    except Exception as e:
        device_info.set_led_color("red")
        logging.exception(e, "Exception while sending data:")
        return False

    if selected_network == "cellular":
        network.prepareForGPS()

    if not message_sent:
        if cfg.get("_STORE_MEASUREMENT_IF_FAILED_CONNECTION"):
            logging.info("Message transmission failed, storing for later")
            scenario_utils.storeMeasurement(measurements, True)
        else:
            logging.info("Message transmission failed, ignoring message")

    # disconnect from network
    if not light_sleep_on or not is_connected:
        try:
            notifyDisconnected(network)
            network.disconnect()
            device_info.set_led_color("red")
        except Exception as e:
            logging.exception(e, "Exception during disconnection:")
    return message_sent


def executeNetworkDisconnect():
    selected_network = cfg.get("network")
    if selected_network == "lora":
        from . import lora as network
    elif selected_network == "wifi":
        from . import wifi as network
    elif selected_network == "cellular":
        from . import cellular as network
    elif selected_network == "satellite":
        from . import satellite as network
    network.deinit()


def executeDeviceStatisticsUpload(cfg, network):
    stats = {}

    try:
        import srcInfo

        stats["sw_branch"] = utils.get_var_from_module(srcInfo, "branch")
        stats["sw_commit"] = utils.get_var_from_module(srcInfo, "commit")
        stats["sw_custom_branch"] = utils.get_var_from_module(srcInfo, "custom_branch")
        stats["sw_custom_commit"] = utils.get_var_from_module(srcInfo, "custom_commit")
    except:
        logging.error("no srcInfo file found")

    stats["hw_version"] = device_info.get_hw_module_version()
    (major, minor, patch, commit) = device_info.get_firmware_version()
    stats["fw_v_major"] = major
    stats["fw_v_minor"] = minor
    stats["fw_v_patch"] = patch
    stats["fw_v_commit"] = commit
    stats["free_flash"] = device_info.get_free_flash()
    stats["free_data_flash"] = device_info.get_free_flash("/data")
    stats["serial"] = device_info.get_device_id()[0]
    try:
        import platform

        stats["platform"] = platform.platform()
    except:
        logging.info("Skipping platform info.")

    logging.info("Uploading device statistics.")
    return network.send_control_message(cfg, network.create_message(None, stats), "/stat")


def executeDeviceConfigurationUpload(cfg, network):
    # check for configuration pending for upload
    configUploadFileContent = utils.readFromFlagFile("/configLog")
    logging.debug("configUploadFileContent: {}".format(configUploadFileContent))
    if configUploadFileContent:
        logging.info("New configuration found, about to upload it.")
        # from utils import configuration_handler

        # configuration_handler.notifyServerWithNewConfig()

        message_sent = network.send_control_message(
            cfg,
            '[{"n":"config","vs":"' + configUploadFileContent + '"}]',
            "/configResponse",
        )
        if message_sent:
            utils.deleteFlagFile("/configLog")

        # whenever a new config log is uplaoded, upload also statistics for the device
    if configUploadFileContent or utils.existsFlagFile("/ota_applied_flag") or utils.existsFile("/ota_applied_flag"):
        message_sent = executeDeviceStatisticsUpload(cfg, network)
        if message_sent:
            utils.deleteFlagFile("/ota_applied_flag")
            utils.deleteFile("/ota_applied_flag")


def notifyConnected(network):
    # network.send_control_message(cfg, '{"mac":"' + cfg.device_id + '","connected":true}', "/connStat")
    pass


def notifyDisconnected(network):
    # network.send_control_message(cfg, '{"mac":"' + cfg.device_id + '","connected":false}', "/connStat")
    pass


def executeDeviceDeinitialization():
    scenario_utils.device_deinit()


def executeTimingConfiguration():
    if cfg.get("_DEEP_SLEEP_PERIOD_SEC") is not None:
        uptime = getUptime(timeDiffAfterNTP)
        logging.debug("end timestamp: " + str(uptime))
        logging.info("Getting into deep sleep...")
        sleep_period = cfg.get("_DEEP_SLEEP_PERIOD_SEC")
        sleep_period = sleep_period if sleep_period is not None else 600
        if sleep_period % 60 == 0:
            now_timestamp = time()
            next_tick = now_timestamp + sleep_period
            remaining = (sleep_period - next_tick % sleep_period) * 1000 - measurement_run_start_timestamp
            logging.debug(
                "now_timestamp: {}, next_tick: {}, uptime: {}, measurement_time: {}, remaining: {}".format(
                    now_timestamp,
                    next_tick,
                    uptime,
                    measurement_run_start_timestamp,
                    remaining,
                )
            )
            if remaining <= 0:
                remaining = sleep_period * 1000 - uptime
        else:
            remaining = sleep_period * 1000 - uptime
        if remaining < 0:
            remaining = 1000
        sleep_period = remaining % 86400000
        from math import floor

        logging.info(
            "will sleep for {} hours, {} minutes, {} seconds".format(
                floor(sleep_period / 1000 / 3600),
                floor(sleep_period / 1000 % 3600 / 60),
                floor(sleep_period / 1000 % 60),
            )
        )
        machine.deepsleep(sleep_period)
    elif cfg.get("_SCHEDULED_TIMESTAMP_A_SECOND") is not None and cfg.get("_SCHEDULED_TIMESTAMP_B_SECOND") is not None:
        ### RTC tuple format
        ###2021, 7, 8, 3, 16, 8, 45, 890003
        ### yy, MM, dd, DD, hh, mm, ss
        time_tuple = now()
        logging.info("current time: " + str(time_tuple))

        MORNING_MEAS = cfg.get("_SCHEDULED_TIMESTAMP_A_SECOND")
        EVENING_MEAS = cfg.get("_SCHEDULED_TIMESTAMP_B_SECOND")

        if MORNING_MEAS > EVENING_MEAS:
            MORNING_MEAS = cfg.get("_SCHEDULED_TIMESTAMP_B_SECOND")
            EVENING_MEAS = cfg.get("_SCHEDULED_TIMESTAMP_A_SECOND")

        DAY_SECONDS = 86400

        def get_seconds_till_next_slot(current_seconds_of_day):
            # 5:30 => 19800 seconds
            if current_seconds_of_day < MORNING_MEAS:
                return MORNING_MEAS - current_seconds_of_day
            elif current_seconds_of_day < EVENING_MEAS:
                return EVENING_MEAS - current_seconds_of_day
            else:
                return DAY_SECONDS - current_seconds_of_day + MORNING_MEAS

        timezone_offset = utils.getKeyValueInteger("tz_sec_offset")
        hour_offset = 0
        minute_offset = 0
        if timezone_offset:
            hour_offset = timezone_offset // 3600
            minute_offset = (timezone_offset % 3600) // 60

        seconds_of_day = (time_tuple[4] + hour_offset) * 3600 + (time_tuple[5] + minute_offset) * 60 + time_tuple[6]

        seconds_to_wait = get_seconds_till_next_slot(seconds_of_day)
        MIN_WAIT_THRESHOLD = 900  # 15 minutes
        if seconds_to_wait <= MIN_WAIT_THRESHOLD:
            seconds_to_wait = get_seconds_till_next_slot(seconds_of_day + seconds_to_wait + 1)  # go to next slot

        RTC_DRIFT_CORRECTION = 1.011
        logging.info("will wake up again in {} hours ({} seconds) <before correction>".format(seconds_to_wait / 3600, seconds_to_wait))

        seconds_to_wait = int(seconds_to_wait * RTC_DRIFT_CORRECTION)

        logging.info("will wake up again in {} hours ({} seconds) <after correction>".format(seconds_to_wait / 3600, seconds_to_wait))

        machine.deepsleep(seconds_to_wait * 1000)  # +0.01% is RTC correction
    else:
        logging.error("Timing neither periodic nor scheduled, will sleep for a minute")
        machine.deepsleep(60000)
