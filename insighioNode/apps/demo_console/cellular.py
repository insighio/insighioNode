from networking import cellular
from external.kpn_senml.senml_pack_json import SenmlPackJson
from external.kpn_senml.senml_record import SenmlRecord
from external.kpn_senml.senml_unit import SenmlUnits
from external.kpn_senml.senml_unit import SenmlSecondaryUnits
import logging
import device_info
import utime
from . import demo_utils

transfer_client = None
mqtt_connected = False

def add_value_if_valid(results, key, value, unit=None):
    if value is None:
        return
    elif unit:
        results[key] = {"unit": unit, "value": value}
    else:
        results[key] = {"value": value}

def init(cfg):
    if device_info.is_esp32():
        cellular.set_pins(cfg._UC_IO_RADIO_ON, cfg._UC_IO_PWRKEY, cfg._UC_UART_MODEM_TX, cfg._UC_UART_MODEM_RX)

def prepareForConnectAndUpload():
    modem_instance = cellular.get_modem_instance()
    if modem_instance is None:
        return
    modem_instance.prioritizeWWAN()

def prepareForGPS():
    modem_instance = cellular.get_modem_instance()
    if modem_instance is None:
        return
    modem_instance.prioritizeGNSS()

def updateSignalQuality(cfg, measurements):
    if not cfg._MEAS_NETWORK_STAT_ENABLE:
        return

    modem_instance = cellular.get_modem_instance()
    if modem_instance is None:
        return

    rssi = modem_instance.get_rssi()
    (rsrp, rsrq) = modem_instance.get_extended_signal_quality()
    (mcc, mnc) = modem_instance.get_registered_mcc_mnc()
    (lac, ci) = modem_instance.get_lac_n_cell_id()

    add_value_if_valid(measurements, "cell_rssi", rssi, SenmlSecondaryUnits.SENML_SEC_UNIT_DECIBEL_MILLIWATT)
    add_value_if_valid(measurements, "cell_rsrp", rsrp, SenmlSecondaryUnits.SENML_SEC_UNIT_DECIBEL_MILLIWATT)
    add_value_if_valid(measurements, "cell_rsrq", rsrq, SenmlSecondaryUnits.SENML_SEC_UNIT_DECIBEL_MILLIWATT)

    add_value_if_valid(measurements, "cell_mcc", mcc)
    add_value_if_valid(measurements, "cell_mnc", mnc)
    add_value_if_valid(measurements, "cell_lac", lac)
    add_value_if_valid(measurements, "cell_ci", ci)

# network connection
def connect(cfg):
    logging.info("Connecting to cellular...")
    protocol_config = cfg.get_protocol_config()
    results = {}

    modem_instance = cellular.get_modem_instance()

    logging.debug("demo_console: cellular connect modem instance is None: " + str(modem_instance is None))
    if modem_instance is None or not modem_instance.has_sim():
        return results

    (status, activation_duration, attachment_duration, connection_duration, _, _, _) = cellular.connect(cfg)
    add_value_if_valid(results, "status", status == cellular.MODEM_CONNECTED)

    # if network statistics are enabled
    if cfg._MEAS_NETWORK_STAT_ENABLE:

        add_value_if_valid(results, "cell_act_duration", activation_duration, SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND)
        add_value_if_valid(results, "cell_att_duration", attachment_duration, SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND)
        if not protocol_config.use_custom_socket:
            add_value_if_valid(results, "cell_con_duration", connection_duration, SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND)

    if status == cellular.MODEM_CONNECTED:
        global transfer_client
        from . import transfer_protocol

        # AT command based implementation of communication of Quectel BG600L
        modem_model = modem_instance.get_model()
        if modem_model and 'bg600' in modem_model:
            transfer_client = transfer_protocol.TransferProtocolModemAT(cfg, modem_instance)
        elif cfg.protocol == 'coap':
            transfer_client = transfer_protocol.TransferProtocolCoAP(cfg)
        elif cfg.protocol == 'mqtt':
            transfer_client = transfer_protocol.TransferProtocolMQTT(cfg)
        else:
            transfer_client = None

        transfer_client.connect()

    return results


def is_connected():
    modem_instance = cellular.get_modem_instance()
    return modem_instance and transfer_client and modem_instance.is_connected() and transfer_client.is_connected()


def coord_to_double(part1, part2, part3):
    try:
        direction = {'N': 1, 'S': -1, 'E': 1, 'W': -1}
        return (int(part1) + float(part2) / 60.0) * direction[part3]
    except Exception as e:
        logging.exception(e, "error converting coord {} {} {}".format(part1, part2, part3))
        return None


def get_gps_position(cfg, measurements, keep_open=False):
    modem_instance = cellular.get_modem_instance()
    if modem_instance is None:
        return
    if not modem_instance.is_gps_on():
        for i in range(0, 10):
            if modem_instance.set_gps_state(True):
                break
            modem_instance.set_gps_state(False)
            utime.sleep_ms(500)

    if modem_instance.is_gps_on():
        start_time = utime.ticks_ms()

        timeout_ms = 120000
        min_satellite_fix_num = 4
        if hasattr(cfg, "_MEAS_GPS_TIMEOUT"):
            timeout_ms = cfg._MEAS_GPS_TIMEOUT * 1000

        if hasattr(cfg, "_MEAS_GPS_SATELLITE_FIX_NUM"):
            min_satellite_fix_num = cfg._MEAS_GPS_SATELLITE_FIX_NUM

        (_, lat, lon, num_of_sat, hdop) = modem_instance.get_gps_position(timeout_ms, min_satellite_fix_num)
        add_value_if_valid(measurements, "gps_dur", utime.ticks_ms() - start_time, SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND)
        if lat is not None and lon is not None:
            latD = coord_to_double(lat[0], lat[1], lat[2])
            lonD = coord_to_double(lon[0], lon[1], lon[2])
            add_value_if_valid(measurements, "gps_lat", latD, SenmlUnits.SENML_UNIT_DEGREES_LATITUDE)
            add_value_if_valid(measurements, "gps_lon", lonD, SenmlUnits.SENML_UNIT_DEGREES_LONGITUDE)
            add_value_if_valid(measurements, "gps_num_of_sat", num_of_sat)
            add_value_if_valid(measurements, "gps_hdop", hdop)
    if not keep_open:
        modem_instance.set_gps_state(False)


def create_message(device_id, measurements):
    message = SenmlPackJson((device_id + '-') if device_id is not None else None)

    if "dt" in measurements:
        message.base_time = measurements["dt"]["value"]

    for key in measurements:
        logging.debug("[{}]={} - {}".format(key, measurements[key], type(measurements[key])))
        if isinstance(measurements[key], dict):
            if "unit" in measurements[key]:
                message.add(SenmlRecord(key, unit=measurements[key]["unit"], value=measurements[key]["value"]))
            elif key != "dt":
                message.add(SenmlRecord(key, value=measurements[key]["value"]))
        elif measurements[key] is not None:
            message.add(SenmlRecord(key, value=measurements[key]))

    return message.to_json()


def send_message(cfg, message):
    if transfer_client is not None:
        return transfer_client.send_packet(message)
    return False

def send_control_message(cfg, message, configSubtopic):
    if transfer_client is not None:
        return transfer_client.send_control_packet(message, configSubtopic)
    return False

def disconnect():
    global transfer_client
    if transfer_client is not None:
        transfer_client.disconnect()
        transfer_client = None
    logging.info("Deactivate cellular: {}".format(cellular.deactivate()))


def check_and_apply_ota(cfg):
    if transfer_client is not None:
        from . import ota
        ota.checkAndApply(transfer_client)
