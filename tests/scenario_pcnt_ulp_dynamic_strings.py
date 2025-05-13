def generate_assembly(pcnt_1_enabled, pcnt_1_gpio, pcnt_1_high_freq, pcnt_2_enabled, pcnt_2_gpio, pcnt_2_high_freq):
    base_template = """\
#define DR_REG_RTCIO_BASE            0x60008400
#define RTC_IO_TOUCH_PADX_MUX_SEL_M  (BIT(19))
#define RTC_IO_TOUCH_PADX_FUN_IE_M   (BIT(13))
#define RTC_GPIO_IN_REG              (DR_REG_RTCIO_BASE + 0x24)
#define RTC_GPIO_IN_NEXT_S           10
#define DR_REG_SENS_BASE             0x60008800
#define SENS_SAR_PERI_CLK_GATE_CONF_REG  (DR_REG_SENS_BASE + 0x104)
#define SENS_IOMUX_CLK_EN            (BIT(31))

/* Define variables, which go into .bss section (zero-initialized data) */
"""

    pcnt_template = """\

/* pcnt {pcnt_num} */
#define RTC_IO_TOUCH_PADX_{gpio}_REG        (DR_REG_RTCIO_BASE + 0x84 + ({gpio}*0x4))
next_edge_{gpio}: .long 0
edge_count_{gpio}: .long 0
edge_count_loops_{gpio}: .long 0
debounce_counter_{gpio}: .long 1
debounce_max_count_{gpio}: .long 1
io_number_{gpio}: .long {gpio}

"""

    code_template = """\
    /* Code goes into .text section */
    .text
    .global entry
entry:
{pcnt_checks}
{pcnt_functions}
"""

    pcnt_check_template = """\
    jump check_pcnt_{gpio}
"""

    pcnt_function_template = """\
    .global check_pcnt_{gpio}
check_pcnt_{gpio}:
    /* Load io_number_{gpio} */
    move r3, io_number_{gpio}
    ld r3, r3, 0

    # enable IOMUX clock
    WRITE_RTC_FIELD(SENS_SAR_PERI_CLK_GATE_CONF_REG, SENS_IOMUX_CLK_EN, 1)

    # connect GPIO to the RTC subsystem so the ULP can read it
    WRITE_RTC_REG(RTC_IO_TOUCH_PADX_{gpio}_REG, RTC_IO_TOUCH_PADX_MUX_SEL_M, 1, 1)

    # switch the GPIO into input mode
    WRITE_RTC_REG(RTC_IO_TOUCH_PADX_{gpio}_REG, RTC_IO_TOUCH_PADX_FUN_IE_M, 1, 1)

    /* Read the value of lower 16 RTC IOs into R0 */
    READ_RTC_REG(RTC_GPIO_IN_REG, RTC_GPIO_IN_NEXT_S, 16)

    rsh r0, r0, r3
    and r0, r0, 1
    /* State of input changed? */
    move r3, next_edge_{gpio}
    ld r3, r3, 0
    add r3, r0, r3
    and r3, r3, 1
    jump edge_detected_{gpio}, eq
    {sleep_or_halt}

    .global edge_detected_{gpio}
edge_detected_{gpio}:
    /* Flip next_edge_{gpio} */
    move r3, next_edge_{gpio}
    ld r2, r3, 0
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

"""

    loop_detection_template = """\
    /* Check if edge_count has overfloated and switched from 0xFFFF to 0x0000 */
    ld r0, r3, 0
    jumpr loop_detected_{gpio}, 0, EQ
    {sleep_or_halt}

    .global loop_detected_{gpio}
loop_detected_{gpio}:
    move r3, edge_count_loops_{gpio}
    ld r2, r3, 0
    add r2, r2, 1
    st r2, r3, 0
"""

    pcnt_checks = ""
    pcnt_functions = ""

    if pcnt_1_enabled:
        pcnt_checks += pcnt_check_template.format(gpio=pcnt_1_gpio)

        sleep_or_halt = (
            "jump check_pcnt_{}".format(pcnt_2_gpio) if pcnt_2_enabled else "SLEEP 100\n    jump entry" if pcnt_1_high_freq else "halt"
        )

        pcnt_functions += pcnt_function_template.format(
            gpio=pcnt_1_gpio,
            sleep_or_halt=sleep_or_halt,
            loop_detection=loop_detection_template.format(gpio=pcnt_1_gpio, sleep_or_halt=sleep_or_halt) if pcnt_1_high_freq else "",
        )
        base_template += pcnt_template.format(pcnt_num=1, gpio=pcnt_1_gpio)

    if pcnt_2_enabled:
        pcnt_checks += pcnt_check_template.format(gpio=pcnt_2_gpio)
        pcnt_functions += pcnt_function_template.format(
            gpio=pcnt_2_gpio,
            sleep_or_halt="SLEEP 100\n    jump entry" if pcnt_2_high_freq else "halt",
            loop_detection=(
                loop_detection_template.format(gpio=pcnt_2_gpio, sleep_or_halt="SLEEP 100\n    jump entry" if pcnt_2_high_freq else "halt")
                if pcnt_2_high_freq
                else ""
            ),
        )
        base_template += pcnt_template.format(pcnt_num=2, gpio=pcnt_2_gpio)

    return base_template + code_template.format(pcnt_checks=pcnt_checks, pcnt_functions=pcnt_functions)
