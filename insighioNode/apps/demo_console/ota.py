import logging
import device_info
import utils
import gc

from . import cfg


def checkAndApply(client):
    if client is None:
        logging.debug("OTA check aborted, no active transfer client")
        return False

    pendingActions = get_pending_actions(client)

    if pendingActions is None or len(pendingActions) == 0:
        logging.info("No pending actions")
        return

    logging.debug("Pending actions: {}".format(pendingActions))

    # if message is byte array, decode it, or else ignore and proceed
    try:

        pendingActions = sorted(pendingActions, key=lambda d: d["createdAt"])
    except Exception as e:
        pass

    device_info.wdt_reset()

    for action in pendingActions:
        action_content = action.get("content")
        action_id = action.get("id")
        action_type = action.get("type")

        if not action_content:
            logging.debug("Skipping action with no content: {}".format(action_id))
            delete_action(client, action_id)
            continue

        if action_type == "config":
            applyDeviceConfiguration(client, action_id, action_content)
        elif action_type == "cmd":
            if action_content == "tare":
                import utils
                from sensors import hx711

                hw_version = device_info.get_hw_module_version()
                if hw_version == device_info._CONST_ESP32 or hw_version == device_info._CONST_ESP32_WROOM:
                    new_offset = hx711.get_reading(4, 33, 12, None, None, 25, True)
                elif hw_version == device_info._CONST_ESP32S3:
                    new_offset = hx711.get_reading(5, 4, 8, None, None, 6, True)

                cfg.set("_UC_IO_SCALE_OFFSET", new_offset)
                from utils import configuration_handler

                configuration_handler.updateConfigValue("_UC_IO_SCALE_OFFSET", new_offset)
                delete_action(client, action_id)
            elif action_content == "reboot":
                client.disconnect()
                delete_action(client, action_id)
                import machine

                machine.reset()
            else:
                delete_action(client, action_id)
        elif action_type == "ota":
            from external.kpn_senml.senml_pack_json import SenmlPackJson

            senmlMessage = SenmlPackJson("")
            senmlMessage.from_json(action_content)
            eventId = None
            fileId = None
            fileType = None
            fileSize = None
            for el in senmlMessage:
                name = str(el.name)
                if name == "e":
                    eventId = el.value
                elif name == "i":
                    fileId = el.value
                elif name == "t":
                    fileType = el.value
                elif name == "s":
                    fileSize = el.value
            # eventId ==0 => pending for installation
            if str(eventId) == "0" and fileId and fileType and fileSize:
                downloaded_file = downloadOTA(client, fileId, fileType, fileSize)
                if downloaded_file:
                    from . import apply_ota

                    applied = apply_ota.do_apply(downloaded_file)
                    if applied:
                        print("about to reset...")
                        sendOtaStatusMessage(client, fileId, True)
                        delete_action(client, action_id)
                        import utils

                        utils.clearCachedStates()
                        utils.writeToFlagFile("/ota_applied_flag", "done")

                        client.disconnect()

                        import machine

                        machine.reset()
                    else:
                        sendOtaStatusMessage(client, fileId, False, "can not apply")
                        delete_action(client, action_id)
                else:
                    sendOtaStatusMessage(client, fileId, False, "can not download")
        elif action_type == "partialConfig":
            # first clear non-modem based config request
            delete_action(client, action_id)

            try:
                from utils import configuration_handler

                keyValueDict = configuration_handler.stringParamsToDict(action_content)

                from utils import configuration_handler

                for key in keyValueDict:
                    configuration_handler.updateConfigValue(key, keyValueDict[key])

                client.disconnect()

                import machine

                machine.reset()
            except Exception as e:
                logging.exception(e, "unable to apply partial configuration")


def _get_http_scheme():
    return "http" if device_info.get_hw_module_verison() == "esp32wroom" else "https"


def _http_get_with_fallback(url, headers=None, saveToFile=None):
    """Performs a GET request, retrying over plain HTTP if the initial HTTPS attempt fails."""
    gc.collect()
    print("mem free: " + str(gc.mem_free()))

    from utils import httpclient

    use_https = url.startswith("https://")
    http_client = httpclient.HttpClient(headers) if headers else httpclient.HttpClient()

    response = None
    try:
        response = http_client.get(url, saveToFile=saveToFile) if saveToFile else http_client.get(url)
    except Exception as e:
        logging.exception(e, "error executing HTTP GET")

    if (not response or response.status_code != 200) and use_https:
        logging.info("request failed, retrying without HTTPS")
        fallback_url = url.replace("https://", "http://")
        response = http_client.get(fallback_url, saveToFile=saveToFile) if saveToFile else http_client.get(fallback_url)

    return response


def _modem_get_content_with_auth_header(client, url_path, query_params, tmp_file, timeout_ms=120000):
    """Downloads content from a control-channel endpoint via the modem's authenticated HTTP GET and returns it as a string."""
    protocol_config = cfg.get_protocol_config()
    return client.modem_instance.http_get_with_auth_header(
        "console.insigh.io",
        url_path + "?" + query_params,
        protocol_config.thing_token,
        timeout_ms,
    )


def _fetch_control_content(client, url_path, query_params, tmp_file, timeout_ms=120000):
    """Fetches content from a control-channel endpoint via modem or local HTTP client, stripping wrapping quotes."""
    protocol_config = cfg.get_protocol_config()

    if client.modem_based:
        content = _modem_get_content_with_auth_header(client, url_path, query_params, tmp_file, timeout_ms)
    else:
        content = None
        try:
            headers = {"Authorization": protocol_config.thing_token}
            url = "{}://{}{}?{}".format(_get_http_scheme(), "console.insigh.io", url_path, query_params)
            response = _http_get_with_fallback(url, headers)
            if response and response.status_code == 200:
                try:
                    content = response.content.decode("utf-8")
                except Exception as e:
                    logging.exception(e, "error reading response")
        except Exception as e:
            logging.exception(e, "unable to instantiate httpclient")
        finally:
            utils.deleteModule("utils.httpclient")

    if content:
        content = content.strip()
        if content.startswith('"') and content.endswith('"'):
            content = content[1:-1]
        logging.debug("content: |" + content + "|")

    return content


def hasEnoughFreeSpace(fileSize):
    import uos

    # for ESP32 uos.statvfs('/')
    f_bsize, _, f_blocks, f_bfree, _, _, _, _, _, _ = uos.statvfs(device_info.get_device_root_folder())
    freesize = f_bsize * f_bfree

    logging.debug("file size: {} vs free flash: {}".format(fileSize, freesize))
    return fileSize < freesize


# Event codes (e)
# 0: Pending
# 1: Applied
# 2: Failed
# 3: Canceled
def sendOtaStatusMessage(client, fileId, success, reason_measage=None):
    from external.kpn_senml.senml_pack_json import SenmlPackJson
    from external.kpn_senml.senml_record import SenmlRecord

    message = SenmlPackJson("")
    message.add(SenmlRecord("e", value=(1 if success else 2)))  # event id == 2 => failure
    message.add(SenmlRecord("i", value=fileId))
    if reason_measage is not None:
        message.add(SenmlRecord("m", value=reason_measage))

    client.send_control_packet(message.to_json(), "/ota")


def downloadOTA(client, fileId, fileType, fileSize):
    logging.info("About to download OTA package: " + fileId + fileType)

    if not hasEnoughFreeSpace(int(fileSize)):
        logging.error("Not enough space to download package")
        sendOtaStatusMessage(client, fileId, False, "not enough space")
        return None

    logging.debug("OTA size check passed")

    filename = device_info.get_device_root_folder() + fileId + fileType
    # http://<ip>/packages/download?fuid=<file-uid>&did=<device-id>&dk=<device-key>&cid=<control-channel-id>
    # TODO: fix support of redirections
    protocol_config = cfg.get_protocol_config()
    URL = "{}://{}/mf-rproxy/packages/download?fuid={}&did={}&dk={}&cid={}".format(
        _get_http_scheme(),
        protocol_config.server_ip,
        # "console.insigh.io",
        fileId,
        protocol_config.thing_id,
        protocol_config.thing_token,
        protocol_config.control_channel_id,
    )

    logging.debug("OTA URL: " + URL)

    if client.modem_based:
        file_downloaded, downloaded_size = client.modem_instance.http_get_file(URL, filename, 250000)
        if file_downloaded and int(downloaded_size) == int(fileSize):
            return filename

        logging.error(
            "file download failed, file_downloaded: {}, downloaded size: {}, expected file size: {}".format(
                file_downloaded, downloaded_size, fileSize
            )
        )
        return None
    else:
        try:
            response = _http_get_with_fallback(URL, saveToFile=filename)
            success_status = response and response.status_code == 200
        finally:
            utils.deleteModule("utils.httpclient")

        if success_status:
            logging.debug("HTTP file downloaded: " + filename)
            return filename
    return None


def applyDeviceConfiguration(client, configuration_id, configurationParameters):
    if configurationParameters is None:
        return

    from utils import configuration_handler

    keyValueDict = configuration_handler.stringParamsToDict(configurationParameters)

    urlDecodeComponentForKeys(keyValueDict)

    configuration_handler.apply_configuration(keyValueDict)
    delete_action(client, configuration_id)
    client.disconnect()
    import machine

    logging.info("about to reset to use new configuration")
    machine.reset()


# _MEAS_SDI12 = '<meas-sdi12>'
# _MEAS_MODBUS = '<meas-modbus>'
# _MEAS_ADC = '<meas-adc>'
# _MEAS_PULSECOUNTER = '<meas-pulseCounter>'
# _SYSTEM_SETTINGS = '<system-settings>'
def urlDecodeComponentForKeys(keyValueDict):
    from external.microUrllib import parse

    for key in keyValueDict:
        value = keyValueDict[key]

        if value and isinstance(value, str) and (value.startswith("%7B") or value.startswith("%5B")):
            try:
                value = value.replace("'", '"')  # TODO - temp fix because server processed the data, TO REVISIT!
                keyValueDict[key] = parse.unquote_to_bytes(value).decode()
                logging.debug("url decoded key: {} before value: {} after value: {}".format(key, value, keyValueDict[key]))
            except Exception as e:
                logging.exception(e, "unable to decode URL component for key: " + key)
        else:
            logging.debug("url decode ignored key: {} with value: {}".format(key, value))


################################################################
## Implementation of Pending actions API


# GET /device/pending-actions?id=<device-id>&channel=<control-channel>
def get_pending_actions(client):
    logging.info("About to check for pending actions")

    protocol_config = cfg.get_protocol_config()
    URL_PATH = "/mf-rproxy/device/pending-actions"
    URL_QUERY_PARAMS = "id={}&channel={}".format(protocol_config.thing_id, protocol_config.control_channel_id)

    actionsContent = _fetch_control_content(client, URL_PATH, URL_QUERY_PARAMS, "tmpactions")

    import json

    try:
        return json.loads(actionsContent)
    except Exception as e:
        logging.exception(e, "Failed to parse actions content: " + str(e))

    return None


# DELETE /device/pending-actions/:actionId?id=<device-id>&channel=<control-channel>
def delete_action(client, id):
    logging.info("About to delete action: " + str(id))

    protocol_config = cfg.get_protocol_config()
    URL_PATH = "/mf-rproxy/device/pending-actions/{}".format(id)
    URL_QUERY_PARAMS = "id={}&channel={}".format(protocol_config.thing_id, protocol_config.control_channel_id)

    if client.modem_based:
        # NOTE: modem client has no HTTP DELETE support, reuses the PUT-based content
        return client.modem_instance.http_put_with_auth_header(
            "console.insigh.io", "{}?{}".format(URL_PATH, URL_QUERY_PARAMS), protocol_config.thing_token, ""
        )
    try:
        from utils import httpclient

        headers = {"Authorization": protocol_config.thing_token}
        url = "{}://{}{}?{}".format(_get_http_scheme(), "console.insigh.io", URL_PATH, URL_QUERY_PARAMS)
        http_client = httpclient.HttpClient(headers)
        response = None
        try:
            logging.debug("sending HTTP DELETE request to URL: {}".format(url))
            response = http_client.delete(url)
        except Exception as e:
            logging.exception(e, "error executing HTTP DELETE")

        logging.debug(
            "response status code: {}, reason: {}".format(
                response.status_code if response else "No response", response.reason if response else "No response"
            )
        )

        return bool(response and response.status_code == 200)
    except Exception as e:
        logging.exception(e, "unable to instantiate httpclient")

    return False
