import utime
import logging
from external.astronode import astronode

class ModemAstronode:
    def __init__(self, modem_tx=None, modem_rx=None):
        self.modem_instance = False

        if modem_tx is not None and modem_rx is not None:
            self.modem_instance = astronode.ASTRONODE(pin_modem_tx, pin_modem_rx)

        self.prefCfg = astronode.ASTRONODE.ASTRONODE_CONFIG()
        self.prefCfg.with_deep_sleep_en = 0
        self.prefCfg.with_ephemeris = 4
        self.prefCfg.with_geoloc = 0
        self.prefCfg.with_msg_ack_pin_en = 0
        self.prefCfg.with_msg_reset_pin_en = 0
        self.prefCfg.with_pl_ack = 0

    def is_alive(self):
        return self.modem_instance.is_alive()

    def print_status(self):
        (status, pn) = self.modem_instance.product_number_read()
        (status, guid) = self.modem_instance.guid_read()
        (status, sn) = self.modem_instance.serial_number_read()
        (status, config) = modem.configuration_read()

        logging.info("Product Number: {}".format(pn))
        logging.info("GUID: {}".format(guid))
        logging.info("S/N: {}".format(sn))

        if config:
            logging.info("product_id: {}, hardware_rev: {}".format(config.product_id, config.hardware_rev))
            logging.info("firmware version: {}.{}.{}".format(config.firmware_maj_ver, config.firmware_min_ver, config.firmware_rev))

    def get_model(self):
        (status, pn) = self.modem_instance.product_number_read()
        return pn

    def set_default_configuration(self):
        (status, config) =  self.modem_instance.configuration_read()
        if config is None:
            logging.error("error getting device configuration")
            return
        logging.info("product_id: {}, hardware_rev: {}".format(config.product_id, config.hardware_rev))
        logging.info("firmware version: {}.{}.{}".format(config.firmware_maj_ver, config.firmware_min_ver, config.firmware_rev))

        self.prefCfg = astronode.ASTRONODE.ASTRONODE_CONFIG()
        self.prefCfg.with_deep_sleep_en = 0
        self.prefCfg.with_ephemeris = 4
        self.prefCfg.with_geoloc = 0
        self.prefCfg.with_msg_ack_pin_en = 0
        self.prefCfg.with_msg_reset_pin_en = 0
        self.prefCfg.with_pl_ack = 0
        if config.with_deep_sleep_en != self.prefCfg.with_deep_sleep_en or\
            config.with_ephemeris != self.prefCfg.with_ephemeris or\
            config.with_geoloc != self.prefCfg.with_geoloc or\
            config.with_msg_ack_pin_en != self.prefCfg.with_msg_ack_pin_en or\
            config.with_msg_reset_pin_en != self.prefCfg.with_msg_reset_pin_en or\
            config.with_pl_ack != self.prefCfg.with_pl_ack:
            logging.info("modem requires configuration update")
            (status, _) = self.modem_instance.configuration_write(self.prefCfg.with_pl_ack,
                                        self.prefCfg.with_geoloc,
                                        self.prefCfg.with_ephemeris,
                                        self.prefCfg.with_deep_sleep_en,
                                        self.prefCfg.with_msg_ack_pin_en,
                                        self.prefCfg.with_msg_reset_pin_en)
            logging.info("configuration update: {}".format("ok" if (status == astronode.ANS_STATUS_SUCCESS) else "failed"))
        else:
            logging.info("modem configuration ok")

    def send_payload(self, payload):
        (status, message_id) = self.modem_instance.enqueue_payload(payload)
        if status == astronode.ANS_STATUS_BUFFER_FULL:
            logging.info("message buffer full, about to dequeue oldest message")
            (status, message_id) = self.modem_instance.dequeue_payload()
        return (status == astronode.ANS_STATUS_SUCCESS)
