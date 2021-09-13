from . import demo_config as cfg
import json
import utils
import logging
import utime

storage_file_name = "measurements.log"


def timestamp_measurements(measurements):
    measurements["dt"] = {"value": utime.time() + 946684800}   # time offset 1970 -> 2000
    return


def store_measurement_if_needed(measurements):
    if cfg._BATCH_UPLOAD_MESSAGE_BUFFER is None:
        logging.error("Batch upload not activated, ignoring")
        return False

    # +1 is added to count the current measurement that has not been stored to the file
    number_of_measurements = utils.countFileLines(storage_file_name) + 1
    logging.info("Message " + str(number_of_measurements) + " of " + str(cfg._BATCH_UPLOAD_MESSAGE_BUFFER))

    if number_of_measurements < cfg._BATCH_UPLOAD_MESSAGE_BUFFER:
        data = json.dumps(measurements) + "\n"
        utils.appendToFile(storage_file_name, data)
        logging.debug("Measurement stored: " + str(measurements))
        return True
    return False


def parse_stored_measurements_and_upload(network):
    # load stored measurements
    loaded_measurements = []
    stored_measurements_str = utils.readFromFile(storage_file_name)
    for line in stored_measurements_str.splitlines():
        try:
            if line:
                loaded_measurements.append(json.loads(line))
        except Exception as e:
            logging.exception(e, "error reading line: ", line)

    if loaded_measurements and len(loaded_measurements) > 0:
        failed_messages = []
        for past_measurement in loaded_measurements:
            utime.sleep_ms(500)
            message = network.create_message(cfg.device_id, past_measurement)
            message_send_status = network.send_message(cfg, message)

            logging.debug("Message send status: " + str(message_send_status))

            # this only works for BG600 modem since it supports correct message transmission status
            if message_send_status is not None and not message_send_status:
                logging.info("Failed message appended for future upload: " + str(past_measurement))
                failed_messages.append(past_measurement)
        utils.deleteFile(storage_file_name)

        # if failed messages were logged, recreate the file to upload during next connection
        for failed_message in failed_messages:
            utils.appendToFile(storage_file_name, failed_message)
