import logging

from . import cfg
import json
import utils
import utime
import _thread

storage_file_name = "measurements.log"
MAX_NUMBER_OF_FORCED_MESSAGES = 1000

message_buffer_size = cfg.get("_BATCH_UPLOAD_MESSAGE_BUFFER")

mutex = _thread.allocate_lock()

_ESP32_SYS_TIME_OFFSET = 946684800


def buffered_measurements_count():
    return utils.countFlagFileLines(storage_file_name)


def timestamp_measurements(measurements, round_seconds=False):
    epoch = utime.time() + _ESP32_SYS_TIME_OFFSET

    # Friday, April 15, 2022
    if epoch > 1650000000:
        measurements["dt"] = {"value": epoch - (epoch % 60 if round_seconds else 0)}  # time offset 1970 -> 2000
    else:
        measurements["diff_dt"] = {"value": utime.time()}


def update_timestamp_based_on_diff_dt(measurements, round_seconds=False):
    epoch = utime.time() + _ESP32_SYS_TIME_OFFSET

    # Friday, April 15, 2022
    if "diff_dt" in measurements and "dt" not in measurements:
        if epoch > 1650000000:
            # get time jump offset (seconds)
            epoch_diff = utils.readFromFlagFile("/epoch_diff")
            try:
                epoch_diff = int(epoch_diff)
            except:
                epoch_diff = 0

            # need to ensure that epoch_diff is always correct!
            measurement_timestamp = _ESP32_SYS_TIME_OFFSET + epoch_diff + measurements["diff_dt"]["value"]
            measurements["dt"] = {
                "value": measurement_timestamp - (measurement_timestamp % 60 if round_seconds else 0)
            }  # time offset 1970 -> 2000

        measurements["time_diff"] = {"value": measurements["diff_dt"]["value"]}

        del measurements["diff_dt"]


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
            return True
    return False


def pop_last_stored_measurement():
    global mutex
    with mutex:
        lines = utils.readFromFlagFile(storage_file_name)
        if not lines:
            return None
        lines = lines.split("\n")
        last_lines = lines[-2:-1]
        lines = lines[:-2]
        utils.writeToFlagFile(storage_file_name, "\n".join(lines) + "\n")
        logging.debug("message_buffer: last line: {}".format(last_lines))
        return last_lines


def update_last_stored_measurement(updated_measurement):
    last_stored_measurement = pop_last_stored_measurement()

    # parse json and get "dt" field
    if last_stored_measurement is not None:
        measurement = json.loads(last_stored_measurement[0])
        if "dt" in measurement:
            print("updating dt field of last stored measurement")
            updated_measurement["dt"] = measurement["dt"]
    store_measurement(updated_measurement, force_store=True)


def parse_stored_measurements_and_upload(network):
    global mutex
    import device_info

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

    completed_without_errors = True

    for line in stored_measurements_str.split("\n"):
        utime.sleep_ms(50)
        try:
            device_info.wdt_reset()

            if not line:
                continue

            data = json.loads(line)
            update_timestamp_based_on_diff_dt(data, True)

            message = network.create_message(cfg.get("device_id"), data)
            message_send_status = network.send_message(cfg, message)

            completed_without_errors &= message_send_status

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

    return completed_without_errors
