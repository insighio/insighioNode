# setup init

import utime
start_time = utime.ticks_ms()

import logging
import machine
import device_info
from . import scenario_utils
import gc
import utils
from math import floor
from . import message_buffer
try:
    from . import demo_config as cfg
except Exception as e:
    cfg = type('', (), {})()
import _thread

# Globals
timeDiffAfterNTP = None
measurement_run_start_timestamp = None

def getUptime(timeOffset=None):
    uptime = utime.ticks_ms()
    if timeOffset is not None:
        uptime -= timeOffset
    return uptime

def now():
    from machine import RTC
    return RTC().datetime()

def isAlwaysOnScenario():
    return (scenario_utils.get_config("_ALWAYS_ON_CONNECTION") and device_info.bq_charger_exec(device_info.bq_charger_is_on_external_power)) or scenario_utils.get_config("_FORCE_ALWAYS_ON_CONNECTION")

def execute():
    executeDeviceInitialization()
    executeMeasureAndUploadLoop()
    executeDeviceDeinitialization()
    executeTimingConfiguration()

def executeDeviceInitialization():
    # The demo_config.py is autogenerated by webui
    # it is the concatenation of the template configurations in template folder.
    scenario_utils.device_init()

    # Operations for compatibility with older configurations
    # default temperature unit: Celsius
    if scenario_utils.get_config('_MEAS_TEMP_UNIT_IS_CELSIUS') is None:
        cfg._MEAS_TEMP_UNIT_IS_CELSIUS = True

    # initializations
    device_info.set_defaults(heartbeat=False, wifi_on_boot=False, wdt_on_boot=False, wdt_on_boot_timeout_sec=scenario_utils.get_config("_WD_PERIOD"), bt_on_boot=False)
    device_info.set_led_color('blue')
    _DEVICE_ID = device_info.get_device_id()[0]
    cfg.device_id = _DEVICE_ID
    logging.info("Device ID in readable form: {}".format(_DEVICE_ID))

    # wachdog reset
    scenario_utils.watchdog_reset()

def determine_message_buffering_and_network_connection_necessity():
    buffered_upload_enabled = scenario_utils.get_config("_BATCH_UPLOAD_MESSAGE_BUFFER") is not None
    execute_connection_procedure = not buffered_upload_enabled

    # if RTC is invalid, force network connection
    if buffered_upload_enabled and utime.gmtime()[0] < 2021:
        execute_connection_procedure = True
    return (buffered_upload_enabled, execute_connection_procedure)

def executeMeasureAndUploadLoop():
    global measurement_run_start_timestamp
    (buffered_upload_enabled, execute_connection_procedure) = determine_message_buffering_and_network_connection_necessity()

    is_first_run = True
    always_on = isAlwaysOnScenario()
    always_on_period = scenario_utils.get_config("_ALWAYS_ON_PERIOD")
    if always_on_period:
        try:
            # set keepalive timing used for heartbeats in open connections
            proto_cfg_instance = cfg.get_protocol_config()
            proto_cfg_instance.keepalive = int(always_on_period * 1.5) if always_on else 0

            if scenario_utils.get_config("_MEAS_GPS_ENABLE"):
                proto_cfg_instance.keepalive += scenario_utils.get_config("_MEAS_GPS_TIMEOUT")
            logging.debug("keepalive period: " + str(proto_cfg_instance.keepalive))
        except:
            logging.debug("no protocol info, ignoring keepalive configuration")

    always_on_start_timestamp = utime.ticks_ms()
    if not always_on: #or not RTCisValid():
    #     time_to_sleep = 5000 # check connection and upload messages every 5 seconds
    # else:
        time_to_sleep = scenario_utils.get_config("_DEEP_SLEEP_PERIOD_SEC") if scenario_utils.get_config("_DEEP_SLEEP_PERIOD_SEC") else 60
        time_to_sleep = time_to_sleep * 1000 - (utime.ticks_ms() - always_on_start_timestamp)
        time_to_sleep = time_to_sleep if time_to_sleep > 0 else 0

    while True:
        logging.info("Always on connection activated: " + str(always_on))
        always_on_start_timestamp = utime.ticks_ms()
        #measurements = {}
        device_info.wdt_reset()
        measurement_run_start_timestamp = utime.ticks_ms()

        # get measurements
        logging.debug("Starting getting measurements...")
        measurements = scenario_utils.get_measurements(cfg)
        if is_first_run:
            measurements["reset_cause"] = {"value": device_info.get_reset_cause()}

        logging.debug("printing measurements so far: " + str(measurements))

        # if the RTC is OK, timestamp message
        if buffered_upload_enabled and not execute_connection_procedure:
            measurementStored = scenario_utils.storeMeasurement(measurements, False)
            # if always on, do run connect and upload
            # else run connection only if measurement was not stored
            execute_connection_procedure = True if always_on else not measurementStored

        # connect (if needed) and upload message
        connectAndUploadCompletedWithoutErrors = False
        if execute_connection_procedure:
            hasGPSFix = executeGetGPSPosition(cfg, measurements, always_on)

            if not hasGPSFix and scenario_utils.get_config("_MEAS_GPS_NO_FIX_NO_UPLOAD"):
                connectAndUploadCompletedWithoutErrors = False
            else:
                connectAndUploadCompletedWithoutErrors = executeConnectAndUpload(cfg, measurements, is_first_run, always_on)

        #if not connectAndUploadCompletedWithoutErrors or not always_on or not always_on_period:
        if not always_on or not always_on_period:
            # abort measurement while loop
            break
        else:
            if is_first_run:
                # if it is always on, first connect to the network and then start threads,
                # to allow them to immediatelly upload events
                pass
            is_first_run = False
            time_to_sleep = always_on_period * 1000 - (utime.ticks_ms() - always_on_start_timestamp)
            time_to_sleep = time_to_sleep if time_to_sleep > 0 else 0
            logging.info("light sleeping for: " + str(time_to_sleep) + " milliseconds")
            gc.collect()

            start_sleep_time = utime.ticks_ms()
            end_sleep_time = start_sleep_time + time_to_sleep
            while utime.ticks_ms() < end_sleep_time:
                device_info.wdt_reset()
                utime.sleep_ms(1000)
            always_on = isAlwaysOnScenario()

def executeGetGPSPosition(cfg, measurements, always_on):
    try:
        if scenario_utils.get_config("_MEAS_GPS_ENABLE") and (not scenario_utils.get_config("_MEAS_GPS_ONLY_ON_BOOT") or (device_info.get_reset_cause() == 0 or device_info.get_reset_cause() == 1)):
            from . import cellular as network_gps
            network_gps.init(cfg)

            gps_status = network_gps.get_gps_position(cfg, measurements, always_on)

            #close modem after operation if it is not going to be used for connection
            if cfg.network != "cellular":
                network_gps.disconnect()

            return gps_status
    except Exception as e:
        logging.exception(e, "GPS Exception:")
        return False

def executeConnectAndUpload(cfg, measurements, is_first_run, always_on):
    global timeDiffAfterNTP
    from external.kpn_senml.senml_unit import SenmlSecondaryUnits

    logging.debug("loading network modules...")
    # connect to network
    if cfg.network == "lora":
        from . import lora as network
    elif cfg.network == "wifi":
        from . import wifi as network
    elif cfg.network == "cellular":
        from . import cellular as network
    elif cfg.network == "satellite":
        from . import satellite as network

    network.init(cfg)
    logging.debug("Network modules loaded")

    if cfg.network == "cellular":
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
            logging.info("Connecting to network over: " + cfg.network)
            connection_results = network.connect(cfg)

            is_connected = "status" in connection_results and connection_results["status"]["value"] is True
            if "status" in connection_results:
                del connection_results["status"]

            logging.info("Local time after data connection: {}".format(utime.gmtime()))

            if is_connected:
                notifyConnected(network)
    except Exception as e:
        is_connected = False
        connection_results = {}
        logging.exception(e, "Exception during connection:")

    # update radio info
    if scenario_utils.get_config("_MEAS_NETWORK_STAT_ENABLE"):
        network.updateSignalQuality(cfg, measurements)

    try:
        if is_first_run:
            logging.debug("Network [" + cfg.network + "] connected: " + str(is_connected))

        if is_connected:
            device_info.set_led_color("green")

            if is_first_run:
                executeDeviceConfigurationUpload(cfg, network)

            # create packet
            uptime = getUptime(timeDiffAfterNTP)
            measurements["uptime"] = {"unit": SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND, "value": uptime if is_first_run else (uptime - measurement_run_start_timestamp)}
            message_sent = network.send_message(cfg, network.create_message(cfg.device_id, measurements))
            logging.info("measurement sent: {}".format(message_sent))
            message_buffer.parse_stored_measurements_and_upload(network)

            if not always_on or (always_on and is_first_run):
                network.check_and_apply_ota(cfg)
        else:
            logging.debug("Network [" + cfg.network + "] connected: False")
            device_info.set_led_color("red")

    except Exception as e:
        device_info.set_led_color("red")
        logging.exception(e, "Exception while sending data:")
        return False

    if cfg.network == "cellular":
        network.prepareForGPS()

    if not message_sent:
        logging.info("Message transmission failed, storing for later")
        if scenario_utils.get_config("_STORE_MEASUREMENT_IF_FAILED_CONNECTION"):
            scenario_utils.storeMeasurement(measurements, True)

    # disconnect from network
    if not always_on or not is_connected:
        try:
            notifyDisconnected(network)
            network.disconnect()
            device_info.set_led_color("red")
        except Exception as e:
            logging.exception(e, "Exception during disconenction:")
    return message_sent

def get_var_from_module(module, key):
    return getattr(module, key) if hasattr(module, key) else None

def executeDeviceStatisticsUpload(cfg, network):
    stats = {}

    try:
        import srcInfo
        stats["sw_branch"] = get_var_from_module(srcInfo, "branch")
        stats["sw_commit"] = get_var_from_module(srcInfo, "commit")
        stats["sw_custom_branch"] = get_var_from_module(srcInfo, "custom_branch")
        stats["sw_custom_commit"] = get_var_from_module(srcInfo, "custom_commit")
    except:
        logging.error("no srcInfo file found")

    stats["hw_version"] = device_info.get_hw_module_verison()
    (major, minor, patch, commit)  = device_info.get_firmware_version()
    stats["fw_v_major"] = major
    stats["fw_v_minor"] = minor
    stats["fw_v_patch"] = patch
    stats["fw_v_commit"] = commit
    stats["free_flash"] = device_info.get_free_flash()
    stats["serial"] = device_info.get_device_id()[0]
    try:
        import platform
        stats["platform"]=platform.platform()
    except:
        logging.info("Skipping platform info.")

    logging.info("Uploading device statistics.")
    return network.send_control_message(cfg, network.create_message(None, stats), "/stat")

def executeDeviceConfigurationUpload(cfg, network):
    # check for configuration pending for upload
    configUploadFileContent = utils.readFromFile("/configLog")
    if configUploadFileContent:
        logging.info("New configuration found, about to upload it.")
        message_sent = network.send_control_message(cfg, '[{"n":"config","vs":"' + configUploadFileContent +'"}]', "/configResponse")
        if message_sent:
            utils.deleteFile("/configLog")

        # whenever a new config log is uplaoded, upload also statistics for the device
    if configUploadFileContent or utils.existsFile('/ota_applied_flag'):
        message_sent = executeDeviceStatisticsUpload(cfg, network)
        if message_sent:
            utils.deleteFile('/ota_applied_flag')

def notifyConnected(network):
    #network.send_control_message(cfg, '{"mac":"' + cfg.device_id + '","connected":true}', "/connStat")
    pass

def notifyDisconnected(network):
    #network.send_control_message(cfg, '{"mac":"' + cfg.device_id + '","connected":false}', "/connStat")
    pass

def executeDeviceDeinitialization():
    scenario_utils.device_deinit()

    # connect to network
    if cfg.network == "lora":
        from . import lora as network
    elif cfg.network == "wifi":
        from . import wifi as network
    elif cfg.network == "cellular":
        from . import cellular as network
    elif cfg.network == "satellite":
        from . import satellite as network

    network.deinit()

def executeTimingConfiguration():
    if(scenario_utils.get_config("_DEEP_SLEEP_PERIOD_SEC") is not None):
        uptime = getUptime(timeDiffAfterNTP)
        logging.debug('end timestamp: '+str(uptime))
        logging.info('Getting into deep sleep...')
        sleep_period = scenario_utils.get_config("_DEEP_SLEEP_PERIOD_SEC")
        sleep_period = sleep_period if sleep_period is not None else 600
        if sleep_period % 60 == 0:
        	now_timestamp = utime.time()
        	next_tick = now_timestamp + sleep_period
        	remaining = (sleep_period - next_tick % sleep_period) * 1000 - measurement_run_start_timestamp
        	logging.debug('now_timestamp: {}, next_tick: {}, uptime: {}, measurement_time: {}, remaining: {}'.format(now_timestamp, next_tick, uptime, measurement_run_start_timestamp, remaining))
        	if remaining <= 0:
        		remaining = sleep_period * 1000 - uptime
        else:
        	remaining = sleep_period * 1000 - uptime
        if remaining < 0:
        	remaining = 1000
        sleep_period = remaining % 86400000
        from math import floor
        logging.info('will sleep for {} hours, {} minutes, {} seconds'.format(floor(sleep_period/1000/3600),floor(sleep_period/1000%3600/60),floor(sleep_period/1000%60)))
        machine.deepsleep(sleep_period)
    elif(scenario_utils.get_config("_SCHEDULED_TIMESTAMP_A_SECOND") is not None and scenario_utils.get_config("_SCHEDULED_TIMESTAMP_B_SECOND") is not None):
        ### RTC tuple format
        ###2021, 7, 8, 3, 16, 8, 45, 890003
        ### yy, MM, dd, DD, hh, mm, ss
        time_tuple = now()
        logging.info("current time: " + str(time_tuple))

        MORNING_MEAS = scenario_utils.get_config("_SCHEDULED_TIMESTAMP_A_SECOND")
        EVENING_MEAS = scenario_utils.get_config("_SCHEDULED_TIMESTAMP_B_SECOND")

        if MORNING_MEAS > EVENING_MEAS:
            MORNING_MEAS = scenario_utils.get_config("_SCHEDULED_TIMESTAMP_B_SECOND")
            EVENING_MEAS = scenario_utils.get_config("_SCHEDULED_TIMESTAMP_A_SECOND")

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

        seconds_of_day = ((time_tuple [4] + hour_offset) * 3600 + (time_tuple[5] + minute_offset) * 60 + time_tuple[6])

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
