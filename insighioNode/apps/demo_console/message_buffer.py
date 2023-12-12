import logging

try:
    from apps import demo_temp_config as cfg

    logging.info("loaded config: [temp]")
except Exception as e:
    try:
        from . import demo_config as cfg

        logging.info("loaded config: [normal]")
    except Exception as e:
        cfg = type("", (), {})()
        logging.info("loaded config: [fallback]")
import json
import utils
import utime
import _thread

storage_file_name = "measurements.log"
MAX_NUMBER_OF_FORCED_MESSAGES = const(1000)


def get_config(key):
    return getattr(cfg, key) if hasattr(cfg, key) else None


message_buffer_size = get_config("_BATCH_UPLOAD_MESSAGE_BUFFER")

mutex = _thread.allocate_lock()


def buffered_measurements_count():
    return utils.countFileLines(storage_file_name)


def timestamp_measurements(measurements):
    offset = 946684800

    epoch = utime.time() + offset

    # Friday, April 15, 2022
    if epoch > 1650000000:
        measurements["dt"] = {"value": epoch}  # time offset 1970 -> 2000


def store_measurement(measurements, force_store=False):
    global mutex
    # +1 is added to count the current measurement that has not been stored to the file
    number_of_measurements = utils.countFileLines(storage_file_name) + 1
    logging.info("Message #" + str(number_of_measurements))

    if (
        message_buffer_size
        and number_of_measurements < message_buffer_size
        or (force_store and number_of_measurements < MAX_NUMBER_OF_FORCED_MESSAGES)
    ):
        data = json.dumps(measurements) + "\n"
        with mutex:
            utils.appendToFile(storage_file_name, data)
            logging.debug("Measurement stored: " + str(measurements))
            return True
    return False


def parse_stored_measurements_and_upload(network):
    global mutex
    # load stored measurements
    failed_messages = []
    if not utils.existsFile(storage_file_name) and not utils.existsFile(storage_file_name + ".up"):
        return

    logging.info("stored measurements found, about to upload")

    with mutex:
        interupted_upload_str = utils.readFromFile(storage_file_name + ".up")
        stored_measurements_str = utils.readFromFile(storage_file_name)
        utils.copyFile(storage_file_name, storage_file_name + ".up")
        utils.deleteFile(storage_file_name)
        stored_measurements_str += "\n" + interupted_upload_str
    uploaded_measurement_count = 0
    for line in stored_measurements_str.split("\n"):
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
            logging.exception(e, "error reading line: [{}]".format(line))

    with mutex:
        utils.deleteFile(storage_file_name + ".up")

        # if failed messages were logged, recreate the file to upload during next connection
        for failed_message in failed_messages:
            utils.appendToFile(storage_file_name, failed_message)
