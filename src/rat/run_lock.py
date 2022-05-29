"""
    Module that contains run lock class, that dissalows to run more than one instance.
"""

import os
import sys


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
