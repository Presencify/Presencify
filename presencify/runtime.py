"""
Note, this is a beta feature and may not work as expected.
"""
import json
import requests
import inspect
from websocket import create_connection
from .constants import Constants
from .logger import Logger


class MediaSession:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class Runtime:
    """
    Used to execute some JavaScript code in the browser.
    """

    __slots__ = (
        "__pages",
        "__enable",
        "__current_tab",
        "__ws",
        "__connected",
    )

    def __init__(self):
        if inspect.stack()[1].filename == "<string>":
            Logger.write(
                msg="Please don't use the Runtime class from presencify, use 'runtime' directly",
                origin=self,
                level="error",
            )
            return
        self.__connected = False
        self.__current_tab = self.__ws = None

    def __update(self):
        if not self.__connected:
            return
        self.__pages = self.__request()
        self.__pages = self.__filter(self.__pages)
        self.__current_tab = self.__pages[0]
        self.__ws_close()
        self.__ws = create_connection(self.__current_tab["webSocketDebuggerUrl"])

    def __request(self) -> dict:
        with requests.get(Constants.REMOTE_URL) as response:
            return json.loads(response.text)
        return {}

    def __filter(self, data: dict) -> dict:
        return [element for element in data if element["type"] == "page"]

    def __ws_close(self):
        if self.__ws and self.__ws.connected:
            self.__ws.close()

    def close(self) -> None:
        if not self.__connected:
            return
        self.__ws_close()
        self.__connected = False

    @property
    def url(self) -> str:
        return self.__current_tab["url"]

    @property
    def title(self) -> str:
        return self.__current_tab["title"]

    @property
    def icon(self) -> str:
        return self.__current_tab["faviconUrl"]

    def mediaSession(self):
        # TODO: make a better implementation
        if not self.__connected:
            return None
        self.__update()
        self.__ws.send(
            json.dumps(
                {
                    "id": 0,
                    "method": "Runtime.evaluate",
                    "params": {
                        "expression": "\
                        [navigator.mediaSession.metadata.album,\
                        navigator.mediaSession.metadata.artist,\
                        navigator.mediaSession.metadata.artwork[0].src,\
                        navigator.mediaSession.metadata.title].join('@')",
                    },
                }
            )
        )
        data = json.loads(self.__ws.recv())
        if data["result"]["result"]["type"] == "object":
            return None
        data = data["result"]["result"]["value"].split("@")
        return MediaSession(
            album=data[0],
            artist=data[1],
            image=data[2],
            title=data[3],
        )

    def connect(self) -> None:
        try:
            if self.__connected:
                return
            data = self.__request()
            data = self.__filter(data)
            if len(data) == 0:
                raise RuntimeError("No pages found")
            self.__current_tab = data[0]
            self.__connected = True
        except Exception as exc:
            raise RuntimeError("Failed to connect to browser runtime") from exc

    def is_enabled(self) -> bool:
        return self.__connected
