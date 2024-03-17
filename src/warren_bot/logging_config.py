# -*- coding: utf-8 -*-
""" Centralized logging configuration file.

See LICENSE.md for license info.
"""
import logging.config
import os

from pythonjsonlogger import jsonlogger  # noqa: F401 pylint: disable=unused-import


def set_logging_level(level):
    """Return proper logging level for logging library.

    :param level: str of the logging level
    :return: proper logging class
    """
    level = str.upper(level)
    if level == "DEBUG":
        rtn_level = logging.DEBUG
    elif level == "INFO":
        rtn_level = logging.INFO
    elif level in ("WARN", "WARNING"):
        rtn_level = logging.WARNING
    elif level == "ERROR":
        rtn_level = logging.ERROR
    elif level == "CRITICAL":
        rtn_level = logging.CRITICAL
    else:
        rtn_level = logging.INFO
    return rtn_level


if "LOGGING" in os.environ:
    LOGGING_LEVEL = os.environ["LOGGING"]
else:
    LOGGING_LEVEL = "INFO"
LOGGING_LEVEL = set_logging_level(LOGGING_LEVEL)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": "%(asctime)s::%(levelname)s::%(name)s::%(filename)s::%(lineno)s::%(funcName)s::%(message)s",
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
        }
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "stream": "extr://sysstdout",
            "formatter": "json",
        }
    },
    "loggers": {"": {"handlers": ["stdout"], "level": LOGGING_LEVEL}},
}

logging.config.dictConfig(LOGGING)
