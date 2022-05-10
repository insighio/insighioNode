import external.microcoapy as microcoapy
from .coap_config import CoAPConfig
import logging


def sub_cb(topic, msg):
    logging.debug((topic, msg))


class CoAPClient:
    def prepareChannelNames(self, coap_config):
        controlChannel = "channels/" + coap_config.control_channel_id + "/messages"
        self.statusChannel = controlChannel + "/status/" + coap_config.thing_id
        self.requestChannel = controlChannel + "/request/" + coap_config.thing_id
        self.messageChannel = "channels/" + coap_config.message_channel_id + "/messages/" + coap_config.thing_id

        self.uriQueryAuthentication = "authorization=" + coap_config.thing_token

        logging.debug("Selected channels:")
        logging.debug(" status channel: " + self.statusChannel)
        logging.debug(" requestChannel: " + self.requestChannel)
        logging.debug(" messageChannel: " + self.messageChannel)

    def receivedMessageCallback(self, packet, sender):
        logging.debug('Message received:', packet.toString(), ', from: ', sender)
        self.bufferedIncomingMessages.append(packet)

    def __init__(self, coap_config):
        self.client = None
        self.connected = False
        self.config = coap_config
        self.bufferedIncomingMessages = []
        self.prepareChannelNames(coap_config)

    def start(self):
        self.client = microcoapy.Coap()
        self.client.responseCallback = self.receivedMessageCallback

        if self.config.custom_socket is not None:
            # Use custom socket to all operations of CoAP
            logging.debug("Setting custom socket...")
            self.client.setCustomSocket(self.config.custom_socket)
            return 1

        try:
            status = self.client.start()
            # todo: if status is true, send  status message
            # self.__sendMessageEx(self.statusChannel, '1', 1, True)
            # self.__check_msg(1000)
            self.connected = status
            return status
        except Exception as e:
            logging.exception(e, 'Exception during CoAP start: ')
            self.connected = False
            return False

    def is_connected():
        return self.connected

    def postMessage(self, message):
        buffer = bytearray()
        buffer.extend(message)
        return self.client.postNonConf(self.config.server_ip,
                                       self.config.server_port,
                                       self.messageChannel,
                                       buffer,
                                       self.uriQueryAuthentication,
                                       microcoapy.COAP_CONTENT_FORMAT.COAP_APPLICATION_JSON)

    def loop(self):
        return self.client.loop()

    def poll(self, timeoutMs=-1):
        try:
            return self.client.poll(timeoutMs)
        except Exception as e:
            logging.exception(e, 'Exception during CoAP poll: ')
            return False

    # def postAndWaitForReply(self, message, timeoutMs, max_retransmissions=3):
    #     for r in range(max_retransmissions):
    #         messageid = self.postMessage(message)
    #         print("[postAndWaitForReply] post status: " + str(status))
    #         if status == 0:
    #             print("[postAndWaitForReply] Unable to send message, aborting...")
    #             return []
    #         self.bufferedIncomingMessages.clear()
    #         #wait for incomming messages
    #         self.poll(timeoutMs)
    #         #search captured packets for ACK message with message id equal to post message
    #         for pack in self.bufferedIncomingMessages:
    #             if pack.messageid == messageid: # ACK received
    #                 return pack
    #         self.bufferedIncomingMessages.clear()
    #         print('[postAndWaitForReply] ACK not found, retrying...')

    def stop(self):
        status = False
        try:
            self.client.stop()
            self.connected = False
            status = True
        except Exception as e:
            logging.exception(e, 'Exception during CoAP stop: ')

        self.connected = False
        return status
