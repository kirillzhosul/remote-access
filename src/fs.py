"""
    Module that works with filesystem.
"""


import os
import typing


def try_delete(path) -> bool:
    """ Tries to delete given file"""

    try:
        os.remove(path)
        return True
    except Exception:  # noqa, pylint: disable=broad-except
        return False


def try_listdir(path) -> typing.List:
    """ Tries to list directory. """

    try:
        return os.listdir(path)
    except Exception:  # noqa, pylint: disable=broad-except
        return []


def get_size(path: str) -> float:
    """ Returns size of the filesystem element. """

    if os.path.exists(path):
        if os.path.isfile(path):
            return int(os.path.getsize(path) / 1024 * 1024)

        if os.path.isdir(path):
            childrens_size = sum([get_size(os.path.join(path, directory))
                                  for directory in try_listdir(path)])
            return os.path.getsize(path) / 1024 * 1024 + childrens_size

    return 0


def get_type(path: str) -> str:
    """ Returns type of the path. """

    if os.path.isdir(path):
        return "Directory"

    if os.path.isfile(path):
        return "File"

    if os.path.islink(path):
        return "Link"

    if os.path.ismount(path):
        return "Mount"

    return "Unknown"


def build_path(path: str) -> None:
    """ Builds path. """

    try:
        path_elements = path.split("\\")
        path_elements.pop()
        path = "\\".join(path_elements)

        if not os.path.exists(path):
            os.makedirs(path)
    except Exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        pass


def try_get_drives_list() -> typing.List:
    """ Returns list of all drives in the system. """

    try:
        drives_letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return [f"{drive_letter}:\\\\" for drive_letter in drives_letters
                if os.path.exists(f"{drive_letter}:\\\\")]
    except Exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        pass

    return []
