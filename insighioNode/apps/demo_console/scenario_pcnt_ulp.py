import machine
import utils
import utime
import logging
from external.kpn_senml.senml_unit import SenmlUnits
from .dictionary_utils import set_value_int, set_value_float

_is_first_run = True
_is_after_initialization = False
# _consecutive_failures = 0
_reset_in_progress = False
# CONSECUTIVE_FAILURES_FILE = "/pcnt_consecutive_failures"
RESET_IN_PROGRESS_FILE = "/pcnt_reset_in_progress"
HEARTBEAT_FLAG_FILE = "/pcnt_last_heartbeat"
HEARTBEAT_CHECKS_FLAG_FILE = "/pcnt_last_heartbeat_checks"
LAST_RESET_REASON_FLAG_FILE = "/last_reset_reason"
ULP_REQUIRED_WDT_RESET_FLAG_FILE = "/ulp_required_wdt_reset"


def generate_assembly(
    pcnt_1_enabled=False, pcnt_1_gpio=4, pcnt_1_high_freq=False, pcnt_2_enabled=False, pcnt_2_gpio=5, pcnt_2_high_freq=False
):

    base_template = """\
#define DR_REG_RTCIO_BASE            0x60008400
#define RTC_IO_TOUCH_PADX_MUX_SEL_M  (BIT(19))
#define RTC_IO_TOUCH_PADX_FUN_IE_M   (BIT(13))
#define RTC_GPIO_IN_REG              (DR_REG_RTCIO_BASE + 0x24)
#define RTC_GPIO_IN_NEXT_S           10
#define DR_REG_DR_REG_SENS_BASE             0x60008800
#define SENS_SAR_PERI_CLK_GATE_CONF_REG  (DR_REG_DR_REG_SENS_BASE + 0x104)
#define SENS_IOMUX_CLK_EN            (BIT(31))

/* Define variables, which go into .bss section (zero-initialized data) */
sequential_stable_count_max: .long 5
heartbeat_counter: .long 0
"""

    pcnt_template = """\

/* pcnt {pcnt_num} */
#define RTC_IO_TOUCH_PADX_{gpio}_REG        (DR_REG_RTCIO_BASE + 0x84 + ({gpio}*0x4))
next_edge_{gpio}: .long 1
edge_count_{gpio}: .long 0
edge_count_loops_{gpio}: .long 0
previous_input_value_{gpio}: .long 0
sequential_stable_values_count_{gpio}: .long 0
io_number_{gpio}: .long {gpio}

"""

    code_template = """
    /* Code goes into .text section */
    .text
    .global entry
entry:
    # enable IOMUX clock
    WRITE_RTC_FIELD(SENS_SAR_PERI_CLK_GATE_CONF_REG, SENS_IOMUX_CLK_EN, 1)
    {pcnt_io_init}
    # Increment heartbeat counter
    move r3, heartbeat_counter
    ld r2, r3, 0
    add r2, r2, 1
    st r2, r3, 0
    {pcnt_functions}
"""

    pcnt_io_init_template = """
    # connect GPIO to the RTC subsystem so the ULP can read it
    WRITE_RTC_REG(RTC_IO_TOUCH_PADX_{gpio}_REG, RTC_IO_TOUCH_PADX_MUX_SEL_M, 1, 1)

    # switch the GPIO into input mode
    WRITE_RTC_REG(RTC_IO_TOUCH_PADX_{gpio}_REG, RTC_IO_TOUCH_PADX_FUN_IE_M, 1, 1)
"""

    pcnt_function_template = """
    .global check_pcnt_{gpio}
check_pcnt_{gpio}:
    /* Load io_number_{gpio} */
    move r3, io_number_{gpio}
    ld r3, r3, 0

    /* Read the value of lower 16 RTC IOs into R0 */
    READ_RTC_REG(RTC_GPIO_IN_REG, RTC_GPIO_IN_NEXT_S, 16)

    /* get only the bit that refers to our GPIO */
    rsh r0, r0, r3
    and r0, r0, 1

    /* check input value with the previous value */

    /* load previous input to r3 */
    move r2, previous_input_value_{gpio}
    ld r3, r2, 0 /* get the value */
    st r0, r2, 0 /* store current value as previous */
    add r3, r0, r3
    and r3, r3, 1
    jump stable_value_detected_{gpio}, eq
    jump unstable_value_detected_{gpio}

    .global unstable_value_detected_{gpio}
unstable_value_detected_{gpio}:
    move r3, sequential_stable_values_count_{gpio}
    move r2, 0
    st r2, r3, 0
    {sleep_or_halt}

    .global stable_value_detected_{gpio}
stable_value_detected_{gpio}:
    move r3, sequential_stable_values_count_{gpio}
    ld r2, r3, 0 /* get the value */
    add r2, r2, 1
    st r2, r3, 0

    move r3, sequential_stable_count_max
    ld r3, r3, 0

    # ALU Operation: Compare with limit
    sub r2, r2, r3          # r2 = counter - limit

    # JUMP Operation: Branch based on comparison
    jump check_stable_with_previous_stable_{gpio}, ov           # Jump if counter >= limit
    {sleep_or_halt}

    .global check_stable_with_previous_stable_{gpio}
check_stable_with_previous_stable_{gpio}:
    /* State of input changed? */
    move r3, next_edge_{gpio}
    ld r3, r3, 0
    add r3, r0, r3
    and r3, r3, 1
    jump edge_detected_{gpio}, eq
    jump no_detect_{gpio}


    .global edge_detected_{gpio}
edge_detected_{gpio}:
    /* Flip next_edge_{gpio} */
    move r3, next_edge_{gpio}
    /*ld r2, r3, 0*/
    move r2, r0
    add r2, r2, 1
    and r2, r2, 1
    st r2, r3, 0
    /* Increment edge_count_{gpio} */
    move r3, edge_count_{gpio}
    ld r2, r3, 0
    add r2, r2, 1
    st r2, r3, 0
{loop_detection}
    {sleep_or_halt}

    .global no_detect_{gpio}
no_detect_{gpio}:
    {sleep_or_halt}
"""

    loop_detection_template = """\
    /* Check if edge_count has overfloated and switched from 0xFFFF to 0x0000 */
    ld r1, r3, 0
    jumpr loop_detected_{gpio}, 0, EQ
    {sleep_or_halt}

    .global loop_detected_{gpio}
loop_detected_{gpio}:
    move r3, edge_count_loops_{gpio}
    ld r2, r3, 0
    add r2, r2, 1
    st r2, r3, 0
"""

    pcnt_io_init = ""
    pcnt_functions = ""

    if pcnt_1_enabled:
        pcnt_io_init += pcnt_io_init_template.format(gpio=pcnt_1_gpio)

        sleep_or_halt = (
            "jump check_pcnt_{}".format(pcnt_2_gpio)
            if pcnt_2_enabled
            else "SLEEP 100\n    jump entry" if pcnt_1_high_freq or pcnt_2_high_freq else "halt"
        )

        pcnt_functions += pcnt_function_template.format(
            gpio=pcnt_1_gpio,
            sleep_or_halt=sleep_or_halt,
            loop_detection=(
                loop_detection_template.format(gpio=pcnt_1_gpio, sleep_or_halt=sleep_or_halt)
                if pcnt_1_high_freq or pcnt_2_high_freq
                else ""
            ),
        )
        base_template += pcnt_template.format(pcnt_num=1, gpio=pcnt_1_gpio)

    if pcnt_2_enabled:
        pcnt_io_init += pcnt_io_init_template.format(gpio=pcnt_2_gpio)

        sleep_or_halt = "SLEEP 100\n    jump entry" if pcnt_1_high_freq or pcnt_2_high_freq else "halt"

        pcnt_functions += pcnt_function_template.format(
            gpio=pcnt_2_gpio,
            sleep_or_halt=sleep_or_halt,
            loop_detection=(
                loop_detection_template.format(gpio=pcnt_2_gpio, sleep_or_halt=sleep_or_halt)
                if pcnt_1_high_freq or pcnt_2_high_freq
                else ""
            ),
        )
        base_template += pcnt_template.format(pcnt_num=2, gpio=pcnt_2_gpio)

    return base_template + code_template.format(pcnt_io_init=pcnt_io_init, pcnt_functions=pcnt_functions)


ULP_MEM_BASE = 0x50000000
ULP_DATA_MASK = 0xFFFF  # ULP data is only in lower 16 bits
TIMESTAMP_FLAG_FILE = "/pcnt_last_read_timestamp"


def force_watchdog_reset(reason="WDT reset - ULP stuck"):
    """
    Force a WATCHDOG TIMER reset - more aggressive than software reset.
    WDT reset clears more hardware state including RTC peripherals.
    This is closer to a power-on-reset than machine.reset().
    """
    import utime

    logging.error("=" * 70)
    logging.error(" FORCING WATCHDOG TIMER RESET (HARD RESET)")
    logging.error(" Reason: {}".format(reason))
    logging.error(" This is MORE aggressive than software reset")
    logging.error(" Device will reset via WDT in 3 seconds...")
    logging.error("=" * 70)

    try:
        utils.writeToFlagFile(LAST_RESET_REASON_FLAG_FILE, "WDT_RESET: " + reason)
        utils.writeToFlagFile(ULP_REQUIRED_WDT_RESET_FLAG_FILE, "1")
    except:
        pass

    utime.sleep(3)

    try:
        # Enable and trigger watchdog timer for hardware reset
        from machine import WDT

        wdt = WDT(timeout=1000)  # 1 second timeout
        logging.error("WDT enabled, entering infinite loop to trigger reset...")
        # Infinite loop without feeding watchdog will trigger hardware reset
        while True:
            utime.sleep_ms(100)
    except:
        # Fallback to software reset if WDT not available
        logging.error("WDT not available, falling back to software reset")
        machine.reset()


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


def force_stop_ulp_execution():
    """
    Aggressively force-stop ULP execution before reset.
    This attempts to halt the ULP processor in multiple ways.
    """
    import utime

    logging.debug("Force-stopping ULP execution...")

    try:
        DR_REG_RTCCNTL_BASE = 0x60008000
        RTC_CNTL_STATE0_REG = DR_REG_RTCCNTL_BASE + 0x18
        RTC_CNTL_ULP_CP_TIMER_REG = DR_REG_RTCCNTL_BASE + 0xFC
        RTC_CNTL_ULP_CP_CTRL_REG = DR_REG_RTCCNTL_BASE + 0x100
        RTC_CNTL_ULP_CP_SLP_TIMER_EN = 1 << 31

        DR_REG_RTCCNTL_BASE = 0x60008000
        RTC_CNTL_SWD_WKEY_VALUE = 0x8F1D312A
        RTC_CNTL_SWD_WPROTECT_REG = DR_REG_RTCCNTL_BASE + 0xB8
        machine.mem32[RTC_CNTL_SWD_WPROTECT_REG] = RTC_CNTL_SWD_WKEY_VALUE

        # Method 1: Disable ULP wakeup timer
        try:
            current_val = machine.mem32[RTC_CNTL_STATE0_REG]
            machine.mem32[RTC_CNTL_STATE0_REG] = current_val & ~RTC_CNTL_ULP_CP_SLP_TIMER_EN
            machine.mem32[RTC_CNTL_ULP_CP_TIMER_REG] = 0
        except:
            pass

        # Method 2: Directly halt ULP CPU via control register
        try:
            machine.mem32[RTC_CNTL_ULP_CP_CTRL_REG] = 0
        except:
            pass

        # Method 3: Set ULP program counter to init value in ULP_CP_TIMER_REG
        try:
            # RTC_CNTL_ULP_CP_TIMER_REG contains PC_INIT in bits [10:0]
            machine.mem32[RTC_CNTL_ULP_CP_TIMER_REG] &= ~0x7FF  # Clear PC_INIT bits
        except:
            pass

        utime.sleep_ms(50)  # Give time for ULP to stop
        logging.debug("ULP force-stop completed")
        return True

    except Exception as e:
        logging.debug("Error during force-stop: {}".format(e))
        return False


def reset_ulp_nuclear():
    """
    NUCLEAR OPTION: Try EVERY possible mechanism to reset the ULP coprocessor.
    This attempts to completely nuke the ULP and RTC domain state.
    """
    import utime

    logging.error("=" * 70)
    logging.error(" NUCLEAR ULP RESET - TRYING ALL MECHANISMS")
    logging.error("=" * 70)

    import machine

    # CRITICAL: Force-stop ULP execution FIRST before attempting reset
    force_stop_ulp_execution()
    utime.sleep_ms(100)  # Extended wait for ULP to fully halt

    try:
        # ESP32-S3 System and RTC registers (from ESP-IDF reg_base.h)
        DR_REG_SYSTEM_BASE = 0x600C0000
        DR_REG_RTCCNTL_BASE = 0x60008000
        DR_REG_SENS_BASE = 0x60008800

        RTC_CNTL_SWD_WKEY_VALUE = 0x8F1D312A
        RTC_CNTL_SWD_WPROTECT_REG = DR_REG_RTCCNTL_BASE + 0xB8
        machine.mem32[RTC_CNTL_SWD_WPROTECT_REG] = RTC_CNTL_SWD_WKEY_VALUE

        # System reset registers (from system_reg.h)
        SYSTEM_PERIP_RST_EN0_REG = DR_REG_SYSTEM_BASE + 0x20
        SYSTEM_PERIP_RST_EN1_REG = DR_REG_SYSTEM_BASE + 0x24
        SYSTEM_PERIP_CLK_EN0_REG = DR_REG_SYSTEM_BASE + 0x18
        SYSTEM_PERIP_CLK_EN1_REG = DR_REG_SYSTEM_BASE + 0x1C

        # RTC control registers (from rtc_cntl_reg.h)
        RTC_CNTL_STATE0_REG = DR_REG_RTCCNTL_BASE + 0x18
        RTC_CNTL_ULP_CP_TIMER_REG = DR_REG_RTCCNTL_BASE + 0xFC
        RTC_CNTL_SDIO_ACT_CONF_REG = DR_REG_RTCCNTL_BASE + 0x70
        RTC_CNTL_OPTIONS0_REG = DR_REG_RTCCNTL_BASE + 0x00
        RTC_CNTL_RESET_STATE_REG = DR_REG_RTCCNTL_BASE + 0x38
        RTC_CNTL_ULP_CP_CTRL_REG = DR_REG_RTCCNTL_BASE + 0x100

        # SENS registers (from sens_reg.h)
        SENS_SAR_PERI_CLK_GATE_CONF_REG = DR_REG_SENS_BASE + 0x104
        SENS_SAR_PERI_RESET_CONF_REG = DR_REG_SENS_BASE + 0x108

        # Bit definitions
        RTC_CNTL_ULP_CP_SLP_TIMER_EN = 1 << 31
        SENS_IOMUX_CLK_EN = 1 << 31

        # ===== STEP 1: Force stop ULP execution =====
        logging.debug("Nuclear Step 1: Force-stopping ULP...")
        try:
            # Disable ULP timer wakeup
            current_val = machine.mem32[RTC_CNTL_STATE0_REG]
            machine.mem32[RTC_CNTL_STATE0_REG] = current_val & ~RTC_CNTL_ULP_CP_SLP_TIMER_EN

            current_val = machine.mem32[RTC_CNTL_ULP_CP_TIMER_REG]
            machine.mem32[RTC_CNTL_ULP_CP_TIMER_REG] = current_val & ~RTC_CNTL_ULP_CP_SLP_TIMER_EN

            # Try to stop ULP CPU directly via control register
            current_val = machine.mem32[RTC_CNTL_ULP_CP_CTRL_REG]
            try:
                machine.mem32[RTC_CNTL_ULP_CP_CTRL_REG] = current_val & ~RTC_CNTL_ULP_CP_SLP_TIMER_EN
            except:
                pass

            utime.sleep_ms(20)

            machine.mem32[RTC_CNTL_ULP_CP_CTRL_REG] = current_val | RTC_CNTL_ULP_CP_SLP_TIMER_EN
        except Exception as e:
            logging.debug("Step 1 error: {}".format(e))

        # ===== STEP 2: Reset via SYSTEM peripheral reset =====
        logging.debug("Nuclear Step 2: SYSTEM peripheral reset...")
        try:
            # not confirmed!
            # Reset RTC peripherals via system registers
            # Bit positions for ESP32-S3 (these control RTC/ULP reset)
            current_rst = machine.mem32[SYSTEM_PERIP_RST_EN1_REG]
            machine.mem32[SYSTEM_PERIP_RST_EN1_REG] = current_rst | (1 << 22)  # RTC reset
            utime.sleep_ms(10)
            machine.mem32[SYSTEM_PERIP_RST_EN1_REG] = current_rst  # Release reset
            utime.sleep_ms(50)
        except Exception as e:
            logging.debug("Step 2 error: {}".format(e))

        # ===== STEP 3: Power cycle ULP clock =====
        logging.debug("Nuclear Step 3: Power cycling ULP clocks...")
        try:
            DR_REG_RTCCNTL_BASE = 0x60008000
            RTC_CNTL_SDIO_ACT_CONF_REG = DR_REG_RTCCNTL_BASE + 0x70
            current_clk = machine.mem32[RTC_CNTL_SDIO_ACT_CONF_REG]
            # # Bit 26: CK8M_FORCE_PU, Bit 16: CK8M_FORCE_NO_GATING
            machine.mem32[RTC_CNTL_SDIO_ACT_CONF_REG] = current_clk & ~((1 << 16) | (1 << 26))
            utime.sleep_ms(100)  # Let it power down
            # machine.mem32[RTC_CNTL_SDIO_ACT_CONF_REG] = current_clk | ((1 << 16) | (1 << 26))

            # # Disable 8MHz RTC clock (ULP power source)
            # current_clk = machine.mem32[RTC_CNTL_CLK_CONF_REG]
            # # Bit 22: CK8M_FORCE_PU, Bit 23: CK8M_FORCE_NO_GATING
            # machine.mem32[RTC_CNTL_CLK_CONF_REG] = current_clk & ~((1 << 22) | (1 << 23))
            # utime.sleep_ms(100)  # Let it power down

            # # Re-enable
            # machine.mem32[RTC_CNTL_CLK_CONF_REG] = current_clk | ((1 << 22) | (1 << 23))
            # utime.sleep_ms(100)
        except Exception as e:
            logging.debug("Step 3 error: {}".format(e))

        # ===== STEP 4: Reset SENS/SAR peripherals =====
        logging.debug("Nuclear Step 4: Resetting SENS peripherals...")
        try:
            # Release reset for all SAR peripherals
            machine.mem32[SENS_SAR_PERI_RESET_CONF_REG] = 0
            utime.sleep_ms(100)  # Increased delay

            # Re-enable IOMUX clock (SENS_IOMUX_CLK_EN = bit 31)
            machine.mem32[SENS_SAR_PERI_CLK_GATE_CONF_REG] = SENS_IOMUX_CLK_EN
            utime.sleep_ms(100)  # Increased delay
        except Exception as e:
            logging.debug("Step 4 error: {}".format(e))

        # ===== STEP 5: Clear ALL ULP/RTC_SLOW memory =====
        logging.debug("Nuclear Step 5: Clearing RTC_SLOW memory (8KB)...")
        try:
            # RTC_SLOW_MEM is mapped at 0x50000000 for ULP access
            # But from CPU side it may be different - use ULP_MEM_BASE
            ULP_MEM_BASE_ADDR = 0x50000000
            cleared_count = 0
            for i in range(2048):  # 8KB = 2048 words
                try:
                    machine.mem32[ULP_MEM_BASE_ADDR + i * 4] = 0
                    cleared_count += 1
                except:
                    break
            logging.debug("Cleared {} words of RTC memory".format(cleared_count))
        except Exception as e:
            logging.debug("Step 5 error: {}".format(e))

        # ===== STEP 6: Reset RTC state machine =====
        logging.debug("Nuclear Step 6: Resetting RTC state machine...")
        try:
            DR_REG_RTCCNTL_BASE = 0x60008000
            RTC_CNTL_RESET_STATE_REG = DR_REG_RTCCNTL_BASE + 0x38
            # Try to reset RTC state
            machine.mem32[RTC_CNTL_RESET_STATE_REG] = 0xFFFFFFFF
            utime.sleep_ms(10)
            machine.mem32[RTC_CNTL_RESET_STATE_REG] = 0  # 0
            utime.sleep_ms(50)
            machine.mem32[RTC_CNTL_RESET_STATE_REG] = 0xF041  # 0
            utime.sleep_ms(50)
        except Exception as e:
            logging.debug("Step 6 error: {}".format(e))

        # ===== STEP 7: Re-initialize clocks =====
        logging.debug("Nuclear Step 7: Re-initializing clocks...")
        try:
            # Re-enable clock bits in SDIO_ACT_CONF register
            current_clk = machine.mem32[RTC_CNTL_SDIO_ACT_CONF_REG]
            machine.mem32[RTC_CNTL_SDIO_ACT_CONF_REG] = current_clk | ((1 << 16) | (1 << 26))
            utime.sleep_ms(200)  # Extended delay for clock stabilization
        except Exception as e:
            logging.debug("Step 7 error: {}".format(e))

        # ===== STEP 8: Final verification =====
        logging.debug("Nuclear Step 8: Final stabilization delay...")
        utime.sleep_ms(500)  # Long delay to ensure all hardware is stable

        logging.error("=" * 70)
        logging.error(" NUCLEAR RESET COMPLETED")
        logging.error("=" * 70)
        return True

    except Exception as e:
        logging.exception(e, "Error during nuclear ULP reset")
        return False


def init_ulp(pcnt_cfg, force_reset=False):
    """
    Initialize ULP coprocessor with optional reset.

    Args:
        pcnt_cfg: Pulse counter configuration
        force_reset: If True, perform reset before initialization
        reset_level: 0=standard, 1=aggressive, 2=nuclear, 3=watchdog (full device reset)
    """
    from esp32 import ULP
    from external.esp32_ulp import src_to_binary
    import utime

    global _reset_in_progress

    # Prevent re-entry during reset
    if _reset_in_progress:
        logging.warning("Reset already in progress, skipping")
        return

    if force_reset:
        _reset_in_progress = True
        utils.writeToFlagFile(RESET_IN_PROGRESS_FILE, "1")

    # Load binary with error handling
    ulp = ULP()
    ulp.set_wakeup_period(0, 0)

    # If force_reset is True, perform hardware reset first
    if force_reset:
        logging.error("Attempting NUCLEAR ULP reset")

        utils.writeToFlagFile(LAST_RESET_REASON_FLAG_FILE, "nuclear")
        machine.soft_reset()  # Perform a full device reset after nuclear reset

    load_addr = 0

    number_of_pulse_counters = get_number_of_pulse_counters(pcnt_cfg)
    if number_of_pulse_counters == 0 or number_of_pulse_counters > 2:
        logging.error("No pulse counters enabled")
        return

    # Calculate entry address based on .bss variables:
    # - 2 shared variables (sequential_stable_count_max, heartbeat_counter)
    # - 6 variables per PCNT (next_edge, edge_count, edge_count_loops, previous_input_value, sequential_stable_values_count, io_number)
    # CRITICAL: ulp.run() expects address in WORDS, not bytes!
    entry_addr = 8 * 4  # if one pulse counter is enabled (2 + 6 = 8 words)
    if number_of_pulse_counters > 1:
        entry_addr = 14 * 4  # if two pulse counters enabled (2 + 6 + 6 = 14 words)

    logging.info(
        "ULP configuration: {} pulse counters, entry address: {} words (0x{:04x})".format(number_of_pulse_counters, entry_addr, entry_addr)
    )

    if number_of_pulse_counters == 1 and len(pcnt_cfg) == 1:
        pcnt_cfg.append({"enabled": False})

    script_to_run = generate_assembly(
        pcnt_1_enabled=pcnt_cfg[0].get("enabled"),
        pcnt_1_gpio=pcnt_cfg[0].get("gpio"),
        pcnt_1_high_freq=pcnt_cfg[0].get("highFreq"),
        pcnt_2_enabled=pcnt_cfg[1].get("enabled"),
        pcnt_2_gpio=pcnt_cfg[1].get("gpio"),
        pcnt_2_high_freq=pcnt_cfg[1].get("highFreq"),
    )

    logging.info("=" * 60)
    logging.info("Generated ULP Assembly Code:")
    logging.info("=" * 60)
    print(script_to_run)
    logging.info("=" * 60)

    # Compile assembly to binary with error handling
    logging.info("Compiling ULP assembly for ESP32-S3...")
    try:
        binary = src_to_binary(script_to_run, cpu="esp32s2")
        if binary is None or len(binary) == 0:
            logging.error("CRITICAL: ULP assembly compilation returned empty binary!")
            logging.error("ULP will NOT run. Check assembly code for errors.")
            return
        logging.info("ULP binary compiled successfully: {} bytes".format(len(binary)))
    except Exception as e:
        logging.exception(e, "CRITICAL: ULP assembly compilation failed!")
        return

    try:
        ulp.load_binary(load_addr, binary)
        logging.info("ULP binary loaded at address {}".format(load_addr))
    except Exception as e:
        logging.exception(e, "CRITICAL: Failed to load ULP binary!")
        return

    # Initialize GPIOs for ULP access
    for pcnt in pcnt_cfg:
        if pcnt.get("enabled"):
            gpio_num = pcnt.get("gpio")
            logging.info("Initializing GPIO {} for ULP".format(gpio_num))
            init_gpio(gpio_num, ulp)

    # Set ULP wakeup period
    wakeup_period = 1 if get_pulse_counters_are_high_frequency(pcnt_cfg) else 100
    logging.info("Setting ULP wakeup period: {} cycles".format(wakeup_period))
    ulp.set_wakeup_period(0, wakeup_period)

    # Extended delay before starting to ensure hardware is stable
    if force_reset:
        logging.info("Waiting for hardware stabilization after reset...")
        utime.sleep_ms(500)  # Much longer delay after reset
    else:
        utime.sleep_ms(50)  # Increased from 10ms

    # Start ULP execution
    logging.info("Starting ULP execution at entry address {} words (0x{:04x})...".format(entry_addr, entry_addr))
    try:
        ulp.run(entry_addr)
        logging.info("ULP run() completed - coprocessor should now be executing")
    except Exception as e:
        logging.exception(e, "CRITICAL: Failed to start ULP execution!")
        _reset_in_progress = False
        utils.writeToFlagFile(RESET_IN_PROGRESS_FILE, "0")
        return

    # Extended wait for ULP to start executing
    utime.sleep_ms(200)  # Increased from 100ms
    try:
        heartbeat_check = value(1)  # Read heartbeat at offset 1
        logging.info("ULP heartbeat immediately after start: {}".format(heartbeat_check))
        if heartbeat_check == 0:
            logging.error("WARNING: ULP heartbeat is still 0 after startup - ULP may not be running!")
        else:
            logging.info("SUCCESS: ULP is executing! Heartbeat counter started.")
    except Exception as e:
        logging.exception(e, "Could not read ULP heartbeat after startup")

    # Clear reset-in-progress flag
    _reset_in_progress = False
    utils.writeToFlagFile(RESET_IN_PROGRESS_FILE, "0")

    logging.info("Pulse counting initialization complete")


def init_gpio(gpio_num, ulp=None):
    logging.info("Setting up ULP GPIO")
    if ulp is None:
        from esp32 import ULP

        ulp = ULP()
    try:
        ulp.init_gpio(gpio_num)
    except:
        logging.debug("ulp.init_gpio not supported on this firmware")


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


def check_ulp_malfunction():
    """
    Check if ULP has stopped running by comparing heartbeat counter.
    Returns: (is_malfunctioning, message)
    """
    current_heartbeat = value(1)  # heartbeat_counter at offset 1

    # Read last heartbeat
    last_heartbeat_str = utils.readFromFlagFile(HEARTBEAT_FLAG_FILE)

    # Read how many times we've checked
    check_count_str = utils.readFromFlagFile(HEARTBEAT_CHECKS_FLAG_FILE)

    try:
        last_heartbeat = int(last_heartbeat_str) if last_heartbeat_str else 0
    except:
        last_heartbeat = 0

    try:
        check_count = int(check_count_str) if check_count_str else 0
    except:
        check_count = 0

    check_count += 1
    utils.writeToFlagFile(HEARTBEAT_CHECKS_FLAG_FILE, str(check_count))

    # Store current heartbeat for next check
    utils.writeToFlagFile(HEARTBEAT_FLAG_FILE, "{}".format(current_heartbeat))

    # CRITICAL: If heartbeat is 0 after multiple checks, ULP never started or is dead
    if current_heartbeat == 0 and check_count > 2:
        return True, "ULP completely dead - heartbeat stuck at 0 after {} checks".format(check_count)

    # Handle counter wrap-around (16-bit)
    if current_heartbeat < last_heartbeat:
        # Wrapped around, this is normal - reset check count
        utils.writeToFlagFile(HEARTBEAT_CHECKS_FLAG_FILE, "0")
        return False, "Heartbeat wrapped around (OK)"

    if last_heartbeat > 0 and current_heartbeat == last_heartbeat:
        return True, "ULP stopped running - heartbeat not incrementing (stuck at: {})".format(current_heartbeat)

    # Normal operation - reset check count
    if current_heartbeat > last_heartbeat:
        utils.writeToFlagFile(HEARTBEAT_CHECKS_FLAG_FILE, "0")

    return False, "ULP running normally (heartbeat: {} -> {})".format(last_heartbeat, current_heartbeat)


def read_ulp_values(measurements, pcnt_cfg):
    logging.info("Reading pulse counters from ULP...")

    # Read heartbeat counter for malfunction detection
    heartbeat = value(1)  # heartbeat_counter is at offset 0

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
                set_value_float(measurements, "pcnt_period_s_{}".format(id), 0, SenmlUnits.SENML_UNIT_SECOND)
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
            # Calculate correct register offsets matching assembly layout
            base_offset = 2 + (cnt * 6)
            reg_edge_cnt_16bit = base_offset + 1  # edge_count is second variable
            reg_loops = base_offset + 2  # edge_count_loops is third
            cnt += 1

            read_ulp_values_for_pcnt(measurements, reg_edge_cnt_16bit, reg_loops, formula, time_diff_from_prev, id)

    # Store heartbeat for malfunction detection on next read
    set_value_int(measurements, "ulp_heartbeat", heartbeat, SenmlUnits.SENML_UNIT_COUNTER)


def reset_ulp_register_values(pcnt_cfg, number_of_pulse_counters):
    """
    Reset all ULP state variables to prevent desynchronization.

    Memory layout per PCNT (6 words each):
    Offset 0: sequential_stable_count_max (shared)
    Offset 1: heartbeat_counter (shared)

    For PCNT 1 (starting at offset 2):
      Offset 2: next_edge
      Offset 3: edge_count (16-bit)
      Offset 4: edge_count_loops (overflow counter)
      Offset 5: previous_input_value
      Offset 6: sequential_stable_values_count
      Offset 7: io_number

    For PCNT 2: same pattern starting at offset 8 (2 + 6)
    """
    cnt = 0
    for pcnt in pcnt_cfg:
        if pcnt.get("enabled"):
            gpio_num = pcnt.get("gpio")
            # Calculate register offsets (each PCNT uses 6 consecutive words)
            base_offset = 2 + (cnt * 6)  # Start at offset 2 (after shared variables)
            reg_next_edge = base_offset + 0
            reg_edge_cnt_16bit = base_offset + 1
            reg_loops = base_offset + 2
            reg_prev_input = base_offset + 3
            reg_stable_count = base_offset + 4
            # reg_io_number = base_offset + 5 (read-only, no need to reset)

            logging.debug("Resetting PCNT {} registers at base offset {}".format(pcnt.get("id"), base_offset))

            # Reset counters
            setval(reg_edge_cnt_16bit, 0x0)
            setval(reg_loops, 0x0)

            # Reset state variables
            setval(reg_prev_input, 0x0)
            setval(reg_stable_count, 0x0)

            # Read current GPIO state and set next_edge accordingly
            # to avoid waiting for the wrong edge
            try:
                pin = machine.Pin(gpio_num, machine.Pin.IN)
                current_state = pin.value()
                # If pin is HIGH (1), wait for LOW (0), and vice versa
                setval(reg_next_edge, 1 if current_state == 0 else 0)
            except:
                # Fallback: assume we want to detect rising edge first
                setval(reg_next_edge, 0x1)

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
        "========= pcnt_count: {}, edge_cnt: {}, time_diff_from_prev: {}, calculated_value: {}, {} pulse/sec".format(
            pulse_cnt, edge_cnt, time_diff_from_prev, calculated_value, pulse_cnt / time_diff_from_prev if time_diff_from_prev > 0 else 0
        )
    )
    logging.debug("=============================================")


def execute(measurements, pcnt_cfg):
    global _is_first_run
    global _is_after_initialization
    # global _consecutive_failures
    global _reset_in_progress

    # Prevent execution if reset is in progress
    if _reset_in_progress:
        logging.warning("Reset in progress, skipping this cycle")
        return

    # Check if we crashed during a previous reset
    reset_flag = utils.readFromFlagFile(RESET_IN_PROGRESS_FILE)
    if reset_flag == "1":
        logging.error("Detected unfinished reset from previous cycle - clearing flag")
        utils.writeToFlagFile(RESET_IN_PROGRESS_FILE, "0")
        _reset_in_progress = False

    for pcnt in pcnt_cfg:
        if pcnt.get("enabled"):
            pcnt["highFreq"] = False
    try:
        if machine.reset_cause() != machine.DEEPSLEEP_RESET and _is_first_run:
            init_ulp(pcnt_cfg)
            _is_after_initialization = True
            # _consecutive_failures = 0
            # # Clear persisted failure count on fresh boot (not from deep sleep)
            # utils.writeToFlagFile(CONSECUTIVE_FAILURES_FILE, "0")
            # else:
            #     # Load persisted consecutive failures count (survives deep sleep)
            #     try:
            #         failures_str = utils.readFromFlagFile(CONSECUTIVE_FAILURES_FILE)
            #         _consecutive_failures = int(failures_str) if failures_str else 0
            #     except:
            #         _consecutive_failures = 0

            # Check for ULP malfunction before reading values
            is_stuck, message = check_ulp_malfunction()
            logging.info("ULP status: {}".format(message))

            if is_stuck:
                # _consecutive_failures += 1
                # # Persist the failure count immediately
                # utils.writeToFlagFile(CONSECUTIVE_FAILURES_FILE, str(_consecutive_failures))

                # Perform reset based on level
                init_ulp(pcnt_cfg, force_reset=True)
                _is_after_initialization = True
                set_value_int(measurements, "ulp_reinitialized", 1, SenmlUnits.SENML_UNIT_COUNTER)

                # Reset the heartbeat tracking after reinitialization
                utils.writeToFlagFile(HEARTBEAT_FLAG_FILE, "0")
                # Don't read values this cycle, let ULP stabilize
                _is_first_run = False
                return
            # else:
            #     # ULP is running normally, reset failure counter
            #     if _consecutive_failures > 0:
            #         logging.info("ULP recovered! Resetting failure counter (was: {})".format(_consecutive_failures))
            #         _consecutive_failures = 0
            #         # Clear persisted failure count
            #         utils.writeToFlagFile(CONSECUTIVE_FAILURES_FILE, "0")

        read_ulp_values(measurements, pcnt_cfg)
    except Exception as e:
        logging.exception(e, "Error reading pulse counter")
    _is_first_run = False
