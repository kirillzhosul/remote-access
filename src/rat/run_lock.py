"""
    Module that contains run lock class, that dissalows to run more than one instance.
"""

import os
import sys
from .config import get_folder


class RunLock:
    """ Allows to run only one instance of the script. """
    def __init__(self, filename) -> None:
        self.flock = open(filename, "w")
        self.flock.close()
        try:
            os.remove(filename)
            self.flock = open(filename, "w")
        except WindowsError:
            sys.exit()
    def _unlock(self):
        """ Unlock instance. (Currently not used)"""
        self.flock.close()


def lock() -> RunLock:
    """Locks current instance. """
    return RunLock(get_folder() + "lock")
