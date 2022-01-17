import logging
from . import transfer_protocol
import device_info


def checkAndApply(client):
    if client is None:
        logging.debug("OTA check aborted, no active transfer client")
        return False

    logging.info("Waiting for incoming control message (OTA)...")
    message = client.get_control_message()

    if message is None or message["message"] is None:
        logging.info("No control message received")
        return
    else:
        logging.debug("mqtt message received: " + str(message["message"]) + " in topic: " + str(message["topic"]))

        if message["topic"].endswith("/config"):
            applyDeviceConfiguration(client, message["message"].decode("utf-8"))
        elif message["topic"] is None or message["topic"].endswith("/ota"):
            from external.kpn_senml.senml_pack_json import SenmlPackJson
            senmlMessage = SenmlPackJson("")
            senmlMessage.from_json(message["message"])
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
                        sendStatusMessage(client, fileId, True)
                        client.clear_control_message_ota()
                        import utils
                        utils.clearCachedStates()
                        import machine
                        machine.reset()
                    else:
                        sendStatusMessage(client, fileId, False, "can not apply")
                        client.clear_control_message_ota()
                else:
                    sendStatusMessage(client, fileId, False, "can not download")


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
def sendStatusMessage(client, fileId, success, reason_measage=None):
    from . import transfer_protocol
    from external.kpn_senml.senml_pack_json import SenmlPackJson
    from external.kpn_senml.senml_record import SenmlRecord

    message = SenmlPackJson('')
    message.add(SenmlRecord("e", value=(1 if success else 2)))  # event id == 2 => failure
    message.add(SenmlRecord("i", value=fileId))
    if reason_measage is not None:
        message.add(SenmlRecord("m", value=reason_measage))

    client.send_control_packet_ota(message.to_json())


def progressCallback(microWebCli, progressSize, totalSize):
    if totalSize:
        print('Progress: %d bytes of %d downloaded...' % (progressSize, totalSize))
    else:
        print('Progress: %d bytes downloaded...' % progressSize)


def downloadOTA(client, fileId, fileType, fileSize):
    logging.info("About to download OTA package: " + fileId + fileType)

    if not hasEnoughFreeSpace(int(fileSize)):
        sendStatusMessage(client, fileId, False, "not enough space")
        return None

    logging.debug("OTA size check passed")

    from . import demo_config as cfg

    filename = device_info.get_device_root_folder() + fileId + fileType
    # http://<ip>/packages/download?fuid=<file-uid>&did=<device-id>&dk=<device-key>&cid=<control-channel-id>
    # TODO: fix support of redirections
    protocol_config = cfg.get_protocol_config()
    URL = 'http://{}/mf-rproxy/packages/download?fuid={}&did={}&dk={}&cid={}'.format(
        #cfg.protocol_config.server_ip,
        "console.insigh.io",
        fileId,
        protocol_config.thing_id,
        protocol_config.thing_token,
        protocol_config.control_channel_id
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
        from external.MicroWebCli import microWebCli
        wCli = microWebCli.MicroWebCli(URL)
        logging.debug('GET file %s' % wCli.URL)
        wCli.OpenRequest()
        resp = wCli.GetResponse()
        logging.debug("Get file response status: {}, message: {}".format(resp.GetStatusCode(), resp.GetStatusMessage()))
        if resp.IsSuccess():
            contentType = resp.WriteContentToFile(filename, progressCallback)
            logging.debug('File was saved to "%s"' % (filename))
            return filename
    return None


def downloadOTAQuectelBG600(client, fileId, fileType, fileSize):
    pass


def applyDeviceConfiguration(client, configurationParameters):
    # remove '?' if the string starts with it
    if configurationParameters.startswith("?"):
        configurationParameters = str(configurationParameters[1:])

    keyValueDict = dict()
    keyValueStrings = configurationParameters.split("&")
    for keyValueStr in keyValueStrings:
        keyValue = keyValueStr.split("=")
        if len(keyValue) == 2:
            if keyValue[1] == "true":
                keyValue[1] = "True"
            elif keyValue[1] == "false":
                keyValue[1] = "False"
            keyValueDict[keyValue[0]] = keyValue[1]
            logging.debug("key value added [{}] -> {}".format(keyValue[0], keyValue[1]))
        else:
            logging.error("key value error |{}|".format(keyValue))

    from www import configuration_handler
    configuration_handler.apply_configuration(keyValueDict)
    client.clear_control_message_config()
    import machine
    machine.reset()
