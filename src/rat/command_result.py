"""
    Module that contains encapsulated command result class.
"""

import typing


class CommandResult:
    """ Command result class that implements result of the command container. """

    __text: typing.Optional[str] = None
    __attachment: typing.Optional[typing.Tuple[str, str, str]] = None

    __attachment_delete_after_uploading = True

    def __init__(self, text=None):
        """
        Constructor.
        :param text: Text to send.
        """

        if text is not None:
            self.from_text(text)

    def from_text(self, text: str) -> None:
        """
        Creates command result from text.
        :param text: Text to send.
        """

        self.__text = text
        self.__attachment = None

    def from_attachment(self, path: str, title: str, type_: str) -> None:
        """
        Creates command result from attachment.
        :param path: Path to upload.
        :param title: Title for attachment.
        :param type_: Type of the document ("doc", "audio_message", "photo")
        """

        self.__text = None
        self.__attachment = (path, title, type_)

    def get_text(self):
        """ Text getter. """
        return self.__text

    def get_attachment(self):
        """ Attachment getter. """
        return self.__attachment

    def disable_delete_after_uploading(self):
        """ Disables deletion after uploading. """
        self.__attachment_delete_after_uploading = False

    def should_delete_after_uploading(self):
        """ Returns should we delete file after uploading. """
        return self.__attachment_delete_after_uploading

