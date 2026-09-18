import logging

from external.kpn_senml.senml_unit import SenmlUnits
from external.kpn_senml.senml_unit import SenmlSecondaryUnits

from .dictionary_utils import set_value
from .sdi12_response_parsers import parse_generic_sdi12
from .sdi12_response_parsers import parse_sensor_acclima
from .sdi12_response_parsers import parse_sensor_implexx
from .sdi12_response_parsers import parse_sensor_licor
from .sdi12_response_parsers import parse_sensor_meter

TIMING_OPTIONS = (
    (1.5, 1.0, 100, 50),
    (1.5, 1.1, 160, 110),
    (1.7, 1.0, 160, 80),
    (1.7, 1.2, 160, 160),
    (1.9, 1.2, 160, 100),
    (1.9, 1.2, 160, 80),
    (1.9, 1.8, 160, 140),
    (1.9, 1.8, 160, 20),
    (1.9, 1.8, 160, 40),
)


def detect_timing(sdi12, addresses, start_index=0, watchdog_reset=None):
    if start_index >= len(TIMING_OPTIONS):
        logging.error("detect_timing - Invalid start_index: {}, timing options length: {}".format(start_index, len(TIMING_OPTIONS)))
        return (False, -1, None)

    timing_index = start_index
    while timing_index < len(TIMING_OPTIONS):
        timing = TIMING_OPTIONS[timing_index]
        sdi12.break_level_multiplier = timing[0]
        sdi12.mark_level_multiplier = timing[1]
        sdi12.sleep_period_us_before_write = timing[2]
        sdi12.sleep_period_us_after_write = timing[3]

        logging.debug("detect_timing - Trying timing: {}".format(timing))

        all_sensors_active = True
        for address in addresses:
            if watchdog_reset:
                watchdog_reset()
            address = str(address)
            is_active = sdi12.is_active(address)
            if not is_active:
                all_sensors_active = False
                break
            manufacturer, model = sdi12.get_sensor_info(address)
            if not manufacturer or not model:
                all_sensors_active = False
                break

        if all_sensors_active:
            logging.debug("detect_timing - Found working timing: {}".format(timing))
            return (True, timing_index, timing)

        timing_index += 1

    return (False, -1, None)


def identify_sensor(sdi12, address, measurements, retries=3):
    address = str(address)
    is_active = False

    for _ in range(retries):
        is_active = sdi12.is_active(address)
        logging.debug("identify_sensor - address: {}, is_active: {}".format(address, is_active))
        if is_active:
            break

    if not is_active:
        set_value(measurements, "sdi12_{}_e".format(address), "not_found", None)
        logging.error("identify_sensor - No sensor found at address: [{}]".format(address))
        return (False, "", "")

    manufacturer = ""
    model = ""
    for _ in range(retries):
        manufacturer, model = sdi12.get_sensor_info(address)
        logging.debug("identify_sensor - manufacturer: {}, model: {}".format(manufacturer, model))
        if manufacturer and model:
            break

    manufacturer = manufacturer.lower().strip() if manufacturer else ""
    model = model.lower().strip() if model else ""

    if manufacturer:
        set_value(measurements, "sdi12_{}_i".format(address), manufacturer, None)
    if model:
        set_value(measurements, "sdi12_{}_m".format(address), model, None)

    return (True, manufacturer, model)


def read_measurement(
    sdi12,
    measurements,
    address,
    manufacturer,
    model,
    command,
    location=None,
    force_wait=True,
    measurement_count=1,
):
    address = str(address)
    response = sdi12.get_measurement(address, command, measurement_count, force_wait)
    if response:
        parse_sdi12_sensor_response(manufacturer, model, address, command, response, measurements, location)
    return response


def parse_sdi12_sensor_response(manufacturer, model, address, command, response, measurements, location=None):
    if manufacturer == "meter":
        parse_sensor_meter(model, command, address, response, measurements, location)
    elif manufacturer == "in-situ" and (model == "at500" or model == "at400"):
        parse_generic_sdi12(address, response, measurements, "sdi12", None, "", location)
    elif manufacturer == "acclima" and command == "M":
        parse_sensor_acclima(model, command, address, response, measurements, location)
    elif manufacturer == "implexx" and command == "M":
        parse_sensor_implexx(model, command, address, response, measurements, location)
    elif manufacturer == "ep100g":
        if command == "C":
            parse_generic_sdi12(address, response, measurements, "ep_vwc", SenmlSecondaryUnits.SENML_SEC_UNIT_PERCENT, "", location)
        elif command == "C1":
            parse_generic_sdi12(address, response, measurements, "ep_ec", "uS/cm", "", location)
        elif command == "C2":
            parse_generic_sdi12(address, response, measurements, "ep_temp", SenmlUnits.SENML_UNIT_DEGREES_CELSIUS, "", location)
        elif command == "C5":
            parse_generic_sdi12(address, response, measurements, "ep_temp", SenmlSecondaryUnits.SENML_SEC_UNIT_FAHRENHEIT, "", location)
    elif "li-cor" in manufacturer and command == "M0":
        parse_sensor_licor(model, command, address, response, measurements, location)
    else:
        parse_generic_sdi12(address, response, measurements, "sdi12", None, "_" + command.lower(), location)


def set_no_response_error(measurements, address):
    address = str(address)
    set_value(measurements, "sdi12_{}_e".format(address), "no_response", None)
    logging.error("No response from SDI-12 sensor at address: [{}]".format(address))
