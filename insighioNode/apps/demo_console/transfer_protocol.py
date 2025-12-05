import logging
from . import locks
import utils


class TransferProtocol:
    def __init__(self, cfg, modem_instance=None):
        self.connected = False
        self.protocol_config = cfg.get_protocol_config()
        self.protocol_config.client_name = cfg.get("device_id")
        self.protocol = cfg.get("protocol")
        self.modem_based = False
        if self.protocol_config.keepalive is None:
            self.protocol_config.keepalive = 120
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
        self.modem_based = modem_instance is not None
        self.require_message_delivery_ack = utils.get_var_from_module(self.protocol_config, "REQ_MESG_DEL_ACK")
        if self.require_message_delivery_ack is None:
            self.require_message_delivery_ack = True  # enable if configuration is missing

        logging.debug("Enabled message delivery ack: {}".format(self.require_message_delivery_ack))

    def connect(self):
        if self.is_connected():
            return True

        # TODO: use the keepalive setting
        self.connected = self.modem_instance.mqtt_connect(
            self.protocol_config.server_ip,
            self.protocol_config.server_port,
            self.protocol_config.thing_id,
            self.protocol_config.thing_token,
            self.protocol_config.keepalive,
        )
        return self.connected

    def is_connected(self):
        self.connected = self.modem_instance.mqtt_is_connected()
        return self.connected

    def disconnect(self):
        self.modem_instance.mqtt_disconnect()
        self.connected = False
        logging.info("Disconnected")

    def send_packet(self, message, channel=None):
        # transport-related functionalities
        if not self.connected:
            logging.info("TransferProtocol not connected")
            return False

        topic = "channels/{}/messages/{}".format(self.protocol_config.message_channel_id, self.protocol_config.thing_id)
        return self.modem_instance.mqtt_publish(topic, message, 3, False, 1 if self.require_message_delivery_ack else 0)

    def send_control_packet(self, message, subtopic):
        if not self.connected:
            logging.info("TransferProtocol not connected")
            return False

        logging.info("About to send control message")

        topic = "channels/{}/messages/{}{}".format(self.protocol_config.control_channel_id, self.protocol_config.thing_id, subtopic)
        return self.modem_instance.mqtt_publish(topic, message)

    def send_config_packet(self, message):
        if not self.connected:
            logging.info("TransferProtocol not connected")
            return False

        logging.info("About to send config message")
        URL_base = self.protocol_config.server_ip
        URL_PATH = "/http/channels/{}/messages/{}{}".format(self.protocol_config.control_channel_id, self.protocol_config.thing_id, "/configResponse")

        post_body = [{"n": "config", "vs": message}]
        return self.modem_instance.http_post_with_auth_header(
            URL_base, URL_PATH, self.protocol_config.thing_token, post_body, timeout_ms=125000
        )

    def get_control_message(self):
        if not self.connected:
            logging.info("TransferProtocol not connected")
            return None

        topic = "channels/{}/messages/{}/#".format(self.protocol_config.control_channel_id, self.protocol_config.thing_id)
        return self.modem_instance.mqtt_get_message(topic, 5000)

    def clear_retained(self, topic):
        logging.info("About to clear retained message of topic: " + topic)
        return self.modem_instance.mqtt_publish(topic, "", 3, True)


class TransferProtocolMQTT(TransferProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)
        from protocols import mqtt_client
        import utils

        self.client = mqtt_client.MQTTClientCustom(self.protocol_config)
        self.enable_last_will(self.protocol_config)
        self.require_message_delivery_ack = utils.get_var_from_module(self.protocol_config, "REQ_MESG_DEL_ACK")
        if self.require_message_delivery_ack is None:
            self.require_message_delivery_ack = True  # enable if configuration is missing

        logging.debug("Enabled message delivery ack: {}".format(self.require_message_delivery_ack))

    def connect(self):
        if self.connected:
            return True

        with locks.network_transmit_mutex:
            self.connected = self.client.connect()
            logging.info("mqtt connection status: " + str(self.connected))
            return self.connected

    def enable_last_will(self, protocol_config):
        if protocol_config.lw_subtopic is None or protocol_config.lw_message is None or self.client is None:
            logging.info("Error in last will setup, ignoring")
            return

        logging.info("Setting last will message")
        qos = protocol_config.lw_qos if not None else 0
        retain = protocol_config.lw_retain if not None else False
        self.client.set_last_will(protocol_config.lw_subtopic, protocol_config.lw_message, retain, qos)

    def is_connected(self):
        with locks.network_transmit_mutex:
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

        logging.debug("About to send: " + message)
        for i in range(0, 3):
            with locks.network_transmit_mutex:
                message_publish_ok = self.client.sendMessage(message, channel, False, self.require_message_delivery_ack)
            if message_publish_ok:
                logging.info("Sent.")
                return True
        logging.info("Failed.")
        return False

    def send_control_packet(self, message, subtopic):
        if not self.connected:
            logging.info("TransferProtocol not connected")
            return False

        logging.debug("About to send control message")
        with locks.network_transmit_mutex:
            return self.client.sendControlMessage(message, subtopic)

    def get_control_message(self):
        if not self.connected:
            logging.info("TransferProtocol not connected")
            return None

        with locks.network_transmit_mutex:
            return self.client.subscribe_and_get_first_message()

    def clear_retained(self, topic):
        logging.info("About to clear retained message of topic: " + topic)
        with locks.network_transmit_mutex:
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

        logging.debug("About to send: " + message)
        self.client.postMessage(message)
        logging.info("Done.")
        return True
