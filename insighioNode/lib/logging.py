import sys
import utime

CRITICAL = 50
ERROR = 40
WARNING = 30
INFO = 20
DEBUG = 10
NOTSET = 0

_level_dict = {
    CRITICAL: "CRIT",
    ERROR: "ERROR",
    WARNING: "WARN",
    INFO: "INFO",
    DEBUG: "DEBUG",
}


class Logger(object):
    def __init__(self, name):
        self.level = NOTSET
        self.name = name or "root"

    def _level_str(self, level):
        global _level_dict
        if level in _level_dict:
            return _level_dict[level]
        return "LVL" + str(level)

    def log(self, level, msg, *args, **kwargs):
        global _level
        if level >= (self.level or _level):
            try:
                print("[{}:{:6d}] {}".format(self._level_str(level), utime.ticks_ms(), msg % args))
                return
            except TypeError as te:
                pass
            try:
                print("[{}:{:6d}] {}".format(self._level_str(level), utime.ticks_ms(), msg))
            except TypeError as te:
                pass

    def debug(self, msg, *args, **kwargs):
        self.log(DEBUG, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.log(INFO, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.log(WARNING, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.log(ERROR, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.log(CRITICAL, msg, *args, **kwargs)

    def exc(self, e, msg, *args):
        self.log(ERROR, msg, *args)
        sys.print_exception(e)

    def exception(self, msg, *args):
        e = None
        if hasattr(sys, "exc_info"):
            e = sys.exc_info()[1]
        self.exc(e, msg, *args)


_level = INFO
_loggers = {}


def getLogger(name=""):
    global _loggers
    if name in _loggers:
        return _loggers[name]
    logger = Logger(name)
    _loggers[name] = logger
    return logger


def info(msg, *args):
    getLogger(None).info(msg, *args)


def debug(msg, *args):
    getLogger(None).debug(msg, *args)


def error(msg, *args):
    getLogger(None).error(msg, *args)


def exception(e, msg, *args):
    getLogger(None).exc(e, msg, *args)


def setLevel(level):
    global _level
    _level = level
