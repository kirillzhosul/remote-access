"""
    Module that contains debug stuff.
"""

def message(message: str) -> None:
    """ Show debug message if debug mode."""

    if not DEBUG:
        return

    print(message)


DEBUG = True