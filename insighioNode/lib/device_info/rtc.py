import logging
from time import time

from machine import RTC
from device_info import get_main_version, _MAIN_VERSION_V2, i2c_obj

# ------------------ Constants ------------------
RV8263_ADDR = 0x51

REG_CONTROL1 = 0x00
REG_SECONDS = 0x04  # start of time registers
STOP_BIT = 1 << 5  # Control1 STOP bit
N_TIME_BYTES = 7

_ESP32_SYS_TIME_OFFSET = 946684800

_supports_rtc_chip = None


# ------------------ BCD helpers ------------------
def _bcd_encode(v):
    return ((v // 10) << 4) | (v % 10)


def _bcd_decode(b):
    return ((b >> 4) * 10) + (b & 0x0F)


# ------------------ Low-level helpers ------------------
def _i2c_rtc_read_u8(i2c, reg, n=1):
    if n == 1:
        return i2c.readfrom_mem(RV8263_ADDR, reg, 1)[0]
    else:
        return i2c.readfrom_mem(RV8263_ADDR, reg, n)


def _i2c_rtc_write_u8(i2c, reg, val):
    i2c.writeto_mem(RV8263_ADDR, reg, bytes([val & 0xFF]))


def _i2c_rtc_write_u8_arr(i2c, reg, val_array):
    i2c.writeto_mem(RV8263_ADDR, reg, bytes(val_array))


# ------------------ RTC functions ------------------
def i2c_rtc_set_datetime(i2c, year, month, day, hour, minute, second, weekday=0):
    """
    year: 2000..2099
    weekday: 0..6 (user-defined; commonly Monday=0)
    """
    yy = year - 2000
    if not (0 <= yy <= 99):
        raise ValueError("year must be 2000..2099")

    # 1) Stop RTC while writing
    c1 = _i2c_rtc_read_u8(i2c, REG_CONTROL1)
    _i2c_rtc_write_u8(i2c, REG_CONTROL1, c1 | STOP_BIT)

    # 2) Burst write seconds..year (0x04..0x0A)
    sec_bcd = _bcd_encode(second) & 0x7F  # clear OS flag (bit7)
    data = bytes(
        [
            sec_bcd,
            _bcd_encode(minute),
            _bcd_encode(hour),
            _bcd_encode(day),
            weekday & 0x07,
            _bcd_encode(month),
            _bcd_encode(yy),
        ]
    )
    _i2c_rtc_write_u8_arr(i2c, REG_SECONDS, data)

    # 3) Restart RTC
    _i2c_rtc_write_u8(i2c, REG_CONTROL1, c1 & ~STOP_BIT)


# ----------
def i2c_rtc_get_datetime(i2c):
    raw = _i2c_rtc_read_u8(i2c, REG_SECONDS, N_TIME_BYTES)

    os_flag = 1 if (raw[0] & 0x80) else 0
    second = _bcd_decode(raw[0] & 0x7F)
    minute = _bcd_decode(raw[1] & 0x7F)
    hour = _bcd_decode(raw[2] & 0x3F)
    day = _bcd_decode(raw[3] & 0x3F)
    weekday = raw[4] & 0x07
    month = _bcd_decode(raw[5] & 0x1F)
    year = 2000 + _bcd_decode(raw[6])

    return (year, month, day, hour, minute, second, weekday, os_flag)


def supports_rtc_chip():
    global _supports_rtc_chip

    if _supports_rtc_chip is None:
        hw_version = get_main_version()
        i2c_scan_has_rtc = False
        try:
            i2c = i2c_obj()
            i2c_scan_has_rtc = RV8263_ADDR in i2c.scan()
        except:
            pass
        _supports_rtc_chip = hw_version == _MAIN_VERSION_V2 and i2c_scan_has_rtc
    return _supports_rtc_chip


def system_time():
    epoch = time() + _ESP32_SYS_TIME_OFFSET

    # Friday, April 15, 2022
    return (epoch, epoch > 1650000000)


def i2c_rtc_is_valid():
    if not supports_rtc_chip():
        return False

    i2c = i2c_obj()
    dt = i2c_rtc_get_datetime(i2c)
    year, month, day, hour, minute, second, weekday, os_flag = dt

    print("OS flag:", os_flag)
    if os_flag == 1:
        logging.warning("RTC OS flag is set. RTC time is invalid.")
        return False

    # Check if the RTC time is valid (not in the past)
    if year < 2022 or month < 1 or month > 12 or day < 1 or day > 31:
        return False
    if hour < 0 or hour > 23 or minute < 0 or minute > 59 or second < 0 or second > 59:
        return False

    return True


def update_time_from_rtc():
    _, valid = system_time()
    if valid:
        logging.info("System time is valid. Not updating from RTC.")
        return

    if not supports_rtc_chip():
        logging.info("RTC chip not supported. Not updating from RTC.")
        return

    if not i2c_rtc_is_valid():
        logging.warning("RTC time is invalid. Not updating system time.")
        return

    i2c = i2c_obj()
    dt = i2c_rtc_get_datetime(i2c)
    year, month, day, hour, minute, second, weekday, os_flag = dt

    # Update system time
    rtc = RTC()
    rtc.datetime((year, month, day, weekday, hour, minute, second, 0))
    logging.info("System time updated from RTC: {}".format(rtc.datetime()))


def update_time_ntp():
    import ntptime
    import utils

    rtc = RTC()

    logging.info("time before sync: " + str(rtc.datetime()))
    ntptime.host = "pool.ntp.org"
    cnt = 0
    max_tries = 5
    while cnt < max_tries:
        try:
            epoch_before = time()
            ntptime.settime()
            logging.info("time set")
            update_time_rtc()
            break
        except Exception as e:
            logging.exception(e, "time failed")
        cnt += 1

    epoch_diff = time() - epoch_before
    utils.writeToFlagFile("/epoch_diff", "{}".format(epoch_diff))
    logging.info("time after sync: " + str(rtc.datetime()))


def update_time_from_tuple(time_tuple):
    """
    time_tuple: (year, month, day, weekday, hour, minute, second)
    """
    rtc = RTC()
    rtc.datetime(
        (
            time_tuple[0],
            time_tuple[1],
            time_tuple[2],
            time_tuple[3],  # weekday
            time_tuple[4],  # hour
            time_tuple[5],  # minute
            time_tuple[6],  # second
            0,
        )
    )
    update_time_rtc()
    logging.info("time updated from tuple: " + str(rtc.datetime()))


def update_time_rtc():
    if supports_rtc_chip():
        i2c = i2c_obj()
        dt = RTC().datetime()
        year, month, day, weekday, hour, minute, second, _ = dt
        i2c_rtc_set_datetime(i2c, year, month, day, hour, minute, second, weekday)
