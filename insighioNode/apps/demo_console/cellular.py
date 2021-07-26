from networking import cellular
from external.kpn_senml.senml_pack_json import SenmlPackJson
from external.kpn_senml.senml_record import SenmlRecord
from external.kpn_senml.senml_unit import SenmlUnits
from external.kpn_senml.senml_unit import SenmlSecondaryUnits
import logging
import device_info
import utime


# network connection
def connect(cfg):
    logging.info("Connecting to cellular...")
    enableDataState = (cfg._IP_VERSION == "IP")
    results = {}

    if device_info.is_esp32():
        cellular.set_pins(cfg._UC_IO_RADIO_ON, cfg._UC_IO_PWRKEY, cfg._UC_UART_MODEM_TX, cfg._UC_UART_MODEM_RX)

    modem_instance = cellular.get_modem_instance()
    logging.debug("demo_console: cellular connect modem instance is None: " + str(modem_instance is None))
    if modem_instance is not None:
        (status, activation_duration, attachment_duration, connection_duration, rssi, rsrp, rsrq) = cellular.connect(cfg, dataStateOn=enableDataState)
        results["status"] = {"value": (status == cellular.MODEM_CONNECTED)}

        # if network statistics are enabled
        if cfg._MEAS_NETWORK_STAT_ENABLE:
            results["cell_act_duration"] = {"unit": SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND, "value": activation_duration}
            results["cell_att_duration"] = {"unit": SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND, "value": attachment_duration}
            if rssi:
                results["cell_rssi"] = {"unit": SenmlSecondaryUnits.SENML_SEC_UNIT_DECIBEL_MILLIWATT, "value": rssi}
            if rsrp:
                results["cell_rsrp"] = {"unit": SenmlSecondaryUnits.SENML_SEC_UNIT_DECIBEL_MILLIWATT, "value": rsrp}
            if rsrq:
                results["cell_rsrq"] = {"unit": SenmlSecondaryUnits.SENML_SEC_UNIT_DECIBEL_MILLIWATT, "value": rsrq}
            if not cfg.protocol_config.use_custom_socket:
                results["cell_con_duration"] = {"unit": SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND, "value": connection_duration}

    return results


def coord_to_double(part1, part2, part3):
    try:
        direction = {'N': 1, 'S': -1, 'E': 1, 'W': -1}
        return (int(part1) + float(part2) / 60.0) * direction[part3]
    except Exception as e:
        logging.exception(e, "error converting coord {} {} {}".format(part1, part2, part3))
        return None


def get_gps_position(cfg, measurements):
    if device_info.is_esp32():
        cellular.set_pins(cfg._UC_IO_RADIO_ON, cfg._UC_IO_PWRKEY, cfg._UC_UART_MODEM_TX, cfg._UC_UART_MODEM_RX)

    modem_instance = cellular.get_modem_instance()
    if modem_instance is not None:
        modem_instance.set_gps_state(True)
        if modem_instance.is_gps_on():
            start_time = utime.ticks_ms()
            (_, lat, lon, num_of_sat, hdop) = modem_instance.get_gps_position(180000)
            measurements["gps_dur"] = {"unit": SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND, "value": utime.ticks_ms() - start_time}
            if lat is not None and lon is not None:
                latD = coord_to_double(lat[0], lat[1], lat[2])
                lonD = coord_to_double(lon[0], lon[1], lon[2])
                measurements["gps_lat"] = {"unit": SenmlUnits.SENML_UNIT_DEGREES_LATITUDE, "value": latD}
                measurements["gps_lon"] = {"unit": SenmlUnits.SENML_UNIT_DEGREES_LONGITUDE, "value": lonD}
                measurements["gps_num_of_sat"] = {"value": num_of_sat}
                measurements["gps_hdop"] = {"value": hdop}
        modem_instance.set_gps_state(False)


def create_message(device_id, measurements):
    message = SenmlPackJson(device_id + '-')

    for key in measurements:
        if "unit" in measurements[key]:
            message.add(SenmlRecord(key, unit=measurements[key]["unit"], value=measurements[key]["value"]))
        else:
            message.add(SenmlRecord(key, value=measurements[key]["value"]))

    return message.to_json()


def send_message(cfg, message):
    modem_instance = cellular.get_modem_instance()
    if modem_instance is not None and modem_instance.get_model() == 'bg600l-m3':
        (mqtt_ready, _) = modem_instance.send_at_cmd('AT+QMTOPEN=0,"' + cfg.protocol_config.server_ip + '",' + str(cfg.protocol_config.server_port), 15000, "\\+QMTOPEN:\\s+0,0")

        if not mqtt_ready:
            logging.error("Mqtt not ready")
            return False

        # mqtt_conn, _) = modem_instance.send_at_cmd('AT+QMTCONN=0,"client","a93d2353-c664-4487-b52c-ae3bd73b06c4","ed1d8997-a8b1-46c1-8927-04fb35dd93af"')
        (mqtt_conn, _) = modem_instance.send_at_cmd('AT+QMTCONN=0,"{}","{}","{}"'.format(cfg.protocol_config.thing_id, cfg.protocol_config.thing_id, cfg.protocol_config.thing_token), 15000, "\\+QMTCONN:\\s+0,0,0")

        if not mqtt_conn:
            logging.error("Mqtt not connected")
            return False

        topic = 'channels/{}/messages/{}'.format(cfg.protocol_config.message_channel_id, cfg.protocol_config.thing_id)

        for i in range(0, 4):
            (mqtt_send_ready, _) = modem_instance.send_at_cmd('AT+QMTPUB=0,1,1,0,"' + topic + '"', 15000, '>')
            if mqtt_send_ready:
                (mqtt_send_ok, _) = modem_instance.send_at_cmd(message + '\x1a')
                return mqtt_send_ok

            logging.error("Mqtt not ready to send")

        return False
    else:
        from . import transfer_protocol
        return transfer_protocol.send_packet(cfg, message)


def disconnect():
    logging.info("Deactivate NB-IOT: {}".format(cellular.deactivate()))
