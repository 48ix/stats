"""Custom exceptions."""

# Standard Library
import json as _json

# Project
from stats.log import log


class StatsError(Exception):
    """Base exception."""

    def __init__(self, message="", level="warning"):
        """Initialize the base exception class.

        Keyword Arguments:
            message {str} -- Error message (default: {""})
            level {str} -- Error severity (default: {"warning"})
            keywords {list} -- 'Important' keywords (default: {None})
        """
        self._message = message
        self._level = level
        if self._level == "warning":
            log.error(repr(self))
        elif self._level == "danger":
            log.critical(repr(self))
        else:
            log.info(repr(self))

    def __str__(self):
        """Return the instance's error message.

        Returns:
            {str} -- Error Message
        """
        return self._message

    def __repr__(self):
        """Return the instance's severity & error message in a string.

        Returns:
            {str} -- Error message with code
        """
        return f"[{self.level.upper()}] {self._message}"

    def dict(self):
        """Return the instance's attributes as a dictionary.

        Returns:
            {dict} -- Exception attributes in dict
        """
        return {
            "message": self._message,
            "level": self._level,
        }

    def json(self):
        """Return the instance's attributes as a JSON object.

        Returns:
            {str} -- Exception attributes as JSON
        """
        return _json.dumps(self.__dict__())

    @property
    def message(self):
        """Return the instance's `message` attribute.

        Returns:
            {str} -- Error Message
        """
        return self._message

    @property
    def level(self):
        """Return the instance's `level` attribute.

        Returns:
            {str} -- Alert name
        """
        return self._level


class _UnFmtError(StatsError):
    """Base exception class for freeform error messages."""

    _level = "warning"

    def __init__(self, unformatted_msg="", level=None, **kwargs):
        """Format error message with keyword arguments.

        Keyword Arguments:
            message {str} -- Error message (default: {""})
            level {str} -- Error severity (default: {"warning"})
            keywords {list} -- 'Important' keywords (default: {None})
        """
        self._message = unformatted_msg.format(**kwargs)
        self._level = level or self._level
        super().__init__(message=self._message, level=self._level)


class _PredefinedError(StatsError):
    _message = "undefined"
    _level = "warning"

    def __init__(self, level=None, **kwargs):
        self._fmt_msg = self._message.format(**kwargs)
        self._level = level or self._level
        super().__init__(message=self._fmt_msg, level=self._level)


class ConfigError(_UnFmtError):
    """Raised for generic user-config issues."""
