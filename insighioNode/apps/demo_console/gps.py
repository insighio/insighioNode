import logging
from utime import ticks_ms, sleep_ms, time
from ..dictionary_utils import set_value
from device_info import get_reset_cause
from utils import writeToFlagFile


def init(cfg):
    pass


def deinit():
    pass


def get_gps_position(cfg, measurements, keep_open=False):
    try:
        if cfg.get("meas-gps-enabled") and (not cfg.get("meas-gps-only-on-boot") or (get_reset_cause() == 0 or get_reset_cause() == 1)):
            gps_status = False
            network_cfg = cfg.get("network")
            if network_cfg == "cellular" or network_cfg == "wifi":
                return internal_modem_get_position(cfg, measurements, keep_open)
            elif network_cfg == "lora" or network_cfg == "satellite":
                return external_modem_get_position(cfg, measurements, keep_open)
    except Exception as e:
        logging.exception(e, "GPS Exception:")

    return False


def coord_to_double(part1, part2, part3):
    try:
        direction = {"N": 1, "S": -1, "E": 1, "W": -1}
        return (int(part1) + float(part2) / 60.0) * direction[part3]
    except Exception as e:
        logging.exception(e, "error converting coord {} {} {}".format(part1, part2, part3))
        return None


def internal_modem_get_position(cfg, measurements, always_on):
    from . import cellular as network_gps

    network_gps.init(cfg)

    gps_status = network_gps.get_gps_position(cfg, measurements, always_on)

    # close modem after operation if it is not going to be used for connection
    if cfg.get("network") != "cellular":
        network_gps.disconnect()
    return gps_status


def external_modem_get_position(cfg, measurements, always_on):
    # the following is to be relocated in the future
    from external.kpn_senml.senml_unit import SenmlUnits, SenmlSecondaryUnits
    from networking.modem import modem_gps_l76l

    gps_status = False
    modem = modem_gps_l76l.ModemGPSL76L(
        cfg.get("_UC_IO_RADIO_GPS_ON"),
        cfg.get("_UC_GPS_RESET"),
        cfg.get("_UC_IO_I2C_SCL"),
        cfg.get("_UC_IO_I2C_SDA"),
        cfg.get("_I2C_GPS_ADDRESS"),
    )
    modem.power_on()
    modem_ready = modem.wait_for_modem_power_on()
    if modem_ready:
        modem.init()

        start_time = ticks_ms()

        timeout_ms = 120000
        min_satellite_fix_num = 4
        if cfg.has("meas-gps-timeout"):
            timeout_ms = cfg.get("meas-gps-timeout") * 1000

        if cfg.has("meas-gps-sat-num"):
            min_satellite_fix_num = cfg.get("meas-gps-sat-num")

        (gps_timestamp, lat, lon, num_of_sat, hdop) = modem.get_gps_position(timeout_ms, min_satellite_fix_num)
        set_value(measurements, "gps_dur", ticks_ms() - start_time, SenmlSecondaryUnits.SENML_SEC_UNIT_MILLISECOND)
        if lat is not None and lon is not None:
            latD = coord_to_double(lat[0], lat[1], lat[2])
            lonD = coord_to_double(lon[0], lon[1], lon[2])
            set_value(measurements, "gps_lat", latD, SenmlUnits.SENML_UNIT_DEGREES_LATITUDE)
            set_value(measurements, "gps_lon", lonD, SenmlUnits.SENML_UNIT_DEGREES_LONGITUDE)
            set_value(measurements, "gps_num_of_sat", num_of_sat)
            set_value(measurements, "gps_hdop", hdop)
            gps_status = True

        update_system_time(gps_timestamp)

    if not always_on:
        modem.power_off()
    return gps_status


def update_system_time(gps_timestamp):
    if gps_timestamp is None:
        return

    from machine import RTC

    rtc = RTC()

    # wrong time set, try to get time from other source
    now = rtc.datetime()

    time_tuple = (
        now[0],
        now[1],
        now[2],
        0,
        gps_timestamp[4],
        gps_timestamp[5],
        int(gps_timestamp[6]),
        0,
    )

    logging.debug("Setting cellular RTC with: " + str(time_tuple))

    epoch_before = time()
    rtc.datetime(time_tuple)
    epoch_diff = time() - epoch_before
    writeToFlagFile("/epoch_diff", "{}".format(epoch_diff))

    logging.debug("New RTC: " + str(rtc.datetime()))
