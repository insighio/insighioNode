import logging

try:
    from apps import demo_temp_config as _cfg

    logging.info("[cfg] loaded config: [temp]")
except Exception as e:
    try:
        from . import demo_config as _cfg

        logging.info("[cfg] loaded config: [normal]")
    except Exception as e:
        cfg = type("", (), {})()
        logging.info("[cfg] loaded config: [fallback]")


def has(key):
    return hasattr(_cfg, key)


def get(key):
    return getattr(_cfg, key) if hasattr(_cfg, key) else None


def set_config(key, value):
    setattr(_cfg, key, value)
    return True


def get_protocol_config():
    return _cfg.get_protocol_config()
