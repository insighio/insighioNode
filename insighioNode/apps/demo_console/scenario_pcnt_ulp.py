import machine, time
import esp32
import uio, ure, utime
import sys
from esp32 import ULP
from machine import Pin, mem32, ADC
from esp32_ulp import src_to_binary
import logging

#the ulp source code is ULP pulse counter working on pin 0, improved copy of code from here https://esp32.com/viewtopic.php?t=13638
voltage1 = ""
source = """\
#define DR_REG_RTCIO_BASE            0x3ff48400
#define RTC_IO_TOUCH_PAD0_REG        (DR_REG_RTCIO_BASE + 0x94)
#define RTC_IO_TOUCH_PAD0_MUX_SEL_M  (BIT(19))
#define RTC_IO_TOUCH_PAD0_FUN_IE_M   (BIT(13))
#define RTC_GPIO_IN_REG              (DR_REG_RTCIO_BASE + 0x24)
#define RTC_GPIO_IN_NEXT_S           14

  /* Define variables, which go into .bss section (zero-initialized data)
  .bss*/

  /* Next input signal edge expected: 0 (negative) or 1 (positive) */
  .global next_edge
next_edge:
  .long 0

  /* Total number of signal edges acquired */
  .global edge_count
edge_count:
  .long 0

  /* RTC IO number used to sample the input signal. Set by main program. */
  .global io_number
io_number:
  .long 10

  /* Code goes into .text section */
  .text
  .global entry
entry:
  # connect GPIO to the RTC subsystem so the ULP can read it
  WRITE_RTC_REG(RTC_IO_TOUCH_PAD0_REG, RTC_IO_TOUCH_PAD0_MUX_SEL_M, 1, 1)

  # switch the GPIO into input mode
  WRITE_RTC_REG(RTC_IO_TOUCH_PAD0_REG, RTC_IO_TOUCH_PAD0_FUN_IE_M, 1, 1)
  /* Load io_number */
  move r3, io_number
  ld r3, r3, 0

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
  jump edge_detected, eq
  /* Not changed */
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
  halt
"""

load_addr, entry_addr = 0, 3*4
ULP_MEM_BASE = 0x50000000
ULP_DATA_MASK = 0xffff  # ULP data is only in lower 16 bits

def value(start=0):
    """
    Function to read variable from ULP memory
    """
    val = (int(hex(mem32[ULP_MEM_BASE + start*4] & ULP_DATA_MASK),16))
    logging.info("Reading value: " + str(val))
    return val

def init_ulp():
    binary = src_to_binary(source)
    ulp = ULP()
    ulp.set_wakeup_period(0, 50000)  # use timer0, wakeup after 50.000 cycles
    ulp.load_binary(load_addr, binary)
    ulp.run(entry_addr)
    logging.info("ULP Started")

def setval(start=1, value=0x0):
    """
    Function to set variable in ULP memory
    """
    mem32[ULP_MEM_BASE + start*4] = value

def read_ulp_values():
    pulses = value(1)
    logging.info("pulses: {}".format(pulses))
    #message[setting.channel] = pulses/2*setting.multiplier
    setval(1,0x0)

    # except Exception as e:
    #     log("Exception:\n")
    #     sys.print_exception(e, logfile)
    #     logfile.flush()
    #     setval(1, pulses + value(1))
    #     machine.deepsleep(15*60*1000)


def start():
    if machine.reset_cause()==machine.PWRON_RESET or machine.reset_cause()==machine.HARD_RESET or machine.reset_cause()==machine.SOFT_RESET:
        init_ulp()
        setval(1,0x0)
    read_ulp_values()
    logging.info("about to sleep for 1 minute")
    machine.deepsleep(60000)
