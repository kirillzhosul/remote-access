import os
import shutil
import sys
from .debug import message as debug_message
from . import fs
from .config import FEATURE_AUTORUN_ENABLED, DISALLOW_NOT_EXECUTABLE_AUTORUN, get_config, get_folder

# Autorun.

def autorun_register() -> None:
    """ Registers current file to the autorun registry (if executable). """

    if not FEATURE_AUTORUN_ENABLED:
        debug_message("[Autorun] Not registering, as disabled...")
        return

    if fs.executable_get_extension() != "exe" and DISALLOW_NOT_EXECUTABLE_AUTORUN:
        debug_message("[Autorun] Not registering, "
                      "as running not from final executable file (not a .exe), "
                      "if you prefer to register anyway, "
                      "change value in DISALLOW_NOT_EXECUTABLE_AUTORUN flag")
        return

    if not sys.platform.startswith("win32"):
        debug_message("[Autorun] Not registering, as running not from Windows-Family OS.")
        return

    try:
        import winreg  # pylint: disable=import-outside-toplevel
    except ImportError:
        debug_message("[Autorun] Failed to regiter self to the autorun! "
                      "Could not import module winreg that is required for that!")
        return

    try:
        executable_filename = get_config()["autorun"]["executable"]
        executable_path = f"{get_folder()}{executable_filename}.{fs.executable_get_extension()}"

        if not os.path.exists(executable_path):
            fs.build_path(executable_path)
            shutil.copyfile(sys.argv[0], executable_path)

        registry_key = winreg.OpenKey(key=winreg.HKEY_CURRENT_USER,
                                      sub_key="Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                                      reserved=0, access=winreg.KEY_ALL_ACCESS)
        winreg.SetValueEx(registry_key,
                          get_config()["autorun"]["name"], 0,
                          winreg.REG_SZ,
                          executable_path)
        winreg.CloseKey(registry_key)
        debug_message("[Autorun] Successfully regitering self to the registry!")
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"[Autorun] Failed to regiter self to the registry! Exception - {exception}")


def autorun_unregister() -> None:
    """ Unegisters current file to the autorun registry (if executable). """

    if not FEATURE_AUTORUN_ENABLED:
        debug_message("[Autorun] Not unregistering, as disabled...")
        return

    if fs.executable_get_extension() != "exe" and DISALLOW_NOT_EXECUTABLE_AUTORUN:
        debug_message("[Autorun] Not unregistering, "
                      "as running not from final executable file (not a .exe), "
                      "if you prefer to register anyway, "
                      "change value in DISALLOW_NOT_EXECUTABLE_AUTORUN flag")
        return

    if not sys.platform.startswith("win32"):
        debug_message("[Autorun] Not unregistering, as running not from Windows-Family OS.")
        return

    try:
        import winreg  # pylint: disable=import-outside-toplevel
    except ImportError:
        debug_message("[Autorun] Failed to unregister self from the autorun! "
                      "Could not import module winreg")
        return

    try:
        registry_autorun_key = "Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        registry_key: winreg.HKEYType = winreg.OpenKey(key=winreg.HKEY_CURRENT_USER,
                                                       sub_key=registry_autorun_key,
                                                       reserved=0, access=winreg.KEY_ALL_ACCESS)
        winreg.DeleteValue(registry_key, get_config()["autorun"]["name"])
        winreg.CloseKey(registry_key)
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"[Autorun] Failed to unregister self from the autorun! "
                      f"Exception: {exception}")

