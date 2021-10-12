from networking import cellular
from external.kpn_senml.senml_pack_json import SenmlPackJson
from external.kpn_senml.senml_record import SenmlRecord
from external.kpn_senml.senml_unit import SenmlUnits
from external.kpn_senml.senml_unit import SenmlSecondaryUnits
import logging
import device_info
import utime

transfer_client = None
mqtt_connected = False


def add_value_if_valid(results, key, value, unit=None):
    if value is None:
        return
    elif unit:
        results[key] = {"unit": unit, "value": value}
    else:
        results[key] = {"value": value}


# network connection
def connect(cfg):
    logging.info("Connecting to cellular...")
    protocol_config = cfg.get_protocol_config()
    enableDataState = (cfg._IP_VERSION == "IP")
    results = {}

    if device_info.is_esp32():
        cellular.set_pins(cfg._UC_IO_RADIO_ON, cfg._UC_IO_PWRKEY, cfg._UC_UART_MODEM_TX, cfg._UC_UART_MODEM_RX)

    modem_instance = cellular.get_modem_instance()

    try:
        if cfg.RTC_USE_TIMEZONE_OVER_GMT is not None:
            modem_instance.use_timezone_over_gmt = cfg.RTC_USE_TIMEZONE_OVER_GMT
    except Exception as e:
        pass

    logging.debug("demo_console: cellular connect modem instance is None: " + str(modem_instance is None))
    if modem_instance is not None and modem_instance.has_sim():
        (status, activation_duration, attachment_duration, connection_duration, rssi, rsrp, rsrq) = cellular.connect(cfg, dataStateOn=enableDataState)
        add_value_if_valid(results, "status", status == cellular.MODEM_CONNECTED)

        # if network statistics are enabled
        if cfg._MEAS_NETWORK_STAT_ENABLE:
            (mcc, mnc) = modem_instance.get_registered_mcc_mnc()
            (lac, ci) = modem_instance.get_lac_n_cell_id()

            add_value_if_valid(results, "cell_act_duration", activation_duration, SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND)
            add_value_if_valid(results, "cell_att_duration", attachment_duration, SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND)
            if not protocol_config.use_custom_socket:
                add_value_if_valid(results, "cell_con_duration", connection_duration, SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND)

            add_value_if_valid(results, "cell_rssi", rssi, SenmlSecondaryUnits.SENML_SEC_UNIT_DECIBEL_MILLIWATT)
            add_value_if_valid(results, "cell_rsrp", rsrp, SenmlSecondaryUnits.SENML_SEC_UNIT_DECIBEL_MILLIWATT)
            add_value_if_valid(results, "cell_rsrq", rsrq, SenmlSecondaryUnits.SENML_SEC_UNIT_DECIBEL_MILLIWATT)

            add_value_if_valid(results, "cell_mcc", mcc)
            add_value_if_valid(results, "cell_mnc", mnc)
            add_value_if_valid(results, "cell_lac", lac)
            add_value_if_valid(results, "cell_ci", ci)

        if status == cellular.MODEM_CONNECTED:
            global transfer_client
            from . import transfer_protocol

            # AT command based implementation of communication of Quectel BG600L
            if modem_instance.get_model() == 'bg600l-m3':
                transfer_client = transfer_protocol.TransferProtocol(cfg, modem_instance)
            else:
                transfer_client = transfer_protocol.TransferProtocol(cfg)

            transfer_client.connect()

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
        for i in range(0, 3):
            if modem_instance.set_gps_state(True):
                break
            modem_instance.set_gps_state(False)
            utime.sleep_ms(500)

        if modem_instance.is_gps_on():
            start_time = utime.ticks_ms()

            timeout_ms = 120000
            min_satellite_fix_num = 4
            try:
                timeout_ms = cfg._MEAS_GPS_TIMEOUT * 1000
            except:
                pass
            try:
                min_satellite_fix_num = cfg._MEAS_GPS_SATELLITE_FIX_NUM
            except:
                pass

            (_, lat, lon, num_of_sat, hdop) = modem_instance.get_gps_position(timeout_ms, min_satellite_fix_num)
            add_value_if_valid(measurements, "gps_dur", utime.ticks_ms() - start_time, SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND)
            if lat is not None and lon is not None:
                latD = coord_to_double(lat[0], lat[1], lat[2])
                lonD = coord_to_double(lon[0], lon[1], lon[2])
                add_value_if_valid(measurements, "gps_lat", latD, SenmlUnits.SENML_UNIT_DEGREES_LATITUDE)
                add_value_if_valid(measurements, "gps_lon", lonD, SenmlUnits.SENML_UNIT_DEGREES_LONGITUDE)
                add_value_if_valid(measurements, "gps_num_of_sat", num_of_sat)
                add_value_if_valid(measurements, "gps_hdop", hdop)
        modem_instance.set_gps_state(False)


def create_message(device_id, measurements):
    message = SenmlPackJson(device_id + '-')

    if "dt" in measurements:
        message.base_time = measurements["dt"]["value"]

    for key in measurements:
        if "unit" in measurements[key]:
            message.add(SenmlRecord(key, unit=measurements[key]["unit"], value=measurements[key]["value"]))
        elif key != "dt":
            message.add(SenmlRecord(key, value=measurements[key]["value"]))

    return message.to_json()


def send_message(cfg, message):
    if transfer_client is not None:
        return transfer_client.send_packet(message)
    return False


def disconnect():
    global transfer_client
    if transfer_client is not None:
        transfer_client.disconnect()
        transfer_client = None
    logging.info("Deactivate cellular: {}".format(cellular.deactivate()))


def checkAndApplyOTA(cfg):
    if transfer_client is not None:
        from . import ota
        ota.checkAndApply(transfer_client)
