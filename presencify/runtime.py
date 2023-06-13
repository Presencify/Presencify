"""
Note, this is a beta feature and may not work as expected.
"""
import json
import httpx
import subprocess as sp
from websocket import create_connection
from .constants import Constants
from .logger import Logger
from .utils import Utils


class MediaSession:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __eq__(self, other):
        if not isinstance(other, MediaSession):
            return False
        return (
            self.artist == other.artist
            and self.artwork == other.artwork
            and self.title == other.title
        )


class Runtime:
    """
    Used to execute some JavaScript code in the browser.
    """

    __slots__ = (
        "__pages",
        "__enable",
        "__current_tab",
        "__ws",
        "__port",
        "__connected",
    )

    def __init__(self, port: int):
        self.__port = port
        self.__connected = False
        self.__current_tab = self.__ws = None

    @property
    def connected(self) -> bool:
        return self.__connected

    def __update(self):
        if not self.__connected:
            return
        self.__pages = self.__request()
        if self.__pages == []:
            Logger.write(
                msg="Remote browser closed unexpectedly!",
                origin=self,
                level="error",
            )
            self.__connected = False
            return
        self.__pages = self.__filter(self.__pages)
        self.__current_tab = self.__pages[0]
        self.__ws_close()
        self.__ws = create_connection(self.__current_tab["webSocketDebuggerUrl"])

    def __request(self) -> dict:
        try:
            response = httpx.get(Constants.REMOTE_URL.format(port=self.__port))
            return response.json()
        except Exception as exc:
            return []

    def __filter(self, data: dict) -> dict:
        return [element for element in data if element["type"] == "page"]

    def __ws_close(self):
        if self.__ws and self.__ws.connected:
            self.__ws.close()

    def close(self) -> None:
        if not self.__connected:
            Logger.write(
                msg="Cannot close a connection that is not open!",
                origin=self,
                level="error",
            )
            return
        self.__ws_close()
        self.__connected = False
        Logger.write(msg="Closed connection with browser", origin=self)

    @property
    def url(self) -> str:
        self.__update()
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
                        [navigator.mediaSession.playbackState,\
                        navigator.mediaSession.metadata.album,\
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
            playbackState=data[0],
            album=data[1],
            artist=data[2],
            image=data[3],
            title=data[4],
        )

    def execute(self, code: str) -> None:
        if not self.__connected:
            return
        self.__update()
        self.__ws.send(
            json.dumps(
                {
                    "id": 0,
                    "method": "Runtime.evaluate",
                    "params": {"expression": code},
                }
            )
        )
        data = json.loads(self.__ws.recv())
        if data["result"]["result"]["type"] == "undefined":
            return None
        return data["result"]["result"]["value"]

    def connect(self) -> None:
        if self.__connected:
            return
        data = self.__request()
        data = self.__filter(data)
        if len(data) == 0:
            raise RuntimeError("No pages found")
        self.__current_tab = data[0]
        self.__connected = True
        Logger.write(
            msg=f"Browser remote instance connected successfully",
            origin=self,
        )

    def is_enabled(self) -> bool:
        return self.__connected
