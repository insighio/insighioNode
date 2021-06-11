network="lora"

""" System-related configuration options """
_DEEP_SLEEP_PERIOD_SEC = <period>  # tx period in secs

""" LoRa example configuration options """
_MAX_CONNECTION_ATTEMPT_TIME_SEC = 60

""" LoRa-related configuration options """
_DEV_EUI = '<lora-dev-eui>'
_APP_EUI = '<lora-app-eui>'
_APP_KEY = '<lora-app-key>'

from network import LoRa
_LORA_REGION = LoRa.<lora-region>
_LORA_ADR = <lora-adr>
_LORA_DR = <lora-dr> # data rate in case ADR is false
_LORA_CONFIRMED = <lora-confirmed> # confirmed transmission or not
_LORA_TX_RETRIES = <lora-retries>
_LORA_SOCKET_TIMEOUT = 30 # socket timeout for sending/receiving messages
_LISTEN_DL_MSG = False # set to true if we want to listen for DL message
_LORA_SOCKET_BUFFER_SIZE = 128 # max buffer for rx
