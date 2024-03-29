network="lora"

""" LoRa example configuration options """
_MAX_CONNECTION_ATTEMPT_TIME_SEC = 60

""" LoRa-related configuration options """
_DEV_EUI = "<lora-dev-eui>"
_APP_EUI = "<lora-app-eui>"
_APP_KEY = "<lora-app-key>"

_LORA_REGION = "<lora-region>"
_LORA_ADR = <lora-adr>
_LORA_DR = <lora-dr>
_LORA_CONFIRMED = <lora-confirmed>
_LORA_TX_RETRIES = <lora-retries>
_LORA_SOCKET_TIMEOUT = 30
_LISTEN_DL_MSG = False
_LORA_SOCKET_BUFFER_SIZE = 128

class LoRaConfig:
    def __init__(self):
        self.keepalive = 0

def get_protocol_config():
    return LoRaConfig()
