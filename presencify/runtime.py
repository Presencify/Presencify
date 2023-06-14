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


class Tab:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __eq__(self, other):
        if not isinstance(other, Tab):
            return False
        return self.url == other.url

    def __repr__(self):
        return f"<Tab url={self.url}>"

    def __str__(self):
        return self.url

    def execute(self, code: str) -> None:
        ws = create_connection(self.webSocketDebuggerUrl)
        ws.send(
            json.dumps(
                {"id": 1, "method": "Runtime.evaluate", "params": {"expression": code}}
            )
        )
        data = json.loads(ws.recv())
        ws.close()
        _type = data["result"]["result"]["type"]
        if _type == "object" or _type == "undefined":
            return None
        return data["result"]["result"]["value"]

    def media_session(self) -> MediaSession:
        """
        Get the current media session.
        """
        data = self.execute(
            "[navigator.mediaSession.playbackState,\
                        navigator.mediaSession.metadata.album || '',\
                        navigator.mediaSession.metadata.artist,\
                        navigator.mediaSession.metadata.artwork[0].src,\
                        navigator.mediaSession.metadata.title].join('@')"
        )
        if data is None:
            return None
        data = data.split("@")
        data = {
            "state": data[0],
            "album": data[1],
            "artist": data[2],
            "image": data[3],
            "title": data[4],
        }
        return MediaSession(**data)


class Runtime:
    def __init__(self, port: int, origin: str):
        self.__port = port
        self.__tabs = []
        self.__origin = origin
        self.__connected = False
        self.__current_tab = None

    @property
    def connected(self) -> bool:
        return self.__connected

    @property
    def current_tab(self) -> Tab:
        self.__update()
        return self.__current_tab

    def __req(self) -> list:
        """
        Request the remote browser for get the tabs.
        """
        try:
            res = httpx.get(Constants.REMOTE_URL.format(port=self.__port))
            return res.json()
        except Exception as exc:
            Logger.write(
                msg=f"{self.__origin} failed to connect and get tabs: {exc}",
                origin=self,
                level="error",
            )
            return []

    def __update(self):
        """
        Update tabs and return the current tab or the tab specified.
        """
        if not self.__connected:
            Logger.write(
                msg=f"Remote browser update failed for {self.__origin}: not connected!",
                origin=self,
                level="warning",
            )
            return
        try:
            tabs = self.__req()
            if len(tabs) == 0:
                raise RuntimeError("No information received from the remote browser")
            self.__tabs = [tab for tab in tabs if tab["type"] == "page"]
            if len(self.__tabs) == 0:
                raise RuntimeError("No tabs found in the remote browser")
            self.__tabs = [Tab(**tab) for tab in self.__tabs]
            self.__current_tab = self.__tabs[0]
            Logger.write(msg=f"Updated tabs in {self.__origin}!", origin=self)
        except Exception as exc:
            self.__connected = False
            self.__tabs = []
            Logger.write(
                msg=f"Failed to update tabs in {self.__origin}: {exc}",
                origin=self,
                level="error",
            )

    def tabs(self, url_pattern: str = None, force_update: bool = False) -> list:
        """
        Get all tabs or all tabs with the specified url pattern.
        """
        if force_update:
            self.__update()
        if url_pattern is None:
            return self.__tabs
        return [tab for tab in self.__tabs if url_pattern in tab.url]

    def connect(self) -> None:
        """
        Connect to the remote browser.
        """
        if self.__connected:
            Logger.write(
                msg="Remote browser already connected!", origin=self, level="warning"
            )
            return
        self.__update()
        self.__connected = True
        Logger.write(msg=f"Remote browser for {self.__origin} connected!", origin=self)

    def close(self) -> None:
        if self.__connected is False:
            Logger.write(
                msg=f"Remote browser for {self.__origin} already disconnected!",
                origin=self,
            )
            return
        self.__connected = False
        Logger.write(
            msg=f"Remote browser for {self.__origin} disconnected!", origin=self
        )
