import logging
import device_info
import utils
import gc

from . import cfg


def checkAndApply(client):
    if client is None:
        logging.debug("OTA check aborted, no active transfer client")
        return False

    logging.info("Waiting for incoming control message (OTA)...")
    messageDict = client.get_control_message()

    if messageDict is None or messageDict["topic"] is None or messageDict["message"] is None:
        logging.info("No control message received")
        return

    topic = messageDict["topic"]
    message = messageDict["message"]
    # if message is byte array, decode it, or else ignore and proceed
    try:
        topic = topic.decode("utf-8")
    except Exception as e:
        pass
    try:
        message = message.decode("utf-8")
    except Exception as e:
        pass

    logging.debug("mqtt message received: " + str(message) + " in topic: " + str(topic))

    # if it is a device configuration with content
    if topic.endswith("/config"):
        # if modem based, clear message and ignore
        if client.modem_based:
            client.clear_retained(topic)
            checkAndApply(client)
            return

        # first clear non-modem based config request
        client.clear_retained(topic + "Request")
        applyDeviceConfiguration(client, message, topic)
    # if it is a configuration request without content
    elif topic.endswith("/configRequest") and message == "pending":
        if not client.modem_based:
            client.clear_retained(topic)
            checkAndApply(client)
            return

        # first clear non-modem based config request
        client.clear_retained(topic.replace("Request", ""))
        config_content = downloadDeviceConfigurationHTTP(client)

        applyDeviceConfiguration(client, config_content, topic)
    elif topic.endswith("/partialConfig"):
        # first clear non-modem based config request
        client.clear_retained(topic)

        try:
            from utils import configuration_handler

            keyValueDict = configuration_handler.stringParamsToDict(message)

            from utils import configuration_handler

            for key in keyValueDict:
                configuration_handler.updateConfigValue(key, keyValueDict[key])

            import machine

            machine.reset()
        except Exception as e:
            logging.exception(e, "unable to apply partial configuration")

    elif topic.endswith("/cmd") and message == "tare":
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
        client.clear_retained(topic)
    elif topic.endswith("/cmd") and message == "reboot":
        client.clear_retained(topic)
        import machine

        machine.reset()
    # topic is None ? why is this?
    elif topic is None or topic.endswith("/ota"):
        from external.kpn_senml.senml_pack_json import SenmlPackJson

        senmlMessage = SenmlPackJson("")
        senmlMessage.from_json(message)
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
                    client.clear_retained(topic)
                    import utils

                    utils.clearCachedStates()
                    utils.writeToFile("/ota_applied_flag", "done")
                    import machine

                    machine.reset()
                else:
                    sendOtaStatusMessage(client, fileId, False, "can not apply")
                    client.clear_retained(topic)
            else:
                sendOtaStatusMessage(client, fileId, False, "can not download")


def hasEnoughFreeSpace(fileSize):
    import uos

    # for ESP32 uos.statvfs('/')
    (f_bsize, _, f_blocks, f_bfree, _, _, _, _, _, _) = uos.statvfs(device_info.get_device_root_folder())
    freesize = f_bsize * f_bfree
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


def downloadDeviceConfigurationHTTP(client):
    logging.info("About to download device configuration over HTTP...")
    protocol_config = cfg.get_protocol_config()
    URL_base = "console.insigh.io"
    URL_PATH = "/mf-rproxy/device/config"
    URL_QUERY_PARAMS = "id={}&channel={}".format(protocol_config.thing_id, protocol_config.control_channel_id)
    if client.modem_based:
        file = "tmpconfig"
        file_downloaded = client.modem_instance.http_get_with_auth_header(
            URL_base,
            URL_PATH + "?" + URL_QUERY_PARAMS,
            protocol_config.thing_token,
            file,
            120000,
        )
        if file_downloaded:
            local_file_name = device_info.get_device_root_folder() + file
            is_file_locally = client.modem_instance.get_file(file, local_file_name)
            if is_file_locally:
                client.modem_instance.delete_file(file)
                configContent = utils.readFromFile(local_file_name)
                logging.debug("config content: |" + configContent + "|")
                if configContent.startswith('"') and configContent.endswith('"'):
                    configContent = configContent[1:-1]

                return configContent
    else:  # not tested
        gc.collect()
        print("mem free: " + str(gc.mem_free()))
        try:
            from utils import httpclient

            headers = {"Authorization": protocol_config.thing_token}
            params = "id={}&channel={}".format(protocol_config.thing_id, protocol_config.control_channel_id)
            http_version = "http" if device_info.get_hw_module_verison() == "esp32wroom" else "https"
            use_https = http_version == "https"
            url = "{}://{}{}?{}".format(http_version, URL_base, URL_PATH, params)
            client = httpclient.HttpClient(headers)
            response = None
            try:
                response = client.get(url)
            except Exception as e:
                logging.exception(e, "error executing HTTP GET")

            if (not response or response.status_code != 200) and use_https:
                logging.info("request failed, retrying without HTTPS")
                response = client.get(url.replace("https://", "http://"))

            if response and response.status_code == 200:
                try:
                    resp = response.content.decode("utf-8")
                    if resp.startswith('"') and resp.endswith('"'):
                        resp = resp[1:-1]
                    logging.debug("new configuration: " + resp)

                    utils.deleteModule("utils.httpclient")

                    return resp
                except Exception as e:
                    logging.exception(e, " error reading response")
                    pass
        except Exception as e:
            logging.exception(e, "unable to instantiate httpclient")

    utils.deleteModule("utils.httpclient")
    return None


def downloadOTA(client, fileId, fileType, fileSize):
    logging.info("About to download OTA package: " + fileId + fileType)

    if not hasEnoughFreeSpace(int(fileSize)):
        sendOtaStatusMessage(client, fileId, False, "not enough space")
        return None

    logging.debug("OTA size check passed")

    filename = device_info.get_device_root_folder() + fileId + fileType
    # http://<ip>/packages/download?fuid=<file-uid>&did=<device-id>&dk=<device-key>&cid=<control-channel-id>
    # TODO: fix support of redirections
    protocol_config = cfg.get_protocol_config()
    http_version = "http" if device_info.get_hw_module_verison() == "esp32wroom" else "https"
    use_https = http_version == "https"
    URL = "{}://{}/mf-rproxy/packages/download?fuid={}&did={}&dk={}&cid={}".format(
        http_version,
        protocol_config.server_ip,
        # "console.insigh.io",
        fileId,
        protocol_config.thing_id,
        protocol_config.thing_token,
        protocol_config.control_channel_id,
    )

    logging.debug("OTA URL: " + URL)

    if client.modem_based:
        file = fileId + fileType
        # TODO: clear all local files from previous failed attempts?
        file_downloaded = client.modem_instance.http_get_file(URL, file, 250000)
        if file_downloaded:
            local_file_name = device_info.get_device_root_folder() + file
            is_file_locally = client.modem_instance.get_file(file, local_file_name)
            if is_file_locally:
                client.modem_instance.delete_file(file)
                return local_file_name
        return None
    else:
        gc.collect()
        print("mem free: " + str(gc.mem_free()))
        try:
            from utils import httpclient

            client = httpclient.HttpClient()
            response = None
            try:
                response = client.get(URL, saveToFile=filename)
            except Exception as e:
                logging.exception(e, "error executing HTTP GET")

            if (not response or response.status_code != 200) and use_https:
                logging.info("request failed, retrying without HTTPS")
                response = client.get(URL.replace("https://", "http://"), saveToFile=filename)

            success_status = response and response.status_code == 200

            utils.deleteModule("utils.httpclient")

            if success_status:
                logging.debug("HTTP file downloaded: " + filename)
                return filename
        except Exception as e:
            logging.exception(e, "unable to instantiate httpclient")
    return None


def applyDeviceConfiguration(client, configurationParameters, topic):
    if configurationParameters is None:
        return

    from utils import configuration_handler

    keyValueDict = configuration_handler.stringParamsToDict(configurationParameters)

    configuration_handler.apply_configuration(keyValueDict)
    client.clear_retained(topic)
    client.disconnect()
    import machine

    logging.info("about to reset to use new configuration")
    machine.reset()
