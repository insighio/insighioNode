import logging

_name_mapping = None

try:
    from apps import demo_temp_config as cfg
except Exception as e:
    try:
        from . import demo_config as cfg
        if hasattr(cfg, '_MEAS_NAME_MAPPING'):
            _name_mapping = getattr(cfg, '_MEAS_NAME_MAPPING')
            logging.info("loaded name mapping")
    except Exception as e:
        pass

def get_meas_name(or_name):
    if _name_mapping is None:
        return or_name
    try:
        return _name_mapping[or_name]
    except:
        return or_name

def set_value(measurements, key, value, unit=None):
    if value is not None:
        record = {"value": value}
        if unit is not None:
            record["unit"] = unit
        measurements[get_meas_name(key)] = record


def set_value_int(measurements, key, value, unit=None):
    if value is not None:
        try:
            set_value(measurements, get_meas_name(key), round(float(value)), unit)
        except Exception as e:
            logging.exception(e, "set_value_int error: [{}]".format(value))


def set_value_float(measurements, key, value, unit=None, precision=2, multiplier=1):
    if value is not None:
        if isinstance(value, str):
            value = float(value) * multiplier
        try:
            set_value(measurements, get_meas_name(key), float("%0.*f" % (precision, value)), unit)
        except Exception as e:
            logging.exception(e, "set_value_float error: [{}]".format(value))
