import logging


def set_value(measurements, key, value, unit=None):
    if value is not None:
        record = {"value": value}
        if unit is not None:
            record["unit"] = unit
        measurements[key] = record


def set_value_int(measurements, key, value, unit=None):
    if value is not None:
        set_value(measurements, key, round(value), unit)


def set_value_float(measurements, key, value, unit=None, precision=2):
    if value is not None:
        if isinstance(value, str):
            value = float(value)
        try:
            set_value(measurements, key, float("%0.*f" % (precision, value)), unit)
        except Exception as e:
            logging.exception(e, "set_value_float error: [{}]".format(value))
