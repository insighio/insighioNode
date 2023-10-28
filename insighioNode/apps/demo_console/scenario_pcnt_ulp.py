#import logging
from math import floor
import machine
#
# sourceESPIDF = """\
# #define DR_REG_RTCIO_BASE            0x60008400
# #define DR_REG_SENS_BASE             0x60008800
# #define RTC_GPIO_IN_REG              (DR_REG_RTCIO_BASE + 0x24)
# #define RTC_GPIO_IN_NEXT_S           10
# #define SENS_SAR_PERI_CLK_GATE_CONF_REG  (DR_REG_SENS_BASE + 0x104)
# #define SENS_IOMUX_CLK_EN            (BIT(31))
#
#   /* Define variables, which go into .bss section (zero-initialized data) */
#
# next_edge: .long 0
# edge_count: .long 0
# debounce_counter: .long 1
# debounce_max_count: .long 1
# io_number: .long 4
#
# 	/* Load io_number */
# 	move r3, io_number
# 	ld r3, r3, 0
#
#     /* ESP32S3 powers down RTC periph when entering deep sleep and thus by association SENS_SAR_PERI_CLK_GATE_CONF_REG */
#     /* WRITE_RTC_FIELD(SENS_SAR_PERI_CLK_GATE_CONF_REG, SENS_IOMUX_CLK_EN, 1); */
#
# 	/* Read the value of lower 16 RTC IOs into R0 */
# 	READ_RTC_REG(RTC_GPIO_IN_REG, RTC_GPIO_IN_NEXT_S, 16)
# 	rsh r0, r0, r3
#
# 	and r0, r0, 1
# 	/* State of input changed? */
# 	move r3, next_edge
# 	ld r3, r3, 0
# 	add r3, r0, r3
# 	and r3, r3, 1
# 	jump changed, eq
# 	/* Not changed */
# 	/* Reset debounce_counter to debounce_max_count */
# 	move r3, debounce_max_count
# 	move r2, debounce_counter
# 	ld r3, r3, 0
# 	st r3, r2, 0
# 	/* End program */
# 	halt
#
# 	.global changed
# changed:
# 	/* Input state changed */
# 	/* Has debounce_counter reached zero? */
# 	move r3, debounce_counter
# 	ld r2, r3, 0
# 	add r2, r2, 0 /* dummy ADD to use "jump if ALU result is zero" */
# 	jump edge_detected, eq
# 	/* Not yet. Decrement debounce_counter */
# 	sub r2, r2, 1
# 	st r2, r3, 0
# 	/* End program */
# 	halt
#
# 	.global edge_detected
# edge_detected:
# 	/* Reset debounce_counter to debounce_max_count */
# 	move r3, debounce_max_count
# 	move r2, debounce_counter
# 	ld r3, r3, 0
# 	st r3, r2, 0
# 	/* Flip next_edge */
# 	move r3, next_edge
# 	ld r2, r3, 0
# 	add r2, r2, 1
# 	and r2, r2, 1
# 	st r2, r3, 0
# 	/* Increment edge_count */
# 	move r3, edge_count
# 	ld r2, r3, 0
# 	add r2, r2, 1
# 	st r2, r3, 0
# 	halt
# """

source_pcnt_high_freq = """\

#define DR_REG_RTCIO_BASE            0x60008400
#define DR_REG_SENS_BASE             0x60008800
#define RTC_GPIO_IN_REG              (DR_REG_RTCIO_BASE + 0x24)
#define RTC_GPIO_IN_NEXT_S           10

  /* Define variables, which go into .bss section (zero-initialized data) */

next_edge: .long 0
edge_count: .long 0
debounce_counter: .long 1
debounce_max_count: .long 1
io_number: .long 4

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
	jump entry

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
	jump entry

"""

source_pcnt_low_freq = """\

#define DR_REG_RTCIO_BASE            0x60008400
#define DR_REG_SENS_BASE             0x60008800
#define RTC_GPIO_IN_REG              (DR_REG_RTCIO_BASE + 0x24)
#define RTC_GPIO_IN_NEXT_S           10

  /* Define variables, which go into .bss section (zero-initialized data) */

next_edge: .long 0
edge_count: .long 0
debounce_counter: .long 1
debounce_max_count: .long 1
io_number: .long 4

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
	halt

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
	halt

"""

# sourceCnt = """\
# data:       .long 0
#
# entry:      move r3, data    # load address of data into r3
#             ld r2, r3, 0     # load data contents ([r3+0]) into r2
#             add r2, r2, 1    # increment r2
#             st r2, r3, 0     # store r2 contents into data ([r3+0])
#
#             jump entry             # halt ULP co-prozessor (until it gets waked up again)
# """

load_addr, entry_addr = 0, 5*4
ULP_MEM_BASE = 0x50000000
ULP_DATA_MASK = 0xffff  # ULP data is only in lower 16 bits
_SLEEP_TIME = 10000
_PER_SEC = 2 * _SLEEP_TIME // 1000

def init_ulp():
    from esp32 import ULP
    from external.esp32_ulp import src_to_binary

    binary = src_to_binary(sourceESPIDF, cpu="esp32s3")
    ulp = ULP()

    ulp.load_binary(load_addr, binary)

    init_gpio(4, ulp)
    ulp.set_wakeup_period(0, 0)  # use timer0, wakeup after 50.000 cycles

    ulp.run(entry_addr)
#    logging.info("ULP Started")

def init_gpio(gpio_num, ulp=None):
    if ulp is None:
        from esp32 import ULP
        ulp = ULP()
    ulp.init_gpio(gpio_num)

def value(start=0):
    """
    Function to read variable from ULP memory
    """
    val = (int(hex(machine.mem32[ULP_MEM_BASE + start*4] & ULP_DATA_MASK),16))
#    logging.info("Reading value[{}]: {}".format(start, val))
    return val

def setval(start=0, value=0x0):
    """
    Function to set variable in ULP memory
    """
    machine.mem32[ULP_MEM_BASE + start*4] = value

def read_ulp_values():
    val1 = value(1)
    print("events: {}, pulses: {}, per_sec: {}".format( val1, val1//2, val1//_PER_SEC))
#    logging.info("loops: {}, pulses: {}".format(value(5), floor(value(1)//2)))
    setval(1, 0x0)


def start():
    if machine.reset_cause()==machine.PWRON_RESET or machine.reset_cause()==machine.HARD_RESET or machine.reset_cause()==machine.SOFT_RESET:
        init_ulp()
    else:
        init_gpio(4)
    read_ulp_values()
#    logging.info("about to sleep for 1 minute")
    machine.deepsleep(_SLEEP_TIME)
