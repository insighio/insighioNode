from utime import sleep_ms, ticks_ms, sleep_us, ticks_add, ticks_diff
import logging

from . import cfg

from external.kpn_senml.senml_unit import SenmlUnits
from .dictionary_utils import set_value_float


def shield_accel_measurements(measurements):
    read_accelerometer(measurements, True)


def calculate_baseline(asm330Obj):
    from . import running_stats

    statsX = running_stats.RunningStats()
    statsY = running_stats.RunningStats()
    statsZ = running_stats.RunningStats()

    for i in range(0, 1000):
        (asm330_accX, asm330_accY, asm330_accZ) = asm330Obj.get_reading(True)
        if asm330_accX is None or asm330_accY is None or asm330_accZ is None:
            continue

        statsX.push(asm330_accX)
        statsY.push(asm330_accY)
        statsZ.push(asm330_accZ)

        sleep_us(100)

    return (statsX.mean(), statsY.mean(), statsZ.mean())


def storeAccelerometerMeasurement(measurement, statsX, statsY, statsZ, dev_is_operating, current_total, do_store_measurement=True):
    set_value_float(measurement, "asm330_accX", statsX.mean(), SenmlUnits.SENML_UNIT_ACCELERATION)
    set_value_float(measurement, "asm330_accY", statsY.mean(), SenmlUnits.SENML_UNIT_ACCELERATION)
    set_value_float(measurement, "asm330_accZ", statsZ.mean(), SenmlUnits.SENML_UNIT_ACCELERATION)
    set_value_float(measurement, "dev_is_operating", dev_is_operating)
    set_value_float(measurement, "vibration_total", current_total, SenmlUnits.SENML_UNIT_ACCELERATION)

    if do_store_measurement:
        storeMeasurement(measurement, True)


def read_accelerometer(measurements=None, single_measurement=False):
    logging.info("starting [read_accelerometer] thread")

    try:
        # add support for asm330
        from sensors import asm330

        # only at setup
        # sens.get_sensor_whoami()
        asm330.init(cfg.get("_UC_IO_I2C_SCL"), cfg.get("_UC_IO_I2C_SDA"))
    except Exception as e:
        logging.info("No sensors detected")
        return

    statsX = None
    statsY = None
    statsZ = None
    from math import fabs, pow, sqrt

    from . import running_stats

    statsX = running_stats.RunningStats()
    statsY = running_stats.RunningStats()
    statsZ = running_stats.RunningStats()

    if single_measurement:
        (asm330_accX, asm330_accY, asm330_accZ) = (None, None, None)

        while asm330_accX is None or asm330_accY is None or asm330_accZ is None:
            (asm330_accX, asm330_accY, asm330_accZ) = asm330.get_reading(False)
            sleep_ms(1)

        if asm330_accX is None or asm330_accY is None or asm330_accZ is None:
            return

        statsX.push(asm330_accX)
        statsY.push(asm330_accY)
        statsZ.push(asm330_accZ)
        current_total = sqrt(pow(statsX.mean(), 2) + pow(statsY.mean(), 2) + pow(statsZ.mean(), 2))
        storeAccelerometerMeasurement(measurements, statsX, statsY, statsZ, -1, current_total, False)
        return

    REPORT_PERIOD_MS = 10000
    FORCE_REPORT_PERIOD_MS = 300000

    now = ticks_ms()
    next_report = ticks_add(now, REPORT_PERIOD_MS)
    next_force_report = ticks_add(now, FORCE_REPORT_PERIOD_MS)

    previous_reported_total = []
    dev_is_operating = -1
    idle_value = 100000  # intentionally big value to drop exclude it in the iteration of min calculation
    (baseX, baseY, baseZ) = calculate_baseline(asm330)

    while 1:

        (asm330_accX, asm330_accY, asm330_accZ) = asm330.get_reading(True)
        if asm330_accX is None or asm330_accY is None or asm330_accZ is None:
            sleep_ms(1)
            continue

        statsX.push(fabs(asm330_accX - baseX))
        statsY.push(fabs(asm330_accY - baseY))
        statsZ.push(fabs(asm330_accZ - baseZ))

        now = ticks_ms()
        if ticks_diff(now, next_force_report) >= 0:
            logging.debug("======== Starting force report!")
            current_total = sqrt(pow(statsX.mean(), 2) + pow(statsY.mean(), 2) + pow(statsZ.mean(), 2))
            measurement = {}

            storeAccelerometerMeasurement(measurement, statsX, statsY, statsZ, dev_is_operating, current_total)

            next_force_report = ticks_add(now, FORCE_REPORT_PERIOD_MS)

        if ticks_diff(now, next_report) >= 0:
            logging.debug("======== Starting normal report")
            current_total = sqrt(pow(statsX.mean(), 2) + pow(statsY.mean(), 2) + pow(statsZ.mean(), 2))
            measurement = {}

            if len(previous_reported_total) < 2:
                previous_reported_total.append(current_total)

                storeAccelerometerMeasurement(measurement, statsX, statsY, statsZ, dev_is_operating, current_total)

            elif previous_reported_total[0] != 0:
                previous_reported_total.reverse()
                two_values_ago = previous_reported_total.pop()
                total_diff = (current_total - two_values_ago) / min(two_values_ago, current_total)
                previous_reported_total.append(current_total)

                if fabs(total_diff) > 1:  # big vibration, so report it.
                    dev_is_operating_updated = 1 if total_diff > 0 else 0
                    if dev_is_operating == 1 and dev_is_operating_updated == 0:  # if dropping check if going to idle
                        drop_diff_from_idle = (current_total - idle_value) / min(idle_value, current_total)

                        # if current vibraation has diff over 100% from the min idle, consider it non idle
                        if drop_diff_from_idle > 1:
                            dev_is_operating_updated = 1  # do not consider that dev has dropped to idle.

                    dev_is_operating = dev_is_operating_updated

                    storeAccelerometerMeasurement(measurement, statsX, statsY, statsZ, dev_is_operating, current_total)
                else:
                    logging.debug("Ignoring low intensity vibration: diff: {}".format(total_diff))

            idle_value = min(idle_value, max(current_total, 5))  # set minimum vibration to value 5

            statsX.clear()
            statsY.clear()
            statsZ.clear()

            (baseX, baseY, baseZ) = calculate_baseline(asm330)

            next_report = ticks_add(now, REPORT_PERIOD_MS)

        sleep_ms(1)


def executeStartAccelerometerReading():
    import _thread

    _thread.start_new_thread(read_accelerometer, ())
