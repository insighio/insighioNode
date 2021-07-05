import sys
import device_info

CELLULAR_NO_INIT = None
CELLULAR_NO      = 0
CELLULAR_SEQUANS = 1
CELLULAR_MC60    = 2
CELLULAR_BG600   = 3
CELLULAR_UNKNOWN = 4

CELLULAR_MC60_STR  = "MC60"
CELLULAR_BG600_STR = "BG600"

cellular_model = CELLULAR_NO
modem_instance = None


def get_modem_id():
    global cellular_model
    return cellular_model


def detect_modem(cfg):
    global cellular_model
    if sys.platform == 'esp32':
        from networking.modem.modem_base import Modem
        uart1 = UART(1)
        uart1.init(115200, bits=8, parity=None, stop=1, tx=cfg.MODEM_PIN_TX, rx=cfg.MODEM_PIN_RX, timeout=500, timeout_char=1000)
        modemInst = Modem(uart1)
        model_name = modemInst.get_model()
        modemInst = None
        uart1 = None
        if not model_name:
            cellular_model = CELLULAR_NO
        elif model_name == CELLULAR_MC60_STR:
            cellular_model = CELLULAR_MC60
        elif model_name == CELLULAR_BG600_STR:
            cellular_model = CELLULAR_BG600
        else:
            cellular_model = CELLULAR_UNKNOWN
    else:
        try:
            import pycom
            cellular_model = CELLULAR_SEQUANS if sys.platform in device_info._LTE_COMPATIBLE_PLATFORMS else CELLULAR_NO
        except Exception as e:
            cellular_model = CELLULAR_NO
    return cellular_model


def get_modem_instance(cfg):
    global modem_instance
    if modem_instance is None:
        modem_id = get_modem_id()
        if modem_id == CELLULAR_NO_INIT:
            modem_id = detect_modem(cfg)

        if modem_id == CELLULAR_MC60 or modem_id == CELLULAR_BG600 or modem_id == CELLULAR_UNKNOWN:
            uart1 = UART(1)
            uart1.init(115200, bits=8, parity=None, stop=1, tx=cfg.MODEM_PIN_TX, rx=cfg.MODEM_PIN_RX, timeout=500, timeout_char=1000)

            if modem_id == CELLULAR_MC60:
                from networking.modem.modem_mc60 import ModemMC60
                modem_instance = ModemMC60(uart1)
            elif modem_id == CELLULAR_BG600:
                from networking.modem.modem_bg600 import ModemBG600
                modem_instance = ModemBG600(uart1)
            else:
                from networking.modem.modem_base import Modem
                modem_instance = Modem(uart1)  # generic
        elif modem_id == CELLULAR_SEQUANS:
            from networking.modem.modem_sequans import ModemSequans
            modem_instance = ModemSequans()

    return modem_instance
