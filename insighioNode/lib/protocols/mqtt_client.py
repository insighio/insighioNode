from external.umqtt.simple import MQTTClient as uMQTTClient
import utime as time
from .mqtt_config import MQTTConfig
import logging
# for ESP32 use mutex instead of thread lock
# from utils import mutex
import _thread


class MQTTClientCustom:
    def __init__(self, mqtt_config):
        self.client = uMQTTClient(mqtt_config.client_name, mqtt_config.server_ip, mqtt_config.server_port,
                                  mqtt_config.thing_id, mqtt_config.thing_token)
        self.config = mqtt_config
        self.prepareChannelNames(mqtt_config)
        self.lastReceivedMessage = None
        # self.mutex = mutex.Mutex()
        self.mutex = _thread.allocate_lock()

    def prepareChannelNames(self, mqtt_config):
        controlChannel = "channels/" + mqtt_config.control_channel_id + "/messages"
        self.otaChannel = controlChannel + "/" + mqtt_config.thing_id + "/ota"
        self.messageChannel = "channels/" + mqtt_config.message_channel_id + "/messages/" + mqtt_config.thing_id

        logging.debug("Selected channels:")
        logging.debug(" ota channel: " + self.otaChannel)
        logging.debug(" messageChannel: " + self.messageChannel)

    def subscribe_callback(self, topic, message):
        logging.debug("topic: " + str(topic) + ", message: " + str(message))
        with self.mutex:
            logging.debug("in mutex")
            self.lastReceivedMessage = dict()
            self.lastReceivedMessage["topic"] = topic
            self.lastReceivedMessage["message"] = message

    def __check_msg(self, timeout_ms):
        start_time = time.ticks_ms()
        end_time = start_time + timeout_ms
        while (time.ticks_ms() < end_time):
            try:
                self.client.check_msg()
                # if mutex.test():
                if self.mutex.acquire(1, 1):  # 1 = wait for lock, 1 = 1 second wait else fail
                    if self.lastReceivedMessage is not None:
                        message = self.lastReceivedMessage.copy()
                        self.lastReceivedMessage = None
                        self.mutex.release()
                        return message
                    self.mutex.release()
            except AssertionError:
                pass
            time.sleep_ms(10)

        return None

    def __sendMessageEx(self, url, message, qos=0, retained=False):
        try:
            self.client.publish(url, message, retained, qos)
            # if publish fails, exception is thrown, else return True
            return True
        except Exception as e:
            logging.exception(e, 'Exception during MQTT message sending:')
            return False

    def connect(self):
        self.client.set_callback(self.subscribe_callback)
        try:
            logging.debug("Connecting to MQTT...")
            self.client.connect()
            # if connect fails, exception is thrown, else return True
            return True
        except Exception as e:
            logging.exception(e, 'Exception during MQTT connect with:')
            return False

    def sendMessage(self, message, topic=None, retained=False):
        if topic is None:
            topic = self.messageChannel
        return self.__sendMessageEx(topic, message, 1, retained)

    def sendOtaMessage(self, message):
        return self.sendMessage(message, self.otaChannel, False)

    def clearOtaMessages(self):
        return self.sendMessage("", self.otaChannel, True)

    def subscribe_and_get_first_message(self, channel=None):
        try:
            if channel is None:
                channel = self.otaChannel
            self.client.subscribe(channel)
            return self.__check_msg(5000)
        except Exception as e:
            logging.exception(e, 'Exception during MQTT subscribe with:')
            return None
        return None

    def disconnect(self):
        try:
            self.client.disconnect()
            return True
        except Exception as e:
            logging.exception(e, 'Exception during MQTT disconnect:')
            return False
