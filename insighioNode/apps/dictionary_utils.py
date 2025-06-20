import logging
from . import cfg

_name_mapping = cfg.get("meas-name-ext-mapping")

# fallback for backward compatibility
if _name_mapping is None and cfg.has("meas-name-mapping"):
    _name_mapping = cfg.get("meas-name-mapping")
    _name_mapping_extended = {}
    if _name_mapping is not None:
        for key, value in _name_mapping.items():
            _name_mapping_extended[key] = {"alias": value, "unit": None}
    _name_mapping = _name_mapping_extended


def get_meas_name(or_name):
    if cfg.is_temp():
        return or_name

    if _name_mapping is None or or_name not in _name_mapping or "alias" not in _name_mapping[or_name]:
        return or_name
    try:
        return _name_mapping[or_name]["alias"]
    except:
        return or_name


def get_meas_unit(or_name, or_unit):
    if cfg.is_temp():
        return or_unit

    if _name_mapping is None or or_name not in _name_mapping or "unit" not in _name_mapping[or_name]:
        return or_unit
    try:
        return _name_mapping[or_name]["unit"]
    except:
        return or_unit


def set_value(measurements, key, value, unit=None):
    if value is not None:
        record = {"value": value}
        custom_unit = get_meas_unit(key, unit)
        if custom_unit is not None:
            record["unit"] = custom_unit
        measurements[get_meas_name(key)] = record


def set_value_int(measurements, key, value, unit=None):
    if value is not None:
        try:
            set_value(measurements, key, round(float(value)), unit)
        except Exception as e:
            logging.exception(e, "set_value_int error: [{}]".format(value))


def set_value_float(measurements, key, value, unit=None, precision=3, multiplier=1):
    if value is not None:
        if isinstance(value, str):
            value = float(value) * multiplier
        elif isinstance(value, int) or isinstance(value, float):
            value = value * multiplier

        try:
            set_value(
                measurements,
                key,
                float("%0.*f" % (precision, value)),
                unit,
            )
        except Exception as e:
            logging.exception(e, "set_value_float error: [{}]".format(value))


def _has(obj, key):
    if not obj or not key:
        return False
    try:
        return key in obj
    except:
        return False


def _get(obj, key):
    if not obj or not key:
        return None
    try:
        return obj[key]
    except:
        return None
