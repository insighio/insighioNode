from external.umqtt.simple import MQTTClient as uMQTTClient
import utime
from .mqtt_config import MQTTConfig
import logging
import _thread


class MQTTClientCustom:
    def __init__(self, mqtt_config):
        self.client = uMQTTClient(mqtt_config.client_name, mqtt_config.server_ip, mqtt_config.server_port,
                                  mqtt_config.thing_id, mqtt_config.thing_token, mqtt_config.keepalive)
        self.config = mqtt_config
        self.prepareChannelNames(mqtt_config)
        self.lastReceivedMessage = None
        self.clean_session = True
        self._has_connected = False
        self._is_connected = False
        self.keepalive = 1000 * mqtt_config.keepalive  # ms
        self._ping_interval = self.keepalive // 4 if self.keepalive else 20000
        p_i = self._ping_interval * 1000  # Can specify shorter e.g. for subscribe-only
        if p_i and p_i < self._ping_interval:
            self._ping_interval = p_i
        self.mutex = _thread.allocate_lock()

    def prepareChannelNames(self, mqtt_config):
        controlChannel = "channels/" + mqtt_config.control_channel_id + "/messages" if mqtt_config.control_channel_id else ""
        self.controlChannelGeneric = controlChannel + "/" + mqtt_config.thing_id if mqtt_config.control_channel_id and mqtt_config.thing_id else ""
        self.otaChannel = controlChannel + "/" + mqtt_config.thing_id + "/ota" if mqtt_config.control_channel_id and mqtt_config.thing_id else ""
        self.messageChannel = "channels/" + mqtt_config.message_channel_id + "/messages/" + mqtt_config.thing_id  if mqtt_config.message_channel_id and mqtt_config.thing_id else ""

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
        start_time = utime.ticks_ms()
        end_time = start_time + timeout_ms
        while (utime.ticks_ms() < end_time):
            try:
                self.client.check_msg()
                with self.mutex:
                    if self.lastReceivedMessage is not None:
                        message = self.lastReceivedMessage.copy()
                        self.lastReceivedMessage = None
                        return message
            except AssertionError:
                pass
            utime.sleep_ms(10)

        return None

    def __sendMessageEx(self, url, message, qos=0, retained=False):
        try:
            self.client.publish(url, message, retained, qos)
            # if publish fails, exception is thrown, else return True
            return True
        except Exception as e:
            logging.exception(e, 'Exception during MQTT message sending:')
            return False

    def set_last_will(self, subtopic, msg, retain=False, qos=0):
        try:
            self.client.set_last_will(self.controlChannelGeneric + subtopic, msg, retain, qos)
        except Exception as e:
            logging.exception(e, 'Exception while setting last will')

    def connect(self):
        self.client.set_callback(self.subscribe_callback)
        try:
            logging.debug("Connecting to MQTT...")
            if self._has_connected and not self.clean_session:
                # Power up. Clear previous session data but subsequently save it.
                self.client.connect(True) # Connect with clean session
                try:
                    disconnect=b"\xe0\0"
                    with self.client.lock:
                        self.client._write(disconnect, len(disconnect))  # Force disconnect but keep socket open
                except:
                    pass
            self.client.connect(self.clean_session)
            self._is_connected = True

            if not self._has_connected:
                self._has_connected = True

            if self.keepalive > 0:
                _thread.start_new_thread(self.keep_alive_thread, ())
            return True
        except Exception as e:
            logging.exception(e, 'Exception during MQTT connect with:')
            self._is_connected = False
            return False

    def is_connected(self):
        return self._is_connected

    def sendMessage(self, message, topic=None, retained=False, require_message_delivery_ack=True):
        if topic is None:
            topic = self.messageChannel
        return self.__sendMessageEx(topic, message, 1 if require_message_delivery_ack else 0, retained)

    def sendControlMessage(self, message, subtopic):
        return self.sendMessage(message, self.controlChannelGeneric + subtopic, False)

    def subscribe_and_get_first_message(self, channel=None):
        try:
            if channel is None:
                channel = self.controlChannelGeneric + "/#"
            self.client.subscribe(channel)
            return self.__check_msg(5000)
        except Exception as e:
            logging.exception(e, 'Exception during MQTT subscribe with:')
            return None
        return None

    def disconnect(self):
        try:
            self.client.disconnect()
            self._has_connected = False
            self._is_connected = False
            return True
        except Exception as e:
            logging.exception(e, 'Exception during MQTT disconnect:')
            return False

    def keep_alive_thread(self):
        while self._has_connected:
            pings_due = utime.ticks_diff(utime.ticks_ms(), self.client.last_rx) // self._ping_interval
            if pings_due >= 4:
                logging.debug('Reconnect: broker fail.')
                self._is_connected = False
                break
            utime.sleep_ms(self._ping_interval)
            try:
                self.client.ping()
                logging.debug('Mqtt Ping ok')
            except OSError:
                logging.debug('Mqtt Ping failed')
                self._is_connected = False
                break
