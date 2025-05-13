def get_assembly_pcnt_1_enabled_low_frequency_gpio_4_pcnt_2_disabled():
    return """\
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
debounce_counter_4: .long 1
debounce_max_count_4: .long 1
io_number_4: .long 4

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


def get_assembly_pcnt_1_enabled_high_frequency_gpio_4_pcnt_2_disabled():
    return """\
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
debounce_counter_4: .long 1
debounce_max_count_4: .long 1
io_number_4: .long 4

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
    /* State of input changed? */
    move r3, next_edge_4
    ld r3, r3, 0
    add r3, r0, r3
    and r3, r3, 1
    jump edge_detected_4, eq
    SLEEP 100
    jump entry

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
    /* Check if edge_count has overfloated and switched from 0xFFFF to 0x0000 */
    ld r0, r3, 0
    jumpr loop_detected_4, 0, EQ
    SLEEP 100
    jump entry

    .global loop_detected_4
loop_detected_4:
    move r3, edge_count_loops_4
    ld r2, r3, 0
    add r2, r2, 1
    st r2, r3, 0

    SLEEP 100
    jump entry
"""


def get_assembly_pcnt_1_disabled_pcnt_2_enabled_low_frequency_gpio_5():
    return """\
#define DR_REG_RTCIO_BASE            0x60008400
#define RTC_IO_TOUCH_PADX_MUX_SEL_M  (BIT(19))
#define RTC_IO_TOUCH_PADX_FUN_IE_M   (BIT(13))
#define RTC_GPIO_IN_REG              (DR_REG_RTCIO_BASE + 0x24)
#define RTC_GPIO_IN_NEXT_S           10
#define DR_REG_SENS_BASE             0x60008800
#define SENS_SAR_PERI_CLK_GATE_CONF_REG  (DR_REG_SENS_BASE + 0x104)
#define SENS_IOMUX_CLK_EN            (BIT(31))

/* Define variables, which go into .bss section (zero-initialized data) */

/* pcnt 2 */
#define RTC_IO_TOUCH_PADX_5_REG        (DR_REG_RTCIO_BASE + 0x84 + (5*0x4))
next_edge_5: .long 0
edge_count_5: .long 0
edge_count_loops_5: .long 0
debounce_counter_5: .long 1
debounce_max_count_5: .long 1
io_number_5: .long 5

    /* Code goes into .text section */
    .text
    .global entry
entry:
    jump check_pcnt_5

    .global check_pcnt_5
check_pcnt_5:
    /* Load io_number_5 */
    move r3, io_number_5
    ld r3, r3, 0

    # enable IOMUX clock
    WRITE_RTC_FIELD(SENS_SAR_PERI_CLK_GATE_CONF_REG, SENS_IOMUX_CLK_EN, 1)

    # connect GPIO to the RTC subsystem so the ULP can read it
    WRITE_RTC_REG(RTC_IO_TOUCH_PADX_5_REG, RTC_IO_TOUCH_PADX_MUX_SEL_M, 1, 1)

    # switch the GPIO into input mode
    WRITE_RTC_REG(RTC_IO_TOUCH_PADX_5_REG, RTC_IO_TOUCH_PADX_FUN_IE_M, 1, 1)

    /* Read the value of lower 16 RTC IOs into R0 */
    READ_RTC_REG(RTC_GPIO_IN_REG, RTC_GPIO_IN_NEXT_S, 16)

    rsh r0, r0, r3
    and r0, r0, 1
    /* State of input changed? */
    move r3, next_edge_5
    ld r3, r3, 0
    add r3, r0, r3
    and r3, r3, 1
    jump edge_detected_5, eq
    halt
    
    .global edge_detected_5
edge_detected_5:
    /* Flip next_edge_5 */
    move r3, next_edge_5
    ld r2, r3, 0
    add r2, r2, 1
    and r2, r2, 1
    st r2, r3, 0
    /* Increment edge_count_5 */
    move r3, edge_count_5
    ld r2, r3, 0
    add r2, r2, 1
    st r2, r3, 0
    halt
"""


def get_assembly_pcnt_1_disabled_pcnt_2_enabled_high_frequency_gpio_5():
    return """\
#define DR_REG_RTCIO_BASE            0x60008400
#define RTC_IO_TOUCH_PADX_MUX_SEL_M  (BIT(19))
#define RTC_IO_TOUCH_PADX_FUN_IE_M   (BIT(13))
#define RTC_GPIO_IN_REG              (DR_REG_RTCIO_BASE + 0x24)
#define RTC_GPIO_IN_NEXT_S           10
#define DR_REG_SENS_BASE             0x60008800
#define SENS_SAR_PERI_CLK_GATE_CONF_REG  (DR_REG_SENS_BASE + 0x104)
#define SENS_IOMUX_CLK_EN            (BIT(31))

/* Define variables, which go into .bss section (zero-initialized data) */

/* pcnt 2 */
#define RTC_IO_TOUCH_PADX_5_REG        (DR_REG_RTCIO_BASE + 0x84 + (5*0x4))
next_edge_5: .long 0
edge_count_5: .long 0
edge_count_loops_5: .long 0
debounce_counter_5: .long 1
debounce_max_count_5: .long 1
io_number_5: .long 5

    /* Code goes into .text section */
    .text
    .global entry
entry:
    jump check_pcnt_5

    .global check_pcnt_5
check_pcnt_5:
    /* Load io_number_5 */
    move r3, io_number_5
    ld r3, r3, 0

    # enable IOMUX clock
    WRITE_RTC_FIELD(SENS_SAR_PERI_CLK_GATE_CONF_REG, SENS_IOMUX_CLK_EN, 1)

    # connect GPIO to the RTC subsystem so the ULP can read it
    WRITE_RTC_REG(RTC_IO_TOUCH_PADX_5_REG, RTC_IO_TOUCH_PADX_MUX_SEL_M, 1, 1)

    # switch the GPIO into input mode
    WRITE_RTC_REG(RTC_IO_TOUCH_PADX_5_REG, RTC_IO_TOUCH_PADX_FUN_IE_M, 1, 1)

    /* Read the value of lower 16 RTC IOs into R0 */
    READ_RTC_REG(RTC_GPIO_IN_REG, RTC_GPIO_IN_NEXT_S, 16)

    rsh r0, r0, r3
    and r0, r0, 1
    /* State of input changed? */
    move r3, next_edge_5
    ld r3, r3, 0
    add r3, r0, r3
    and r3, r3, 1
    jump edge_detected_5, eq
    SLEEP 100
    jump entry

    .global edge_detected_5
edge_detected_5:
    /* Flip next_edge_5 */
    move r3, next_edge_5
    ld r2, r3, 0
    add r2, r2, 1
    and r2, r2, 1
    st r2, r3, 0
    /* Increment edge_count_5 */
    move r3, edge_count_5
    ld r2, r3, 0
    add r2, r2, 1
    st r2, r3, 0
    /* Check if edge_count has overfloated and switched from 0xFFFF to 0x0000 */
    ld r0, r3, 0
    jumpr loop_detected_5, 0, EQ
    SLEEP 100
    jump entry

    .global loop_detected_5
loop_detected_5:
    move r3, edge_count_loops_5
    ld r2, r3, 0
    add r2, r2, 1
    st r2, r3, 0

    SLEEP 100
    jump entry
"""


def get_assembly_pcnt_1_enabled_low_frequency_gpio_4_pcnt_2_enabled_low_frequency_gpio_5():
    return """\
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
debounce_counter_4: .long 1
debounce_max_count_4: .long 1
io_number_4: .long 4

/* pcnt 2 */
#define RTC_IO_TOUCH_PADX_5_REG        (DR_REG_RTCIO_BASE + 0x84 + (5*0x4))
next_edge_5: .long 0
edge_count_5: .long 0
edge_count_loops_5: .long 0
debounce_counter_5: .long 1
debounce_max_count_5: .long 1
io_number_5: .long 5

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
    /* State of input changed? */
    move r3, next_edge_4
    ld r3, r3, 0
    add r3, r0, r3
    and r3, r3, 1
    jump edge_detected_4, eq
    jump check_pcnt_5

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
    jump check_pcnt_5

    .global check_pcnt_5
check_pcnt_5:
    /* Load io_number_5 */
    move r3, io_number_5
    ld r3, r3, 0

    # enable IOMUX clock
    WRITE_RTC_FIELD(SENS_SAR_PERI_CLK_GATE_CONF_REG, SENS_IOMUX_CLK_EN, 1)

    # connect GPIO to the RTC subsystem so the ULP can read it
    WRITE_RTC_REG(RTC_IO_TOUCH_PADX_5_REG, RTC_IO_TOUCH_PADX_MUX_SEL_M, 1, 1)

    # switch the GPIO into input mode
    WRITE_RTC_REG(RTC_IO_TOUCH_PADX_5_REG, RTC_IO_TOUCH_PADX_FUN_IE_M, 1, 1)

    /* Read the value of lower 16 RTC IOs into R0 */
    READ_RTC_REG(RTC_GPIO_IN_REG, RTC_GPIO_IN_NEXT_S, 16)

    rsh r0, r0, r3
    and r0, r0, 1
    /* State of input changed? */
    move r3, next_edge_5
    ld r3, r3, 0
    add r3, r0, r3
    and r3, r3, 1
    jump edge_detected_5, eq
    halt

    .global edge_detected_5
edge_detected_5:
    /* Flip next_edge_5 */
    move r3, next_edge_5
    ld r2, r3, 0
    add r2, r2, 1
    and r2, r2, 1
    st r2, r3, 0
    /* Increment edge_count_5 */
    move r3, edge_count_5
    ld r2, r3, 0
    add r2, r2, 1
    st r2, r3, 0
    halt
"""


def get_assembly_pcnt_1_enabled_high_frequency_gpio_4_pcnt_2_enabled_high_frequency_gpio_5():
    return """\
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
debounce_counter_4: .long 1
debounce_max_count_4: .long 1
io_number_4: .long 4

/* pcnt 2 */
#define RTC_IO_TOUCH_PADX_5_REG        (DR_REG_RTCIO_BASE + 0x84 + (5*0x4))
next_edge_5: .long 0
edge_count_5: .long 0
edge_count_loops_5: .long 0
debounce_counter_5: .long 1
debounce_max_count_5: .long 1
io_number_5: .long 5

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
    /* State of input changed? */
    move r3, next_edge_4
    ld r3, r3, 0
    add r3, r0, r3
    and r3, r3, 1
    jump edge_detected_4, eq
    jump check_pcnt_5

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
    /* Check if edge_count has overfloated and switched from 0xFFFF to 0x0000 */
    ld r0, r3, 0
    jumpr loop_detected_4, 0, EQ
    jump check_pcnt_5

    .global loop_detected_4
loop_detected_4:
    move r3, edge_count_loops_4
    ld r2, r3, 0
    add r2, r2, 1
    st r2, r3, 0
    jump check_pcnt_5

    .global check_pcnt_5
check_pcnt_5:
    /* Load io_number_5 */
    move r3, io_number_5
    ld r3, r3, 0

    # enable IOMUX clock
    WRITE_RTC_FIELD(SENS_SAR_PERI_CLK_GATE_CONF_REG, SENS_IOMUX_CLK_EN, 1)

    # connect GPIO to the RTC subsystem so the ULP can read it
    WRITE_RTC_REG(RTC_IO_TOUCH_PADX_5_REG, RTC_IO_TOUCH_PADX_MUX_SEL_M, 1, 1)

    # switch the GPIO into input mode
    WRITE_RTC_REG(RTC_IO_TOUCH_PADX_5_REG, RTC_IO_TOUCH_PADX_FUN_IE_M, 1, 1)

    /* Read the value of lower 16 RTC IOs into R0 */
    READ_RTC_REG(RTC_GPIO_IN_REG, RTC_GPIO_IN_NEXT_S, 16)

    rsh r0, r0, r3
    and r0, r0, 1
    /* State of input changed? */
    move r3, next_edge_5
    ld r3, r3, 0
    add r3, r0, r3
    and r3, r3, 1
    jump edge_detected_5, eq
    SLEEP 100
    jump entry

    .global edge_detected_5
edge_detected_5:
    /* Flip next_edge_5 */
    move r3, next_edge_5
    ld r2, r3, 0
    add r2, r2, 1
    and r2, r2, 1
    st r2, r3, 0
    /* Increment edge_count_5 */
    move r3, edge_count_5
    ld r2, r3, 0
    add r2, r2, 1
    st r2, r3, 0
    /* Check if edge_count has overfloated and switched from 0xFFFF to 0x0000 */
    ld r0, r3, 0
    jumpr loop_detected_5, 0, EQ
    SLEEP 100
    jump entry

    .global loop_detected_5
loop_detected_5:
    move r3, edge_count_loops_5
    ld r2, r3, 0
    add r2, r2, 1
    st r2, r3, 0

    SLEEP 100
    jump entry
"""
