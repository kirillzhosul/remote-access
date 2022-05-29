import typing
import sys
import requests
import json
from .config import (
    get_config
)
from .debug import DEBUG, message as debug_message
from .name import get_name
from .tags import (
    get_tags, parse_tags
)
from .utils import (
    peer_is_allowed,
    list_intersects
)
from . import fs
from .commands import command_alive, execute_command
from .command_result import CommandResult

try:
    # TODO: Move at server setup (but for now there is no NON-VK server types.)
    import vk_api
    import vk_api.utils
    import vk_api.upload
    # There is vk_api.longpoll / vk_api.bot_longpoll imports in server connection,
    # As there is checks for current server type (to not cause import conflicts).

    import requests
except ImportError as exception:
    if DEBUG:
        print(f"[Importing] Cannot import {exception}!")
    sys.exit(1)

# Server.

def server_connect() -> None:
    """ Connects to the server. """

    global _server_api
    global _server_longpoll

    try:
        if "server" not in get_config() or "type" not in get_config()["server"]:
            debug_message("[Server] Failed to get configuration server->type value key! "
                          "Please check configuration file!")
            sys.exit(1)

        server_type = get_config()["server"]["type"]

        if server_type in ("VK_USER", "VK_GROUP"):
            access_token = get_config()["server"]["vk"]["user" if server_type == "VK_USER" else "group"]["access_token"]


            try:
                if server_type == "VK_GROUP":
                    import vk_api.bot_longpoll  # pylint: disable=import-outside-toplevel, redefined-outer-name
                else:
                    import vk_api.longpoll  # pylint: disable=import-outside-toplevel, redefined-outer-name
            except ImportError:
                debug_message("[Server] Failed to import VK longpoll!")
                sys.exit(1)

            _server_api = vk_api.VkApi(token=access_token)

            if server_type == "VK_GROUP":
                group_index = get_config()["server"]["vk"]["group"]["index"]
                _server_longpoll = vk_api.bot_longpoll.VkBotLongPoll(_server_api, group_index)
            else:
                _server_longpoll = vk_api.longpoll.VkLongPoll(_server_api)
        else:
            debug_message(f"[Server] Failed to connect with current server type, "
                          f"as it may be not implemented / exists. Server type - {server_type}")
            sys.exit(1)
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"[Server] Failed to connect with server! Exception - {exception}")
        sys.exit(1)

    debug_message(f"[Server] Connected to the server with type - {server_type}")


def server_listen() -> None:
    """ Listen server for new messages. """

    if _server_longpoll is None:
        debug_message("[Server] Failed to start server listening as server longpoll is not connected!")
        sys.exit(1)

    if "server" not in get_config() or "type" not in get_config()["server"]:
        debug_message("[Server] Failed to get configuration server->type value key! Please check configuration file!")
        sys.exit(1)

    server_type = get_config()["server"]["type"]
    if server_type in ("VK_USER", "VK_GROUP"):
        while True:
            try:
                if server_type == "VK_USER":
                    message_event = vk_api.longpoll.VkEventType.MESSAGE_NEW  # noqa
                elif server_type == "VK_GROUP":
                    message_event = vk_api.bot_longpoll.VkBotEventType.MESSAGE_NEW  # noqa
                else:
                    debug_message(f"[Server] Failed to start server listening with current server type, "
                                  f"as it may be not implemented / exists. Server type - {server_type}")
                    return

                for event in _server_longpoll.listen():  # noqa
                    if event.type == message_event:
                        process_message(event)

            except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
                debug_message(f"[Server] Failed to listen server. Exception - {exception}")
    else:
        debug_message(f"[Server] Failed to listen with current server type, as it may be not implemented / exists. "
                      f"Server type - {server_type}")
        sys.exit(1)


def server_method(method: str, parameters: typing.Dict, is_retry=False) -> typing.Optional[typing.Any]:
    """ Calls server method. """

    if _server_api is None:
        return None

    try:
        if "random_id" not in parameters:
            parameters["random_id"] = vk_api.utils.get_random_id()
        return _server_api.method(method, parameters)  # noqa
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"[Server] Error when trying to call server method (API)! Exception - {exception}")

        retry_on_fail = get_config()["server"]["vk"]["retry_method_on_fail"]

        if is_retry or not retry_on_fail:
            return None

        return server_method(method, parameters, True)


def server_message(text: str, attachmment: typing.Optional[str] = None, peer: typing.Optional[str] = None) -> None:
    """ Sends mesage to the server. """

    if peer is None:
        for config_peer in get_config()["server"]["vk"]["peers"]:
            server_message(text, attachmment, config_peer)
        return

    _text = f"<{get_name()}>\n{text}"

    debug_message("[Server] Sent new message!")

    server_method("messages.send", {
        "message": _text,
        "attachment": attachmment,
        "peer_id": peer
    })


def server_upload_photo(path: str) -> typing.Tuple[bool, str]:
    """ Uploads photo to the server. """

    server_uploader = vk_api.upload.VkUpload(_server_api)
    photo, *_ = server_uploader.photo_messages(path)

    if all(key in photo for key in ("owner_id", "id", "access_key")):
        owner_id = photo["owner_id"]
        photo_id = photo["id"]
        access_key = photo["access_key"]
        return True, f"photo{owner_id}_{photo_id}_{access_key}"

    return False, ""


def server_upload_document(path: str, title: str, peer: int, document_type: str = "doc") -> \
        typing.Tuple[bool, typing.Union[str, typing.Any]]:
    """ Uploads document to the server and returns it (as document string). """

    try:
        server_docs_api = _server_api.get_api().docs # noqa

        if "upload_url" in (upload_server := server_docs_api.getMessagesUploadServer(type=document_type, peer_id=peer)):
            upload_url = upload_server["upload_url"]
        else:
            return False, "Upload Server Error" + str(upload_server)

        request = json.loads(requests.post(upload_url, files={
            "file": open(path, "rb")
        }).text)

        if "file" in request:
            request = server_docs_api.save(file=request["file"], title=title, tags=[])
            document_id = request[document_type]["id"]
            document_owner_id = request[document_type]["owner_id"]
            return True, f"doc{document_owner_id}_{document_id}"

        debug_message(f"[Server] Error when uploading document (Request)! Request - {request}")
        return False, "Request Error" + str(request)
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        debug_message(f"Error when uploading document (Exception)! Exception: {exception}")
        return False, "Exception Error" + str(exception)


# Client.

def process_message(event) -> None:
    """ Processes message from the server. """

    message = event
    if get_config()["server"]["type"] == "VK_GROUP":
        message = message.message

    answer_text: str = "Void... (No response)"
    answer_attachment = None

    try:
        arguments = message.text.split(";")

        if len(arguments) == 0:
            return

        tags = arguments.pop(0)

        if tags == "alive":
            if peer_is_allowed(message.peer_id):
                answer_text = command_alive("", event).get_text()
            else:
                answer_text = "Sorry, but you don't have required permissions to call this command!"
        else:
            if list_intersects(parse_tags(tags), get_tags()):
                if peer_is_allowed(message.peer_id):
                    if len(arguments) == 0:
                        answer_text = "Invalid request! Message can`t be parsed! Try: tag1, tag2; command; args"
                    else:
                        command = str(arguments.pop(0)).lower().replace(" ", "")
                        command_arguments = ";".join(arguments)
                        command_result: CommandResult = execute_command(command, command_arguments, event)
                        command_result_attachment = command_result.get_attachment()

                        if command_result_attachment is not None:
                            uploading_path, uploading_title, uploading_type = command_result_attachment

                            if uploading_type == "photo":
                                uploading_status, uploading_result = \
                                    server_upload_photo(uploading_path)

                                if uploading_status:
                                    answer_text = uploading_title
                                    answer_attachment = uploading_result
                                else:
                                    answer_text = f"Error when uploading photo. Result - {uploading_result}"
                            elif uploading_type in ("doc", "audio_message"):
                                uploading_status, uploading_result = \
                                    server_upload_document(uploading_path, uploading_title,
                                                           message.peer_id, uploading_type)

                                if uploading_status:
                                    answer_text = uploading_title
                                    answer_attachment = uploading_result
                                else:
                                    answer_text = f"Error when uploading document with type `{uploading_type}`. " \
                                                  f"Result - {uploading_result}"

                            if get_config()["settings"]["delete_file_after_uploading"] and \
                                    command_result.should_delete_after_uploading():
                                fs.try_delete(uploading_path)
                        else:
                            answer_text = command_result.get_text()
                else:
                    answer_text = "Sorry, but you don't have required permissions to make this command!"
            else:
                return
    except Exception as exception:  # noqa, pylint: disable=broad-except, redefined-outer-name
        answer_text = f"Failed to process message answer. Exception - {exception}"

    if answer_text or answer_attachment:
        server_message(answer_text, answer_attachment, message.peer_id)


# Server (server_connect()).
_server_api = None
_server_longpoll = None
