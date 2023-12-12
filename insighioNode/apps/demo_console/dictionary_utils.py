import logging

_name_mapping = None


def convertObsoleteMappingToExtended(_name_mapping):
    _name_mapping_extended = {}
    for key, value in _name_mapping.items():
        _name_mapping_extended[key] = {"alias": value, "unit": None}
    return _name_mapping_extended


try:
    from apps import demo_temp_config as cfg
except Exception as e:
    try:
        from . import demo_config as cfg

        if hasattr(cfg, "_MEAS_NAME_EXT_MAPPING"):
            _name_mapping = getattr(cfg, "_MEAS_NAME_EXT_MAPPING")

        # fallback for backward compatibility
        if _name_mapping is None and hasattr(cfg, "_MEAS_NAME_MAPPING"):
            _name_mapping = getattr(cfg, "_MEAS_NAME_MAPPING")
            _name_mapping = convertObsoleteMappingToExtended(_name_mapping)

        logging.info("loaded name mapping")
    except Exception as e:
        pass


def get_meas_name(or_name):
    if _name_mapping is None or or_name not in _name_mapping or "alias" not in _name_mapping[or_name]:
        return or_name
    try:
        return _name_mapping[or_name]["alias"]
    except:
        return or_name


def get_meas_unit(or_name, or_unit):
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
            set_value(measurements, get_meas_name(key), round(float(value)), unit)
        except Exception as e:
            logging.exception(e, "set_value_int error: [{}]".format(value))


def set_value_float(measurements, key, value, unit=None, precision=2, multiplier=1):
    if value is not None:
        if isinstance(value, str):
            value = float(value) * multiplier
        try:
            set_value(
                measurements,
                get_meas_name(key),
                float("%0.*f" % (precision, value)),
                unit,
            )
        except Exception as e:
            logging.exception(e, "set_value_float error: [{}]".format(value))
