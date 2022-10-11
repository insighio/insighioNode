class MQTTConfig:
    def __init__(self):
        self.server_ip = ""
        self.server_port = 1883
        self.control_channel_id = ""
        self.message_channel_id = ""
        self.thing_id = ""
        self.thing_token = ""
        self.client_name = ""
        self.keepalive = 0
        self.lw_subtopic = None
        self.lw_message = None
        self.lw_qos = None
        self.lw_retain = None
