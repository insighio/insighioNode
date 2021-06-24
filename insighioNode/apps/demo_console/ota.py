import logging


def checkAndApply(cfg):
    from protocols import mqtt_client
    mqtt_cli = mqtt_client.MQTTClientCustom(cfg.protocol_config)
    connectionStatus = mqtt_cli.connect()
    logging.info("Mqtt connection status: " + str(connectionStatus))
    connectionStatus = 1  # TODO: temp solution till we resolve what values are returned from connect function
    if connectionStatus != 0:
        message = mqtt_cli.subscribe_and_get_first_message()
        # mqtt_cli.sendMessage(message)
        mqtt_cli.disconnect()

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
                applyOTA(cfg, fileId, fileType)
    else:
        logging.info("MQTT not connected, idle for this loop")


def hasEnoughFreeSpace(fileSize):
    import uos
    # for ESP32 uos.statvfs('/')
    (f_bsize, _, f_blocks, f_bfree, _, _, _, _, _, _) = uos.statvfs('/flash')
    freesize = f_bsize * f_bfree
    return fileSize < freesize


def applyOTA(cfg, fileId, fileType, fileSize):
    logging.info("About to download OTA package: " + fileId + fileType)

    if not hasEnoughFreeSpace(fileSize):
        # send failure message
        pass

    # http://<ip>/packages/download?fuid=<file-uid>&did=<device-id>&dk=<device-key>&cid=<control-channel-id>
