import logging
from . import transfer_protocol


def checkAndApply(client):
    if client is None:
        logging.debug("OTA check aborted, no active transfer client")
        return False

    message = client.get_control_message()

    if message is not None and message["message"] is not None:
        logging.debug("mqtt messqage received: " + str(message["message"]))

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
            applyOTA(client, fileId, fileType, fileSize)


def hasEnoughFreeSpace(fileSize):
    import uos
    # for ESP32 uos.statvfs('/')
    (f_bsize, _, f_blocks, f_bfree, _, _, _, _, _, _) = uos.statvfs('/flash')
    freesize = f_bsize * f_bfree
    return fileSize < freesize


def sendFailureMessage(client, fileId):
    from . import transfer_protocol
    from external.kpn_senml.senml_pack_json import SenmlPackJson
    from external.kpn_senml.senml_record import SenmlRecord

    message = SenmlPackJson('')
    message.add(SenmlRecord("e", value=2))  # event id == 2 => failure
    message.add(SenmlRecord("i", value=fileId))

    client.send_control_packet_ota(message.to_json())
    client.clear_control_messages()


def applyOTA(client, fileId, fileType, fileSize):
    logging.info("About to download OTA package: " + fileId + fileType)

    # if not hasEnoughFreeSpace(int(fileSize)):
    if True:
        sendFailureMessage(client, fileId)
        return

    logging.debug("OTA size check passed")

    # http://<ip>/packages/download?fuid=<file-uid>&did=<device-id>&dk=<device-key>&cid=<control-channel-id>
