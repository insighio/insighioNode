import logging


def send_packet(cfg, message):
    # transport-related functionalities
    cfg.protocol_config.client_name = cfg.device_id
    if cfg.protocol == 'coap':
        from protocols import coap_client
        coap_cli = coap_client.CoAPClient(cfg.protocol_config)
        if cfg.protocol_config.use_custom_socket:
            import external.microATsocket.microATsocket as socket
            from networking import cellular
            cfg.protocol_config.custom_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            cfg.protocol_config.custom_socket.setModemInstance(cellular.get_modem_instance())

        connectionStatus = coap_cli.start()
        logging.info("CoAP connection status: " + str(connectionStatus))
        connectionStatus = 1  # TODO: temp solution till we resolve what values are returned from connect function
        if connectionStatus != 0:
            logging.info("About to send: " + message)
            coap_cli.postMessage(message)
            logging.info("Done.")
            logging.info("Starting polling for 2 seconds:")
            coap_cli.poll(2000)
            logging.info("stopped")
            coap_cli.stop()
            logging.info("Disconnected")
            return True
        else:
            print("CoAP not started, idle for this loop")
            return False
    elif cfg.protocol == 'mqtt':
        from protocols import mqtt_client
        mqtt_cli = mqtt_client.MQTTClientCustom(cfg.protocol_config)
        connectionStatus = mqtt_cli.connect()
        message_publish_ok = False
        logging.info("Mqtt connection status: " + str(connectionStatus))
        if connectionStatus:
            logging.info("About to send: " + message)
            for i in range(0, 3):
                message_publish_ok = mqtt_cli.sendMessage(message)
                if message_publish_ok:
                    logging.info("Done.")
                    break
            mqtt_cli.disconnect()
            logging.info("Disconnected")
        else:
            logging.info("MQTT not connected, idle for this loop")
        return message_publish_ok
