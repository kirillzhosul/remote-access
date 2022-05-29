import requests
import typing
import sys
import subprocess
import os
from .config import (
    DEFAULT_INVALID_IP, DEFAULT_INVALID_HWID,
     PLATFORMS_DEVELOPMENT, PLATFORMS_SUPPORTED
)
from .debug import message as debug_message
from .config import get_config


def get_ip() -> typing.Dict:
    """ Returns IP information. """

    try:
        return requests.get("https://ipinfo.io/json").json()
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"[IP] Failed to grap IP from the system! Exception - {exception}")

    return {"ip": DEFAULT_INVALID_IP}



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


def get_environment_variables() -> typing.Dict:
    """ Returns list of all environment variables in system. """
    return {variable: os.environ.get(variable) for variable in os.environ}


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

