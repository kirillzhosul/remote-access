import os
from .config import get_config, get_folder
from . import fs
from .debug import message as debug_message
from .utils import get_ip

# Name.

def load_name() -> None:
    """ Loads name data. """

    global _name

    try:
        path = get_folder() + get_config()["paths"]["name"]
        fs.build_path(path)

        if os.path.exists(path):
            try:
                with open(path, "r", encoding="UTF-8") as name_file:
                    _name = str(name_file.read())
                return
            except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
                debug_message(f"[Name] Failed to load name! Exception - {exception}")

    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"[Name] Failed to load name! Exception - {exception}")

    _name = get_ip()["ip"]
    save_name()

    debug_message("[Name] Name was set to default during loading (can`t read)")


def save_name() -> None:
    """ Saves name to the file. """

    try:
        path = get_folder() + get_config()["paths"]["name"]
        fs.build_path(path)

        with open(path, "w", encoding="UTF-8") as name_file:
            name_file.write(str(_name))
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"[Name] Failed to read name! Exception - {exception}")


def get_name() -> str:
    if _name is None:
        load_name()
    return _name


def set_name(name: str):
    global _name
    _name = name

_name = None