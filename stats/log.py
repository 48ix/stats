"""Logging instance setup & configuration."""

# Standard Library
import os
import sys

# Third Party
from loguru import logger as _loguru_logger

_LOG_FMT = (
    "<lvl><b>[{level}]</b> {time:YYYYMMDD} {time:HH:mm:ss} <lw>|</lw> {name}<lw>:</lw>"
    "<b>{line}</b> <lw>|</lw> {function}</lvl> <lvl><b>→</b></lvl> {message}"
)
_LOG_LEVELS = [
    {"name": "TRACE", "no": 5, "color": "<m>"},
    {"name": "DEBUG", "no": 10, "color": "<c>"},
    {"name": "INFO", "no": 20, "color": "<le>"},
    {"name": "SUCCESS", "no": 25, "color": "<g>"},
    {"name": "WARNING", "no": 30, "color": "<y>"},
    {"name": "ERROR", "no": 40, "color": "<y>"},
    {"name": "CRITICAL", "no": 50, "color": "<r>"},
]


def base_logger():
    """Initialize logging instance."""
    _loguru_logger.remove()
    _loguru_logger.add(sys.stdout, format=_LOG_FMT, level="INFO", enqueue=True)
    _loguru_logger.configure(levels=_LOG_LEVELS)
    return _loguru_logger


log = base_logger()


def set_log_level(logger, debug):
    """Set log level based on debug state."""
    if debug:
        os.environ["48ix_log_level"] = "DEBUG"
        logger.remove()
        logger.add(sys.stdout, format=_LOG_FMT, level="DEBUG", enqueue=True)
        logger.configure(levels=_LOG_LEVELS)

    if debug:
        logger.debug("Debugging enabled")
    return True
