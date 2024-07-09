from math import floor
import machine
import utils
import utime
import logging
from external.kpn_senml.senml_unit import SenmlUnits, SenmlSecondaryUnits
from .dictionary_utils import set_value, set_value_int, set_value_float

_is_first_run = True
_is_after_initialization = False

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
#define RTC_IO_TOUCH_PADX_REG        (DR_REG_RTCIO_BASE + 0x84 + ({}*0x4))
#define RTC_IO_TOUCH_PADX_MUX_SEL_M  (BIT(19))
#define RTC_IO_TOUCH_PADX_FUN_IE_M   (BIT(13))
#define RTC_GPIO_IN_REG              (DR_REG_RTCIO_BASE + 0x24)
#define RTC_GPIO_IN_NEXT_S           10
#define DR_REG_SENS_BASE             0x60008800
#define SENS_SAR_PERI_CLK_GATE_CONF_REG  (DR_REG_SENS_BASE + 0x104)
#define SENS_IOMUX_CLK_EN            (BIT(31))

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

    # enable IOMUX clock
    WRITE_RTC_FIELD(SENS_SAR_PERI_CLK_GATE_CONF_REG, SENS_IOMUX_CLK_EN, 1)

    # connect GPIO to the RTC subsystem so the ULP can read it
    WRITE_RTC_REG(RTC_IO_TOUCH_PADX_REG, RTC_IO_TOUCH_PADX_MUX_SEL_M, 1, 1)

    # switch the GPIO into input mode
    WRITE_RTC_REG(RTC_IO_TOUCH_PADX_REG, RTC_IO_TOUCH_PADX_FUN_IE_M, 1, 1)

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


def read_ulp_values(measurements, multiplier, label=None):
    logging.info("Reading pulse counters from ULP...")

    # read registers
    if _is_after_initialization:
        edge_cnt_16bit = 0
        loops = 0
    else:
        edge_cnt_16bit = value(1)
        loops = value(2)

    # read last pcnt saved timestamp
    last_timestamp_str = utils.readFromFlagFile(TIMESTAMP_FLAG_FILE)
    now_timestamp = utime.time_ns()

    # reset registers
    setval(1, 0x0)
    setval(2, 0x0)

    utils.writeToFlagFile(TIMESTAMP_FLAG_FILE, "{}".format(now_timestamp))

    # validate timestamps
    last_timestamp = 0
    try:
        last_timestamp = int(last_timestamp_str)
    except:
        pass

    if last_timestamp > now_timestamp:
        last_timestamp = 0
        now_timestamp = 0

    logging.debug("ULP timing: now_timestamp: {}, last_timestamp: {}".format(now_timestamp, last_timestamp))

    if last_timestamp == 0:
            set_value_float(measurements, "pcnt_count", 0, SenmlUnits.SENML_UNIT_COUNTER)
            set_value_int(measurements, "pcnt_edge_count", 0, SenmlUnits.SENML_UNIT_COUNTER)
            set_value_float(measurements, "pcnt_period_s", 0, SenmlUnits.SENML_UNIT_SECOND)
            set_value_float(measurements, "pcnt_count_formula", 0)
            logging.debug("================ {} =======================".format(label))
            logging.debug("========= pcnt_count: ----------------")
            logging.debug("=============================================")
            return

    # execute calculations
    time_diff_from_prev = 0
    try:
        time_diff_from_prev = now_timestamp - last_timestamp
        time_diff_from_prev = time_diff_from_prev / 1E9
        if time_diff_from_prev <= 0:
            time_diff_from_prev = 0
        elif time_diff_from_prev > 86400:  # if bigger than one day
            # check if epoch_diff is stored
            epoch_diff = utils.readFromFlagFile("/epoch_diff")
            logging.debug("reading epoch diff: {}".format(epoch_diff))
            if epoch_diff:
                epoch_diff = int(epoch_diff)
                time_diff_from_prev -= epoch_diff
                logging.debug("new time diff: {}".format(time_diff_from_prev))

                if time_diff_from_prev > 86400:  # if STILL bigger than one day
                    time_diff_from_prev = 0
            else:
                time_diff_from_prev = 0
    except:
        pass


    edge_cnt = 65536 * loops + edge_cnt_16bit
    pulse_cnt = edge_cnt / 2

    set_value_float(measurements, "pcnt_count", pulse_cnt, SenmlUnits.SENML_UNIT_COUNTER)
    set_value_int(measurements, "pcnt_edge_count", edge_cnt, SenmlUnits.SENML_UNIT_COUNTER)
    set_value_float(measurements, "pcnt_period_s", time_diff_from_prev, SenmlUnits.SENML_UNIT_SECOND)

    pcnt_multiplier = 1
    try:
        pcnt_multiplier = int(multiplier)
    except:
        pass

    calculated_value = (edge_cnt / 2)*pcnt_multiplier
    set_value_float(measurements, "pcnt_count_formula", calculated_value)

    logging.debug("   ")
    logging.debug("================ {} =======================".format(label))
    logging.debug("========= pcnt_count: {}, edge_cnt: {}, time_diff_from_prev: {}, calculated_value: {}".format(pulse_cnt, edge_cnt, time_diff_from_prev, calculated_value) )
    logging.debug("=============================================")


def execute(measurements, port_number, is_high_freq, formula, label=""):
    global _is_first_run
    global _is_after_initialization
    if machine.reset_cause() != machine.DEEPSLEEP_RESET and _is_first_run:
        init_ulp(port_number, is_high_freq)
        _is_after_initialization = True
    read_ulp_values(measurements, formula, label)
    _is_first_run = False
