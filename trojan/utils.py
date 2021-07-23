# Utils module.


# Importing.

# Other modules.
import os
import typing

# Local modules.
import config


# Functions.

# Other.

def list_intersects(_list_one: list, _list_two: list) -> bool:
    """
    Returns true if one of element exists in other list.
    :param _list_one: list List one.
    :param _list_two: list List two.
    :return: bool Intersects or not.
    """

    # Checking intersection.
    for _item in _list_one:
        # For items in list one.

        if _item in _list_two:
            # If item in list two.

            # Return True.
            return True

    # No intersection.
    return False

# Debug.


def debug_print(_message: str) -> typing.NoReturn:
    """
    Prints debug message if debug messages is enabled.
    :param _message: str Message to show.
    :return: Don`t returns any.
    """

    if not config.DEBUG_PRINT_ENABLED or config.DEBUG_PRINT_ONLY_EXCEPTIONS:
        # If debug print is not enabled or print only exceptions..

        # Returning.
        return

    # Printing.
    print(_message)


def debug_exception(_message: str, _exception):
    """
    Prints exception with given message.
    :param _message: str Message to show.
    :param _exception: Exception Exception to show.
    :return: Don`t returns any.
    """

    if not config.DEBUG_PRINT_ENABLED:
        # If debug print is not enabled.

        # Returning.
        return

    # Message.
    print(f"Oops... Error occurred! Message: {_message}. Exception: {_exception}")


# Path.


def path_build(_path: str) -> typing.NoReturn:
    """
    Builds path to the file.
    :param _path: str Path to build.
    :return: Don`t returns any.
    """

    try:
        # Trying to build path.

        # Getting path elements (split by \\)
        _path = _path.split("\\")

        # Removing last element (filename)
        _path.pop()

        # Converting back to the string
        _path = "\\".join(_path)

        if not os.path.exists(_path):
            # If path not exists.

            # Making directories.
            os.makedirs(_path)
    except Exception as _exception: # noqa
        # If there is exception occurred.

        # Showing debug error.
        debug_exception(f"Error when building path {_path}", _exception)
