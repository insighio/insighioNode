try:
    from . import demo_config as cfg
except Exception as e:
    cfg = type('', (), {})()
import json
import utils
import logging
import utime
import device_info

storage_file_name = "measurements.log"
MAX_NUMBER_OF_FORCED_MESSAGES=1000

def timestamp_measurements(measurements):
    offset = 0
    if device_info.is_esp32():
        offset = 946684800

    timezone_offset = utils.getKeyValueInteger("tz_sec_offset")

    if timezone_offset is not None:
        offset -= timezone_offset

    epoch = utime.time() + offset

    # Friday, April 15, 2022
    if epoch > 1650000000:
        measurements["dt"] = {"value": epoch}   # time offset 1970 -> 2000


def store_measurement_if_needed(measurements, force_store=False):
    if cfg._BATCH_UPLOAD_MESSAGE_BUFFER is None and not force_store:
        logging.error("Batch upload not activated, ignoring")
        return False

    # +1 is added to count the current measurement that has not been stored to the file
    number_of_measurements = utils.countFileLines(storage_file_name) + 1
    logging.info("Message " + str(number_of_measurements) + " of " + str(cfg._BATCH_UPLOAD_MESSAGE_BUFFER))

    if number_of_measurements < cfg._BATCH_UPLOAD_MESSAGE_BUFFER or (force_store and number_of_measurements < MAX_NUMBER_OF_FORCED_MESSAGES):
        data = json.dumps(measurements) + "\n"
        utils.appendToFile(storage_file_name, data)
        logging.debug("Measurement stored: " + str(measurements))
        return True
    return False


def parse_stored_measurements_and_upload(network):
    # load stored measurements
    failed_messages = []
    stored_measurements_str = utils.readFromFile(storage_file_name)
    uploaded_measurement_count = 0
    for line in stored_measurements_str.split('\n'):
        utime.sleep_ms(50)
        try:
            if not line:
                continue
            message = network.create_message(cfg.device_id, json.loads(line))
            message_send_status = network.send_message(cfg, message)

            logging.debug("Message send status: " + str(message_send_status))

            # this only works for BG600 modem since it supports correct message transmission status
            if message_send_status is not None and not message_send_status:
                logging.info("Failed message appended for future upload: " + str(line))
                failed_messages.append(line + "\n")
            else:
                uploaded_measurement_count += 1
        except Exception as e:
            logging.exception(e, "error reading line: ", line)

    if uploaded_measurement_count > 0:
        utils.deleteFile(storage_file_name)

        # if failed messages were logged, recreate the file to upload during next connection
        for failed_message in failed_messages:
            utils.appendToFile(storage_file_name, failed_message)
