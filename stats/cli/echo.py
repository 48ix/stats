"""Convenience classes & functions for CLI printing & formatting."""
# Standard Library
import json
from typing import Generator

# Third Party
from rich.syntax import Syntax
from rich.console import Console


class Echo:
    """Convenience class for pretty console printing."""

    def __init__(self):
        """Initialize Echo()."""
        self.console = Console()

    def __call__(  # noqa: C901 your mom is too complex
        self, message, *args, error=False, **kwargs,
    ):  # noqa: C901
        """Format message based on type."""
        try:
            to_print = message

            if isinstance(message, bytes):
                message = message.decode()

            if isinstance(message, str):
                color = "cyan"
                if error:
                    color = "red"

                if args:
                    fmt_args = (f"[bold {color}]{a}[/bold {color}]" for a in args)
                    to_print = message.format(*fmt_args)

                elif kwargs:
                    fmt_args = {
                        k: f"[bold {color}]{v}[/bold {color}]" for k, v in kwargs
                    }
                    to_print = message.format(**fmt_args)

            elif isinstance(message, (list, tuple, Generator, dict)):
                try:
                    to_print = Syntax(
                        json.dumps(message, indent=2), "json", theme="native"
                    )
                except json.JSONDecodeError:
                    pass

            elif isinstance(message, Exception):
                raise message

            return self.console.print(to_print)
        except Exception:
            self.console.print_exception()
