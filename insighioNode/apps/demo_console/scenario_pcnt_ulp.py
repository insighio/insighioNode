import machine, time
import esp32
import uio, ure, utime
import sys
from esp32 import ULP
from machine import Pin, mem32, ADC
from external.esp32_ulp import src_to_binary
import logging

from math import floor

#the ulp source code is ULP pulse counter working on pin 0, improved copy of code from here https://esp32.com/viewtopic.php?t=13638

sourceESPIDF = """\

#define DR_REG_RTCCNTL_BASE          0x60008000
#define DR_REG_RTCIO_BASE            0x60008400
#define DR_REG_SENS_BASE             0x60008800

#define RTC_GPIO_IN_REG              (DR_REG_RTCIO_BASE + 0x24)
#define RTC_GPIO_IN_NEXT_S           10

#define SENS_IOMUX_CLK_EN                   (BIT(31))
#define SENS_SAR_PERI_CLK_GATE_CONF_REG     (DR_REG_SENS_BASE + 0x104)
#define RTC_CNTL_LOW_POWER_ST_REG           (DR_REG_RTCCNTL_BASE + 0xD0)
#define RTC_CNTL_RDY_FOR_WAKEUP             (BIT(19))

  /* Define variables, which go into .bss section (zero-initialized data) */

    .global next_edge
next_edge:
    .long 0

    .global edge_count
edge_count:
    .long 0

    .global debounce_counter
debounce_counter:
    .long 3

    .global debounce_max_count
debounce_max_count:
    .long 3

    .global io_number
io_number:
    .long 4

	.global edge_count_to_wake_up
edge_count_to_wake_up:
	.long 2


	/* Code goes into .text section */
	.text
	.global entry
entry:
	/* Load io_number */
	move r3, io_number
	ld r3, r3, 0

    /* ESP32S3 powers down RTC periph when entering deep sleep and thus by association SENS_SAR_PERI_CLK_GATE_CONF_REG */
    WRITE_RTC_FIELD(SENS_SAR_PERI_CLK_GATE_CONF_REG, SENS_IOMUX_CLK_EN, 1);

	/* Lower 16 IOs and higher need to be handled separately,
	 * because r0-r3 registers are 16 bit wide.
	 * Check which IO this is.
	 */
	move r0, r3
	jumpr read_io_high, 16, ge

	/* Read the value of lower 16 RTC IOs into R0 */
	READ_RTC_REG(RTC_GPIO_IN_REG, RTC_GPIO_IN_NEXT_S, 16)
	rsh r0, r0, r3
	jump read_done

	/* Read the value of RTC IOs 16-17, into R0 */
read_io_high:
	READ_RTC_REG(RTC_GPIO_IN_REG, RTC_GPIO_IN_NEXT_S + 16, 2)
	sub r3, r3, 16
	rsh r0, r0, r3

read_done:
	and r0, r0, 1
	/* State of input changed? */
	move r3, next_edge
	ld r3, r3, 0
	add r3, r0, r3
	and r3, r3, 1
	jump changed, eq
	/* Not changed */
	/* Reset debounce_counter to debounce_max_count */
	move r3, debounce_max_count
	move r2, debounce_counter
	ld r3, r3, 0
	st r3, r2, 0
	/* End program */
	halt

	.global changed
changed:
	/* Input state changed */
	/* Has debounce_counter reached zero? */
	move r3, debounce_counter
	ld r2, r3, 0
	add r2, r2, 0 /* dummy ADD to use "jump if ALU result is zero" */
	jump edge_detected, eq
	/* Not yet. Decrement debounce_counter */
	sub r2, r2, 1
	st r2, r3, 0
	/* End program */
	halt

	.global edge_detected
edge_detected:
	/* Reset debounce_counter to debounce_max_count */
	move r3, debounce_max_count
	move r2, debounce_counter
	ld r3, r3, 0
	st r3, r2, 0
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
	/* Compare edge_count to edge_count_to_wake_up */
	move r3, edge_count_to_wake_up
	ld r3, r3, 0
	sub r3, r3, r2
	/* Not yet. End program */
	halt

"""

sourceCnt = """\
data:       .long 0

entry:      move r3, data    # load address of data into r3
            ld r2, r3, 0     # load data contents ([r3+0]) into r2
            add r2, r2, 1    # increment r2
            st r2, r3, 0     # store r2 contents into data ([r3+0])

            halt             # halt ULP co-prozessor (until it gets waked up again)
"""

load_addr, entry_addr = 0, 6*4
ULP_MEM_BASE = 0x50000000
ULP_DATA_MASK = 0xffff  # ULP data is only in lower 16 bits
#load_addr, entry_addr = 0, 4

def init_ulp():
    binary = src_to_binary(sourceESPIDF, cpu="esp32s2")
    ulp = ULP()

    ulp.load_binary(load_addr, binary)

    ulp.init_gpio(4)
    ulp.set_wakeup_period(0, 20000)  # use timer0, wakeup after 50.000 cycles

    ulp.run(entry_addr)
    logging.info("ULP Started")

def value(start=0):
    """
    Function to read variable from ULP memory
    """
    val = (int(hex(mem32[ULP_MEM_BASE + start*4] & ULP_DATA_MASK),16))
    #val = (int(hex(mem32[ULP_MEM_BASE + load_addr] & ULP_DATA_MASK),16))
    logging.info("Reading value[{}]: {}".format(start, val))
    return val

def setval(start=0, value=0x0):
    """
    Function to set variable in ULP memory
    """
    #mem32[ULP_MEM_BASE + load_addr] = value
    mem32[ULP_MEM_BASE + start*4] = value

def read_ulp_values():
    #pulses = value(1)

    value(1)
    # import utime
    # while True:
    #     value(1)
    #     utime.sleep_ms(500)

    #logging.info("pulses: {}".format(floor(pulses//2)))
    #message[setting.channel] = pulses/2*setting.multiplier
    #setval(0,0x0)

    # except Exception as e:
    #     log("Exception:\n")
    #     sys.print_exception(e, logfile)
    #     logfile.flush()
    #     setval(1, pulses + value(1))
    #     machine.deepsleep(15*60*1000)


def start():
    if machine.reset_cause()==machine.PWRON_RESET or machine.reset_cause()==machine.HARD_RESET or machine.reset_cause()==machine.SOFT_RESET:
        init_ulp()
    read_ulp_values()
    logging.info("about to sleep for 1 minute")
    machine.deepsleep(10000)
