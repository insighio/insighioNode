from math import floor
import machine
import utils
import utime
import logging
from external.kpn_senml.senml_unit import SenmlUnits
from .dictionary_utils import set_value, set_value_int
from . import cfg

_is_initialized = False

def setup_assembly(is_high_freq, port_number):
    _edge_not_detected_script = "halt" if not is_high_freq else "SLEEP 100\njump entry"
    _loop_counting = (
        "halt"
        if not is_high_freq
        else """\
	/* Check if edge_count has overfloated and switched from 0xFFFF to 0x0000 */
	ld r0, r3, 0
	jumpr loop_detected, 0, EQ

	SLEEP 100
	jump entry

	.global loop_detected
loop_detected:
	move r3, edge_count_loops
	ld r2, r3, 0
	add r2, r2, 1
	st r2, r3, 0

	SLEEP 100
	jump entry
"""
    )
    return """\

#define DR_REG_RTCIO_BASE            0x60008400
#define RTC_GPIO_IN_REG              (DR_REG_RTCIO_BASE + 0x24)
#define RTC_GPIO_IN_NEXT_S           10

  /* Define variables, which go into .bss section (zero-initialized data) */

next_edge: .long 0
edge_count: .long 0
edge_count_loops: .long 0
debounce_counter: .long 1
debounce_max_count: .long 1
io_number: .long {}

	/* Code goes into .text section */
	.text
	.global entry
entry:
	/* Load io_number */
	move r3, io_number
	ld r3, r3, 0

	/* Read the value of lower 16 RTC IOs into R0 */
	READ_RTC_REG(RTC_GPIO_IN_REG, RTC_GPIO_IN_NEXT_S, 16)
	rsh r0, r0, r3
	and r0, r0, 1
	/* State of input changed? */
	move r3, next_edge
	ld r3, r3, 0
	add r3, r0, r3
	and r3, r3, 1
	jump edge_detected, eq
	/* End program */
	{}

	.global edge_detected
edge_detected:
	/* Flip next_edge */
	move r3, next_edge
	ld r2, r3, 0
	add r2, r2, 1
	and r2, r2, 1
	st r2, r3, 0
	/* Increment edge_count */
	move r3, edge_count
	ld r2, r3, 0
	add r2, r2, 1
	st r2, r3, 0
	{}
""".format(
        port_number,
        _edge_not_detected_script,
        _loop_counting,
    )


ULP_MEM_BASE = 0x50000000
ULP_DATA_MASK = 0xFFFF  # ULP data is only in lower 16 bits
TIMESTAMP_FLAG_FILE = "/pcnt_last_read_timestamp"


def init_ulp(port_number, is_high_freq):
    from esp32 import ULP
    from external.esp32_ulp import src_to_binary

    logging.info("Starting ULP for pulse counting...")

    load_addr, entry_addr = 0, 6 * 4

    script_to_run = setup_assembly(is_high_freq, port_number)
    binary = src_to_binary(script_to_run, cpu="esp32s2")
    ulp = ULP()

    ulp.load_binary(load_addr, binary)

    init_gpio(port_number, ulp)
    ulp.set_wakeup_period(0, 0 if is_high_freq else 1000)

    ulp.run(entry_addr)
    logging.info("Pulse counting read")


def init_gpio(gpio_num, ulp=None):
    logging.info("Setting up ULP GPIO")
    if ulp is None:
        from esp32 import ULP

        ulp = ULP()
    ulp.init_gpio(gpio_num)


def value(start=0):
    """
    Function to read variable from ULP memory
    """
    val = int(hex(machine.mem32[ULP_MEM_BASE + start * 4] & ULP_DATA_MASK), 16)
    return val


def setval(start=0, value=0x0):
    """
    Function to set variable in ULP memory
    """
    machine.mem32[ULP_MEM_BASE + start * 4] = value


def read_ulp_values(measurements, formula):
    logging.info("Reading pulse counters from ULP...")

    # read registers
    edge_cnt_16bit = value(1)
    loops = value(2)

    # read last pcnt saved timestamp
    last_timestamp = utils.readFromFlagFile(TIMESTAMP_FLAG_FILE)
    now_timestamp = utime.time()

    logging.debug("last_timestamp: {}, now_timestamp: {}".format(last_timestamp, now_timestamp))

    # reset registers
    setval(1, 0x0)
    setval(2, 0x0)

    utils.writeToFlagFile(TIMESTAMP_FLAG_FILE, "{}".format(now_timestamp))

    # execute calculations

    time_diff_from_prev = -1
    try:
        logging.debug("ULP timing: now_timestamp: {}, last_timestamp: {}".format(now_timestamp, last_timestamp))
        time_diff_from_prev = now_timestamp - int(last_timestamp)
        if time_diff_from_prev < 0:
            time_diff_from_prev = -1
        elif time_diff_from_prev > 86400:  # if bigger than one day
            # check if epoch_diff is stored
            epoch_diff = utils.readFromFlagFile("/epoch_diff")
            logging.debug("reading epoch diff: {}".format(epoch_diff))
            if epoch_diff:
                epoch_diff = int(epoch_diff)
                time_diff_from_prev -= epoch_diff
                logging.debug("new time diff: {}".format(time_diff_from_prev))

                if time_diff_from_prev > 86400:  # if STILL bigger than one day
                    time_diff_from_prev = -1
            else:
                time_diff_from_prev = -1
    except:
        pass

    if time_diff_from_prev > 0 or cfg.is_temp():
        edge_cnt = 65536 * loops + edge_cnt_16bit

        set_value_int(measurements, "pcnt_count", edge_cnt / 2, SenmlUnits.SENML_UNIT_COUNTER)
        set_value_int(measurements, "pcnt_edge_count", edge_cnt, SenmlUnits.SENML_UNIT_COUNTER)
        set_value_int(measurements, "pcnt_period_s", time_diff_from_prev, SenmlUnits.SENML_UNIT_SECOND)

    if time_diff_from_prev == -1:
        logging.info("Pulse counting: no period detected, waiting for next measurmeent period")
        return

    if formula and formula != "v":
        try:
            raw_value = edge_cnt / 2
            formula = formula.replace("v", str(raw_value))
            formula = formula.replace("t", str(time_diff_from_prev))
            to_execute = "v_transformed=({})".format(formula)
            namespace = {}
            exec(to_execute, namespace)
            set_value(measurements, "pcnt_count_formula", namespace["v_transformed"])
        except Exception as e:
            logging.exception(e, "transformator name:{}, raw_value:{}, code:{}".format(name, raw_value, transformator))


def execute(measurements, port_number, is_high_freq, formula):
    global _is_initialized
    if machine.reset_cause() != machine.DEEPSLEEP_RESET and not _is_initialized:
        init_ulp(port_number, is_high_freq)
        _is_initialized = True
    else:
        init_gpio(port_number)
    read_ulp_values(measurements, formula)
