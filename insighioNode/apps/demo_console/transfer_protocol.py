import logging
import device_info


class TransferProtocol:
    def __init__(self, cfg, modem_instance=None):
        self.connected = False
        self.protocol_config = cfg.get_protocol_config()
        self.protocol_config.client_name = cfg.device_id
        self.protocol = cfg.protocol
        self.modem_based = False
        logging.debug("initializing TransferProtocol for: " + str(self.protocol))

    def is_connected(self):
        return False

    def disconnect(self):
        return False

    def send_packet(self, message, channel=None):
        return False

    def send_control_packet(self, message, subtopic):
        logging.info("Control packet not supported for: " + self.protocol)
        return False

    def get_control_message(self):
        return logging.info("Control packet not supported for: " + self.protocol)

    def clear_retained(self, topic):
        return logging.info("Control packet not supported for: " + self.protocol)

class TransferProtocolModemAT(TransferProtocol):
    def __init__(self, cfg, modem_instance=None):
        super().__init__(cfg, modem_instance)
        self.modem_instance = modem_instance
        self.modem_based = (modem_instance is not None)

    def connect(self):
        if self.connected:
            return True

        #TODO: use the keepalive setting
        self.connected = self.modem_instance.mqtt_connect(self.protocol_config.server_ip, self.protocol_config.server_port, self.protocol_config.thing_id, self.protocol_config.thing_token)
        return self.connected

    def is_connected(self):
        return self.modem_instance.mqtt_is_connected()

    def disconnect(self):
        self.modem_instance.mqtt_disconnect()
        self.connected = False
        logging.info("Disconnected")

    def send_packet(self, message, channel=None):
        # transport-related functionalities
        if not self.connected:
            logging.info("TransferProtocol not connected")
            return False

        topic = 'channels/{}/messages/{}'.format(self.protocol_config.message_channel_id, self.protocol_config.thing_id)
        return self.modem_instance.mqtt_publish(topic, message)

    def send_control_packet(self, message, subtopic):
        if not self.connected:
            logging.info("TransferProtocol not connected")
            return False

        logging.info("About to send control message")

        topic = 'channels/{}/messages/{}{}'.format(self.protocol_config.control_channel_id, self.protocol_config.thing_id, subtopic)
        return self.modem_instance.mqtt_publish(topic, message)

    def get_control_message(self):
        if not self.connected:
            logging.info("TransferProtocol not connected")
            return None

        topic = 'channels/{}/messages/{}/#'.format(self.protocol_config.control_channel_id, self.protocol_config.thing_id)
        return self.modem_instance.mqtt_get_message(topic, 10000)

    def clear_retained(self, topic):
        logging.info("About to clear retained message of topic: " + topic)
        return self.modem_instance.mqtt_publish(topic, "", 3, True)


class TransferProtocolMQTT(TransferProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)
        from protocols import mqtt_client

        if self.protocol_config.keepalive is None:
             self.protocol_config.keepalive = 0
        self.client = mqtt_client.MQTTClientCustom(self.protocol_config)

    def connect(self):
        if self.connected:
            return True

        connectionStatus = self.client.connect()
        logging.info("mqtt connection status: " + str(connectionStatus))
        # connectionStatus is not valid on pycom devices
        self.connected = (connectionStatus or not device_info.is_esp32())
        return self.connected

    def is_connected(self):
        return self.client.is_connected()

    def disconnect(self):
        self.client.disconnect()
        self.connected = False
        logging.info("Disconnected")

    def send_packet(self, message, channel=None):
        # transport-related functionalities
        if not self.connected:
            logging.info("TransferProtocol not connected")
            return False

        logging.info("About to send: " + message)
        for i in range(0, 3):
            message_publish_ok = self.client.sendMessage(message, channel)
            if message_publish_ok:
                logging.info("Sent.")
                return True
        logging.info("Failed.")
        return False

    def send_control_packet(self, message, subtopic):
        if not self.connected:
            logging.info("TransferProtocol not connected")
            return False

        logging.info("About to send control message")
        return self.client.sendControlMessage(message, subtopic)


    def get_control_message(self):
        if not self.connected:
            logging.info("TransferProtocol not connected")
            return None

        return self.client.subscribe_and_get_first_message()

    def clear_retained(self, topic):
        logging.info("About to clear retained message of topic: " + topic)
        return self.client.sendMessage("", topic, True)

class TransferProtocolCoAP(TransferProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)
        from protocols import coap_client
        self.client = coap_client.CoAPClient(self.protocol_config)
        if self.protocol_config.use_custom_socket:
            import external.microATsocket.microATsocket as socket
            from network import LTE
            self.protocol_config.custom_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            self.protocol_config.custom_socket.setModemInstance(LTE())

    def connect(self):
        if self.connected:
            return True

        connectionStatus = self.client.start()
        logging.info("CoAP connection status: " + str(connectionStatus))
        self.connected = True  # TODO: temp solution till we resolve what values are returned from connect function

    def is_connected(self):
        return self.client.is_connected()

    def disconnect(self):
        self.client.stop()
        self.connected = False
        logging.info("Disconnected")

    def send_packet(self, message, channel=None):
        # transport-related functionalities
        if not self.connected:
            logging.info("TransferProtocol not connected")
            return False

        logging.info("About to send: " + message)
        self.client.postMessage(message)
        logging.info("Done.")
        return True
