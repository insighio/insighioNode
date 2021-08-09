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
        logging.debug("mqtt message received: " + str(message["message"]))

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
                    client.clear_control_messages()
                    import machine
                    machine.reset()
                else:
                    sendStatusMessage(client, fileId, False, "can not apply")
                    client.clear_control_messages()
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
        return

    logging.debug("OTA size check passed")

    from external.MicroWebCli import microWebCli
    from . import demo_config as cfg

    filename = device_info.get_device_root_folder() + fileId + fileType
    # http://<ip>/packages/download?fuid=<file-uid>&did=<device-id>&dk=<device-key>&cid=<control-channel-id>
    URL = 'http://{}/mf-rproxy/packages/download?fuid={}&did={}&dk={}&cid={}'.format(
        #'192.168.43.27:3003',
        cfg.protocol_config.server_ip,
        fileId,
        cfg.protocol_config.thing_id,
        cfg.protocol_config.thing_token,
        cfg.protocol_config.control_channel_id
    )
    wCli = microWebCli.MicroWebCli(URL)
    logging.debug('GET file %s' % wCli.URL)
    wCli.OpenRequest()
    resp = wCli.GetResponse()
    logging.debug("Get file response status: {}, message: {}".format(resp.GetStatusCode(), resp.GetStatusMessage()))
    if resp.IsSuccess():
        contentType = resp.WriteContentToFile(filename, progressCallback)
        logging.debug('File was saved to "%s"' % (filename))
        return filename
    return False


def downloadOTAQuectelBG600(client, fileId, fileType, fileSize):
    pass
