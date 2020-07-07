"""Common utility functions."""
# Standard Library
import re


def clean_keyname(keyname):
    """Remove unsupported characters from input string."""
    keyname = str(keyname)
    removed = re.sub(r"[^a-zA-Z0-9\s\_]", "", keyname.strip("\n"))
    replaced = re.sub(r"\s", "_", removed)
    return replaced


def intersperse(lst, item):
    """Insert item between each list item."""
    result = [item] * (len(lst) * 2 - 1)
    result[0::2] = lst
    return result


def make_repr(_class):
    """Create a user-friendly represention of an object."""
    from asyncio import iscoroutine

    def _process_attrs(_dir):
        for attr in _dir:
            if not attr.startswith("_"):
                attr_val = getattr(_class, attr)

                if callable(attr_val):
                    yield f'{attr}=<function name="{attr_val.__name__}">'

                elif iscoroutine(attr_val):
                    yield f'{attr}=<coroutine name="{attr_val.__name__}">'

                elif isinstance(attr_val, str):
                    yield f'{attr}="{attr_val}"'

                else:
                    yield f"{attr}={str(attr_val)}"

    return f'{_class.__name__}({", ".join(_process_attrs(dir(_class)))})'


def split_on_uppercase(s):
    """Split characters by uppercase letters.

    From: https://stackoverflow.com/a/40382663

    """
    string_length = len(s)
    is_lower_around = (
        lambda: s[i - 1].islower() or string_length > (i + 1) and s[i + 1].islower()
    )

    start = 0
    parts = []
    for i in range(1, string_length):
        if s[i].isupper() and is_lower_around():
            parts.append(s[start:i])
            start = i
    parts.append(s[start:])

    return parts


def parse_port_id(port_id):
    """Parse location, participant ID, and port number from port ID."""
    location, participant_id, port_number = port_id.split(".")
    yield location
    yield int(participant_id)
    yield int(port_number)
