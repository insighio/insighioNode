import machine
import utils
import utime
import logging
from external.kpn_senml.senml_unit import SenmlUnits
from .dictionary_utils import set_value_int, set_value_float

_is_first_run = True
_is_after_initialization = False


def generate_assembly(
    pcnt_1_enabled=False, pcnt_1_gpio=4, pcnt_1_high_freq=False, pcnt_2_enabled=False, pcnt_2_gpio=5, pcnt_2_high_freq=False
):
    return """
#define DR_REG_RTCIO_BASE            0x60008400
#define RTC_IO_TOUCH_PADX_MUX_SEL_M  (BIT(19))
#define RTC_IO_TOUCH_PADX_FUN_IE_M   (BIT(13))
#define RTC_GPIO_IN_REG              (DR_REG_RTCIO_BASE + 0x24)
#define RTC_GPIO_IN_NEXT_S           10
#define DR_REG_SENS_BASE             0x60008800
#define SENS_SAR_PERI_CLK_GATE_CONF_REG  (DR_REG_SENS_BASE + 0x104)
#define SENS_IOMUX_CLK_EN            (BIT(31))

/* Define variables, which go into .bss section (zero-initialized data) */

/* pcnt 1 */
#define RTC_IO_TOUCH_PADX_4_REG        (DR_REG_RTCIO_BASE + 0x84 + (4*0x4))
next_edge_4: .long 0
edge_count_4: .long 0
edge_count_loops_4: .long 0
debounce_counter_4: .long 0
debounce_max_count_4: .long 3          // Debounce threshold (3 consecutive readings)
io_number_4: .long 4
last_stable_state_4: .long 0           // Last confirmed stable state

    /* Code goes into .text section */
    .text
    .global entry
entry:
    jump check_pcnt_4

    .global check_pcnt_4
check_pcnt_4:
    /* Load io_number_4 */
    move r3, io_number_4
    ld r3, r3, 0

    # enable IOMUX clock
    WRITE_RTC_FIELD(SENS_SAR_PERI_CLK_GATE_CONF_REG, SENS_IOMUX_CLK_EN, 1)

    # connect GPIO to the RTC subsystem so the ULP can read it
    WRITE_RTC_REG(RTC_IO_TOUCH_PADX_4_REG, RTC_IO_TOUCH_PADX_MUX_SEL_M, 1, 1)

    # switch the GPIO into input mode
    WRITE_RTC_REG(RTC_IO_TOUCH_PADX_4_REG, RTC_IO_TOUCH_PADX_FUN_IE_M, 1, 1)

    /* Read the value of lower 16 RTC IOs into R0 */
    READ_RTC_REG(RTC_GPIO_IN_REG, RTC_GPIO_IN_NEXT_S, 16)

    rsh r0, r0, r3
    and r0, r0, 1

    /* Load last stable state for comparison */
    move r3, last_stable_state_4
    ld r1, r3, 0

    /* Compare current reading with last stable state */
    sub r2, r0, r1
    jump state_changed, ov    // If overflow/underflow, states are different
    and r2, r2, 0xFFFF       // Mask result to check if zero
    jump state_same, eq      // If zero, states are same
    jump state_changed       // Non-zero means different

    .global state_changed
state_changed:
    /* Input state changed, increment debounce counter */
    move r3, debounce_counter_4
    ld r2, r3, 0
    add r2, r2, 1
    st r2, r3, 0

    /* Check if debounce threshold reached */
    move r3, debounce_max_count_4
    ld r1, r3, 0
    sub r1, r2, r1
    jump debounce_confirmed, ov   // If counter >= threshold, state is confirmed
    halt                          // Otherwise, keep debouncing

    .global state_same
state_same:
    /* Input state same as last stable state, reset debounce counter */
    move r3, debounce_counter_4
    move r2, 0
    st r2, r3, 0
    halt

    .global debounce_confirmed
debounce_confirmed:
    /* Debounced state change confirmed */
    /* Reset debounce counter */
    move r3, debounce_counter_4
    move r2, 0
    st r2, r3, 0

    /* Update last stable state */
    move r3, last_stable_state_4
    st r0, r3, 0

    /* Use original edge detection logic for debounced state */
    /* State of input changed? */
    move r3, next_edge_4
    ld r3, r3, 0
    add r3, r0, r3
    and r3, r3, 1
    jump edge_detected_4, eq
    halt

    .global edge_detected_4
edge_detected_4:
    /* Flip next_edge_4 */
    move r3, next_edge_4
    ld r2, r3, 0
    add r2, r2, 1
    and r2, r2, 1
    st r2, r3, 0
    /* Increment edge_count_4 */
    move r3, edge_count_4
    ld r2, r3, 0
    add r2, r2, 1
    st r2, r3, 0

    halt


    """


#
#     base_template = """\
# #define DR_REG_RTCIO_BASE            0x60008400
# #define RTC_IO_TOUCH_PADX_MUX_SEL_M  (BIT(19))
# #define RTC_IO_TOUCH_PADX_FUN_IE_M   (BIT(13))
# #define RTC_GPIO_IN_REG              (DR_REG_RTCIO_BASE + 0x24)
# #define RTC_GPIO_IN_NEXT_S           10
# #define DR_REG_SENS_BASE             0x60008800
# #define SENS_SAR_PERI_CLK_GATE_CONF_REG  (DR_REG_SENS_BASE + 0x104)
# #define SENS_IOMUX_CLK_EN            (BIT(31))
#
# /* Define variables, which go into .bss section (zero-initialized data) */
# """
#
#     pcnt_template = """\
#
# /* pcnt {pcnt_num} */
# #define RTC_IO_TOUCH_PADX_{gpio}_REG        (DR_REG_RTCIO_BASE + 0x84 + ({gpio}*0x4))
# next_edge_{gpio}: .long 0
# edge_count_{gpio}: .long 0
# edge_count_loops_{gpio}: .long 0
# debounce_counter_{gpio}: .long 1
# debounce_max_count_{gpio}: .long 4
# io_number_{gpio}: .long {gpio}
#
# """
#
#     code_template = """\
#     /* Code goes into .text section */
#     .text
#     .global entry
# entry:
# {pcnt_checks}
# {pcnt_functions}
# """
#
#     pcnt_check_template = """\
#     jump check_pcnt_{gpio}
# """
#
#     pcnt_function_template = """\
#     .global check_pcnt_{gpio}
# check_pcnt_{gpio}:
#     /* Load io_number_{gpio} */
#     move r3, io_number_{gpio}
#     ld r3, r3, 0
#
#     # enable IOMUX clock
#     WRITE_RTC_FIELD(SENS_SAR_PERI_CLK_GATE_CONF_REG, SENS_IOMUX_CLK_EN, 1)
#
#     # connect GPIO to the RTC subsystem so the ULP can read it
#     WRITE_RTC_REG(RTC_IO_TOUCH_PADX_{gpio}_REG, RTC_IO_TOUCH_PADX_MUX_SEL_M, 1, 1)
#
#     # switch the GPIO into input mode
#     WRITE_RTC_REG(RTC_IO_TOUCH_PADX_{gpio}_REG, RTC_IO_TOUCH_PADX_FUN_IE_M, 1, 1)
#
#     /* Read the value of lower 16 RTC IOs into R0 */
#     READ_RTC_REG(RTC_GPIO_IN_REG, RTC_GPIO_IN_NEXT_S, 16)
#
#     rsh r0, r0, r3
#     and r0, r0, 1
#     /* State of input changed? */
#     move r3, next_edge_{gpio}
#     ld r3, r3, 0
#     add r3, r0, r3
#     and r3, r3, 1
#     jump edge_detected_{gpio}, eq
#     {sleep_or_halt}
#
#     .global edge_detected_{gpio}
# edge_detected_{gpio}:
#     /* Flip next_edge_{gpio} */
#     move r3, next_edge_{gpio}
#     ld r2, r3, 0
#     add r2, r2, 1
#     and r2, r2, 1
#     st r2, r3, 0
#     /* Increment edge_count_{gpio} */
#     move r3, edge_count_{gpio}
#     ld r2, r3, 0
#     add r2, r2, 1
#     st r2, r3, 0
# {loop_detection}
#     {sleep_or_halt}
#
# """
#
#     loop_detection_template = """\
#     /* Check if edge_count has overfloated and switched from 0xFFFF to 0x0000 */
#     ld r0, r3, 0
#     jumpr loop_detected_{gpio}, 0, EQ
#     {sleep_or_halt}
#
#     .global loop_detected_{gpio}
# loop_detected_{gpio}:
#     move r3, edge_count_loops_{gpio}
#     ld r2, r3, 0
#     add r2, r2, 1
#     st r2, r3, 0
# """
#
# pcnt_checks = ""
# pcnt_functions = ""
#
# if pcnt_1_enabled:
#     pcnt_checks += pcnt_check_template.format(gpio=pcnt_1_gpio)
#
#     sleep_or_halt = (
#         "jump check_pcnt_{}".format(pcnt_2_gpio) if pcnt_2_enabled else "SLEEP 100\n    jump entry" if pcnt_1_high_freq else "halt"
#     )
#
#     pcnt_functions += pcnt_function_template.format(
#         gpio=pcnt_1_gpio,
#         sleep_or_halt=sleep_or_halt,
#         loop_detection=loop_detection_template.format(gpio=pcnt_1_gpio, sleep_or_halt=sleep_or_halt) if pcnt_1_high_freq else "",
#     )
#     base_template += pcnt_template.format(pcnt_num=1, gpio=pcnt_1_gpio)
#
# if pcnt_2_enabled:
#     pcnt_checks += pcnt_check_template.format(gpio=pcnt_2_gpio)
#     pcnt_functions += pcnt_function_template.format(
#         gpio=pcnt_2_gpio,
#         sleep_or_halt="SLEEP 100\n    jump entry" if pcnt_2_high_freq else "halt",
#         loop_detection=(
#             loop_detection_template.format(gpio=pcnt_2_gpio, sleep_or_halt="SLEEP 100\n    jump entry" if pcnt_2_high_freq else "halt")
#             if pcnt_2_high_freq
#             else ""
#         ),
#     )
#     base_template += pcnt_template.format(pcnt_num=2, gpio=pcnt_2_gpio)
#
# return base_template + code_template.format(pcnt_checks=pcnt_checks, pcnt_functions=pcnt_functions)


ULP_MEM_BASE = 0x50000000
ULP_DATA_MASK = 0xFFFF  # ULP data is only in lower 16 bits
TIMESTAMP_FLAG_FILE = "/pcnt_last_read_timestamp"


def get_number_of_pulse_counters(pcnt_cfg):
    """
    Function to get the number of pulse counters
    """
    num_pulse_counters = 0
    for pcnt in pcnt_cfg:
        if pcnt.get("enabled"):
            num_pulse_counters += 1
    return num_pulse_counters


def get_pulse_counters_are_high_frequency(pcnt_cfg):
    for pcnt in pcnt_cfg:
        if pcnt.get("highFreq"):
            return True
    return False


def init_ulp(pcnt_cfg):
    from esp32 import ULP
    from external.esp32_ulp import src_to_binary

    load_addr = 0

    number_of_pulse_counters = get_number_of_pulse_counters(pcnt_cfg)
    if number_of_pulse_counters == 0 or number_of_pulse_counters > 2:
        logging.error("No pulse counters enabled")
        return

    entry_addr = 8 * 4  # if one pulse counter is enabled
    if number_of_pulse_counters > 1:
        entry_addr = 12 * 4

    if number_of_pulse_counters == 1 and len(pcnt_cfg) == 1:
        pcnt_cfg.append({"enabled": False})
        print("passed from here")

    script_to_run = generate_assembly(
        pcnt_1_enabled=pcnt_cfg[0].get("enabled"),
        pcnt_1_gpio=pcnt_cfg[0].get("gpio"),
        pcnt_1_high_freq=pcnt_cfg[0].get("highFreq"),
        pcnt_2_enabled=pcnt_cfg[1].get("enabled"),
        pcnt_2_gpio=pcnt_cfg[1].get("gpio"),
        pcnt_2_high_freq=pcnt_cfg[1].get("highFreq"),
    )

    # print("Generated ULP assembly code:")
    # print(script_to_run)

    binary = src_to_binary(script_to_run, cpu="esp32s2")
    ulp = ULP()

    ulp.load_binary(load_addr, binary)

    for pcnt in pcnt_cfg:
        if pcnt.get("enabled"):
            init_gpio(pcnt.get("gpio"), ulp)

    ulp.set_wakeup_period(0, 0 if get_pulse_counters_are_high_frequency(pcnt_cfg) else 1000)

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


def read_ulp_values(measurements, pcnt_cfg):
    logging.info("Reading pulse counters from ULP...")

    # read last pcnt saved timestamp
    last_timestamp_str = utils.readFromFlagFile(TIMESTAMP_FLAG_FILE)
    now_timestamp = utime.time_ns()

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

    number_of_pulse_counters = get_number_of_pulse_counters(pcnt_cfg)

    logging.debug("ULP timing: now_timestamp: {}, last_timestamp: {}".format(now_timestamp, last_timestamp))

    if last_timestamp == 0:
        reset_ulp_register_values(pcnt_cfg, number_of_pulse_counters)
        for pcnt in pcnt_cfg:
            if pcnt.get("enabled"):
                id = pcnt.get("id")
                set_value_float(measurements, "pcnt_count_{}".format(id), 0, SenmlUnits.SENML_UNIT_COUNTER)
                set_value_int(measurements, "pcnt_edge_count_{}".format(id), 0, SenmlUnits.SENML_UNIT_COUNTER)
                set_value_float(measurements, "pcnt_period_{}".format(id), 0, SenmlUnits.SENML_UNIT_SECOND)
                set_value_float(measurements, "pcnt_count_formula_{}".format(id), 0)
                logging.debug("================ {} =======================".format(id))
                logging.debug("========= pcnt_count: ----------------")
                logging.debug("=============================================")
        return

    # execute calculations
    time_diff_from_prev = 0
    try:
        time_diff_from_prev = now_timestamp - last_timestamp
        time_diff_from_prev = time_diff_from_prev / 1e9
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

    cnt = 0
    for pcnt in pcnt_cfg:
        if pcnt.get("enabled"):
            id = pcnt.get("id")
            formula = pcnt.get("formula")
            reg_edge_cnt_16bit = 1 + (cnt * 6)
            reg_loops = 2 + (cnt * 6)
            cnt += 1

            read_ulp_values_for_pcnt(measurements, reg_edge_cnt_16bit, reg_loops, formula, time_diff_from_prev, id)


def reset_ulp_register_values(pcnt_cfg, number_of_pulse_counters):
    cnt = 0
    for pcnt in pcnt_cfg:
        if pcnt.get("enabled"):
            reg_edge_cnt_16bit = 1 + (cnt * 6)
            reg_loops = 2 + (cnt * 6)

            setval(reg_edge_cnt_16bit, 0x0)
            setval(reg_loops, 0x0)
            cnt += 1


def read_ulp_values_for_pcnt(measurements, reg_edge_cnt_16bit, reg_loops, formula, time_diff_from_prev, id):
    # read registers
    if _is_after_initialization:
        edge_cnt_16bit = 0
        loops = 0
    else:
        edge_cnt_16bit = value(reg_edge_cnt_16bit)
        loops = value(reg_loops)

    # reset registers
    setval(reg_edge_cnt_16bit, 0x0)
    setval(reg_loops, 0x0)

    edge_cnt = 65536 * loops + edge_cnt_16bit
    pulse_cnt = edge_cnt / 2

    set_value_float(measurements, "pcnt_count_{}".format(id), pulse_cnt, SenmlUnits.SENML_UNIT_COUNTER)
    set_value_int(measurements, "pcnt_edge_count_{}".format(id), edge_cnt, SenmlUnits.SENML_UNIT_COUNTER)
    set_value_float(measurements, "pcnt_period_s_{}".format(id), time_diff_from_prev, SenmlUnits.SENML_UNIT_SECOND, 3)

    calculated_value = 0

    # check if formula is just a number as multiplier
    if type(formula) == int or type(formula) == float:
        formula = "v*{}".format(formula)
    elif type(formula) == str:  # check if formula is a number stored as string
        try:
            float(formula)
            formula = "v*{}".format(formula)
        except:
            pass

    try:
        raw_value = edge_cnt / 2
        formula = formula.replace("v", str(raw_value))
        to_execute = "v_transformed=({})".format(formula)
        namespace = {}
        exec(to_execute, namespace)
        calculated_value = namespace["v_transformed"]
        set_value_float(measurements, "pcnt_count_formula_{}".format(id), calculated_value, None, 4)
    except Exception as e:
        logging.exception(e, "formula name:{}, raw_value:{}, code:{}".format(id, raw_value, formula))
        pass

    logging.debug("   ")
    logging.debug("================ pcnt {} =======================".format(id))
    logging.debug(
        "========= pcnt_count: {}, edge_cnt: {}, time_diff_from_prev: {}, calculated_value: {}".format(
            pulse_cnt, edge_cnt, time_diff_from_prev, calculated_value
        )
    )
    logging.debug("=============================================")


def execute(measurements, pcnt_cfg):
    global _is_first_run
    global _is_after_initialization
    try:
        if machine.reset_cause() != machine.DEEPSLEEP_RESET and _is_first_run:
            init_ulp(pcnt_cfg)
            _is_after_initialization = True
        read_ulp_values(measurements, pcnt_cfg)
    except Exception as e:
        logging.exception(e, "Error reading pulse counter")
    _is_first_run = False
