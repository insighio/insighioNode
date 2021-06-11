from external.umqtt.simple import MQTTClient as uMQTTClient
import utime as time
from .mqtt_config import MQTTConfig
import logging


def sub_cb(topic, msg):
    logging.debug((topic, msg))


class MQTTClientCustom:
    def prepareChannelNames(self, mqtt_config):
        controlChannel = "channels/" + mqtt_config.control_channel_id + "/messages"
        self.statusChannel = controlChannel + "/status/" + mqtt_config.thing_id
        self.requestChannel = controlChannel + "/request/" + mqtt_config.thing_id
        self.messageChannel = "channels/" + mqtt_config.message_channel_id + "/messages/" + mqtt_config.thing_id

        logging.debug("Selected channels:")
        logging.debug(" status channel: " + self.statusChannel)
        logging.debug(" requestChannel: " + self.requestChannel)
        logging.debug(" messageChannel: " + self.messageChannel)

    def subscribe_callback(self, topic, msg):
        logging.debug((topic, msg))

    def __init__(self, mqtt_config):
        self.client = uMQTTClient(mqtt_config.client_name, mqtt_config.server_ip, mqtt_config.server_port,
                                  mqtt_config.thing_id, mqtt_config.thing_token)
        self.config = mqtt_config
        self.prepareChannelNames(mqtt_config)

    def __check_msg(self, timeout_ms):
        start_time = time.ticks_ms()
        message = None
        while message is None and ((time.ticks_diff(time.ticks_ms(), start_time) < timeout_ms)):
            message = self.client.check_msg()
        if message is not None:
            logging.debug('MQTT message received: ' + message)

    def __sendMessageEx(self, url, message, qos=0, retained=False):
        try:
            self.client.publish(url, message, retained, qos)
            # self.__check_msg(1000)
        except Exception as e:
            logging.exception(e, 'Exception during MQTT message sending:')

    def connect(self):
        self.client.set_callback(self.subscribe_callback)
        try:
            logging.debug("Connecting to MQTT...")
            status = self.client.connect()
            # todo: if status is true, send  status message
            # self.__sendMessageEx(self.statusChannel, '1', 1, True)
            # self.__check_msg(1000)
            return status
        except Exception as e:
            logging.exception(e, 'Exception during MQTT connect with:')
            return False

    def sendMessage(self, message):
        self.__sendMessageEx(self.messageChannel, message, 1, False)

    def disconnect(self):
        try:
            # self.__sendMessageEx(self.statusChannel, '0', 1, True)
            self.client.disconnect()
            return True
        except Exception as e:
            logging.exception(e, 'Exception during MQTT disconnect:')
            return False
