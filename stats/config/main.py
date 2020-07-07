"""Import configuration from file & validate."""
# Standard Library
import os

# Third Party
import yaml

# Project
from stats.constants import CONFIG_MAIN
from stats.config.params import Params


def _load():
    with CONFIG_MAIN.open("r") as _cf:
        return yaml.safe_load(_cf) or {}


_valid = Params(**_load())

if _valid.debug is True:
    os.environ["48ix_log_level"] = "DEBUG"
