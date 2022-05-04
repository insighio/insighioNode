import logging
import device_info


class TransferProtocol:
    def __init__(self, cfg, modem_instance=None):
        self.connected = False
        self.modem_instance = modem_instance
        self.modem_based = (modem_instance is not None)
        self.protocol_config = cfg.get_protocol_config()
        self.protocol_config.client_name = cfg.device_id
        self.protocol = cfg.protocol
        logging.debug("initializing TransferProtocol for: " + str(self.protocol))
        if not self.modem_based and self.protocol == 'coap':
            from protocols import coap_client
            self.client = coap_client.CoAPClient(self.protocol_config)
            if self.protocol_config.use_custom_socket:
                import external.microATsocket.microATsocket as socket
                from network import LTE
                self.protocol_config.custom_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
                self.protocol_config.custom_socket.setModemInstance(LTE())
        elif not self.modem_based and self.protocol == 'mqtt':
            from protocols import mqtt_client
            self.client = mqtt_client.MQTTClientCustom(self.protocol_config)

    def connect(self):
        if self.connected:
            return True

        if self.modem_based:
            self.connected = self.modem_instance.mqtt_connect(self.protocol_config.server_ip, self.protocol_config.server_port, self.protocol_config.thing_id, self.protocol_config.thing_token)
        elif self.protocol == 'coap':
            connectionStatus = self.client.start()
            logging.info("CoAP connection status: " + str(connectionStatus))
            self.connected = True  # TODO: temp solution till we resolve what values are returned from connect function
        elif self.protocol == 'mqtt':
            connectionStatus = self.client.connect()
            logging.info("mqtt connection status: " + str(connectionStatus))
            # connectionStatus is not valid on pycom devices
            self.connected = (connectionStatus or not device_info.is_esp32())
        return self.connected

    def disconnect(self):
        if self.modem_based:
            self.modem_instance.mqtt_disconnect()
        else:
            self.client.disconnect()
        self.connected = False
        logging.info("Disconnected")

    def send_packet(self, message, channel=None):
        # transport-related functionalities
        if not self.connected:
            logging.info("TransferProtocol not connected")
            return False

        if self.modem_based:
            topic = 'channels/{}/messages/{}'.format(self.protocol_config.message_channel_id, self.protocol_config.thing_id)
            return self.modem_instance.mqtt_publish(topic, message)
        elif self.protocol == 'coap':
            logging.info("About to send: " + message)
            self.client.postMessage(message)
            logging.info("Done.")
            return True
        elif self.protocol == 'mqtt':
            logging.info("About to send: " + message)
            for i in range(0, 3):
                message_publish_ok = self.client.sendMessage(message, channel)
                if message_publish_ok:
                    logging.info("Done.")
                    return True
        logging.info("Failed.")
        return False

    def send_control_packet(self, message, subtopic):
        if not self.connected:
            logging.info("TransferProtocol not connected")
            return False

        logging.info("About to send control message")

        if self.modem_based:
            topic = 'channels/{}/messages/{}{}'.format(self.protocol_config.control_channel_id, self.protocol_config.thing_id, subtopic)
            return self.modem_instance.mqtt_publish(topic, message)
        elif self.protocol == 'mqtt':
            return self.client.sendControlMessage(message, subtopic)
            logging.info("Done.")

    def get_control_message(self):
        if not self.connected:
            logging.info("TransferProtocol not connected")
            return None

        if self.modem_based:
            topic = 'channels/{}/messages/{}/#'.format(self.protocol_config.control_channel_id, self.protocol_config.thing_id)
            return self.modem_instance.mqtt_get_message(topic, 10000)
        elif self.protocol == 'coap':
            return None
        elif self.protocol == 'mqtt':
            return self.client.subscribe_and_get_first_message()

    def clear_retained(self, topic):
        logging.info("About to clear retained message of topic: " + topic)
        if self.modem_based:
            return self.modem_instance.mqtt_publish(topic, "", 3, True)
        elif self.protocol == 'mqtt':
            return self.client.sendMessage("", topic, True)
        else:
            logging.error("clear_retained: protocol not supported")
            return False
