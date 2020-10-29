"""Gunicorn Config File."""

# Standard Library
import shutil

# Third Party
from gunicorn.app.base import BaseApplication

# Project
from stats.util import cpu_count, format_listen_address
from stats.config import params

if params.debug:
    workers = 1
    loglevel = "DEBUG"
else:
    workers = cpu_count(2)
    loglevel = "WARNING"


class CustomWSGI(BaseApplication):
    """Custom gunicorn app."""

    def __init__(self, app, options):
        """Initialize custom WSGI."""
        self.application = app
        self.options = options or {}
        super().__init__()

    def load_config(self):
        """Load gunicorn config."""
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }

        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        """Load gunicorn app."""
        return self.application


def start(**kwargs):
    """Start hyperglass via gunicorn."""
    # Project

    CustomWSGI(
        app="stats.api.main:api",
        options={
            "worker_class": "uvicorn.workers.UvicornWorker",
            "preload": True,
            "keepalive": 10,
            "command": shutil.which("gunicorn"),
            "bind": ":".join(
                (format_listen_address(params.listen_address), str(params.listen_port))
            ),
            "workers": workers,
            "loglevel": loglevel,
            "accesslog": "-",
            "errorlog": "-",
            # "logconfig_dict": {"formatters": {"generic": {"format": "%(message)s"}}},
            **kwargs,
        },
    ).run()


if __name__ == "__main__":
    start()
