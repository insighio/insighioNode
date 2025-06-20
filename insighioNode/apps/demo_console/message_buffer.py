import logging

from .. import cfg
import json
import utils
import utime
import _thread

storage_file_name = "measurements.log"
MAX_NUMBER_OF_FORCED_MESSAGES = 1000

message_buffer_size = cfg.get("batch-upload-buffer-size")

mutex = _thread.allocate_lock()


def buffered_measurements_count():
    return utils.countFlagFileLines(storage_file_name)


def timestamp_measurements(measurements):
    offset = 946684800

    epoch = utime.time() + offset

    # Friday, April 15, 2022
    if epoch > 1650000000:
        measurements["dt"] = {"value": epoch}  # time offset 1970 -> 2000
    else:
        measurements["diff_dt"] = {"value": utime.ticks_ms()}


def store_measurement(measurements, force_store=False):
    global mutex
    # +1 is added to count the current measurement that has not been stored to the file
    number_of_measurements = buffered_measurements_count() + 1
    logging.info("Message #" + str(number_of_measurements))

    if (
        message_buffer_size
        and number_of_measurements < message_buffer_size
        or (force_store and number_of_measurements < MAX_NUMBER_OF_FORCED_MESSAGES)
    ):
        data = json.dumps(measurements) + "\n"
        with mutex:
            utils.appendToFlagFile(storage_file_name, data)
            logging.debug("Measurement stored: " + str(measurements))
            return True
    return False


def parse_stored_measurements_and_upload(network):
    global mutex
    # load stored measurements
    failed_messages = []
    if not utils.existsFlagFile(storage_file_name) and not utils.existsFlagFile(storage_file_name + ".up"):
        return

    logging.info("stored measurements found, about to upload")

    with mutex:
        interupted_upload_str = utils.readFromFlagFile(storage_file_name + ".up")
        stored_measurements_str = utils.readFromFlagFile(storage_file_name)
        utils.copyFlagFile(storage_file_name, storage_file_name + ".up")
        utils.deleteFlagFile(storage_file_name)
        stored_measurements_str += "\n" + interupted_upload_str

    uploaded_measurement_count = 0

    for line in stored_measurements_str.split("\n"):
        utime.sleep_ms(50)
        try:
            if not line:
                continue

            data = json.loads(line)
            if "diff_dt" in data:
                time_diff = utime.ticks_ms() - data["diff_dt"]["value"]
                if time_diff > 0:
                    data["time_diff"] = {"value": time_diff}
                else:
                    data["time_diff"] = {"value": 0}
                del data["diff_dt"]

            message = network.create_message(cfg.get("device_id"), data)
            message_send_status = network.send_message(cfg, message)

            logging.debug("Message send status: " + str(message_send_status))

            # this only works for BG600 modem since it supports correct message transmission status
            if message_send_status is not None and not message_send_status:
                logging.info("Failed message appended for future upload: " + str(line))
                failed_messages.append(line + "\n")
            else:
                uploaded_measurement_count += 1
        except Exception as e:
            logging.exception(e, "error reading line: [{}]".format(line))

    with mutex:
        utils.deleteFlagFile(storage_file_name + ".up")

        # if failed messages were logged, recreate the file to upload during next connection
        for failed_message in failed_messages:
            utils.appendToFlagFile(storage_file_name, failed_message)
