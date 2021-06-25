import logging


class TransferProtocol:
    def __init__(self, cfg):
        self.connected = False
        self.protocol_config = cfg.protocol_config
        self.protocol_config.client_name = cfg.device_id
        self.protocol = cfg.protocol
        logging.debug("initializing TransferProtocol for: " + str(self.protocol))
        if self.protocol == 'coap':
            from protocols import coap_client
            self.client = coap_client.CoAPClient(self.protocol_config)
            if self.protocol_config.use_custom_socket:
                import external.microATsocket.microATsocket as socket
                from network import LTE
                self.protocol_config.custom_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
                self.protocol_config.custom_socket.setModemInstance(LTE())
        elif self.protocol == 'mqtt':
            from protocols import mqtt_client
            self.client = mqtt_client.MQTTClientCustom(self.protocol_config)

    def connect(self):
        if self.protocol == 'coap':
            connectionStatus = self.client.start()
            logging.info("CoAP connection status: " + str(connectionStatus))
            self.connected = True
            return True  # TODO: temp solution till we resolve what values are returned from connect function
            # return connectionStatus
        elif self.protocol == 'mqtt':
            connectionStatus = self.client.connect()
            logging.info("mqtt connection status: " + str(connectionStatus))
            self.connected = True
            return True  # TODO: temp solution till we resolve what values are returned from connect function
            # return connectionStatus
        return False

    def disconnect(self):
        self.client.disconnect()
        self.connected = False
        logging.info("Disconnected")

    def send_packet(self, message):
        # transport-related functionalities
        if not self.connected:
            logging.info("TransferProtocol not connected")
            return False

        if self.protocol == 'coap':
            logging.info("About to send: " + message)
            self.client.postMessage(message)
            logging.info("Done.")
            # logging.info("Starting polling for 2 seconds:")
            # self.client.poll(2000)
        elif self.protocol == 'mqtt':
            logging.info("About to send: " + message)
            self.client.sendMessage(message)
            logging.info("Done.")
        return False

    def get_control_message(self):
        if not self.connected:
            logging.info("TransferProtocol not connected")
            return False

        if self.protocol == 'coap':
            return None
        elif self.protocol == 'mqtt':
            return self.client.subscribe_and_get_first_message()

    def clear_control_messages(self):

        if not self.connected:
            logging.info("TransferProtocol not connected")
            return False

        if self.protocol == 'mqtt':
            logging.info("About to clear retained messages")
            self.client.sendMessage("", self.protocol_config.control_channel_id, True)
            logging.info("Done.")
