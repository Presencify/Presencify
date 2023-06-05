import os
import re
import httpx
import hashlib
import socket as s
import winreg as wr
import subprocess as sp
from .browsers import BROWSERS
from .constants import Constants
from .logger import Logger


class Utils:
    @staticmethod
    def listdirEx(name: str, ext: str = None, exclude: bool = False) -> list:
        if not Utils.exists_file(name):
            return []
        if ext is None:
            return os.listdir(name)
        files = os.listdir(name)
        if exclude:
            return [file for file in files if not file.endswith(ext)]
        return [file for file in files if file.endswith(ext)]

    @staticmethod
    def exist_folder(folder_name: str) -> bool:
        return os.path.exists(folder_name)

    @staticmethod
    def exists_file(file_name: str) -> bool:
        return os.path.exists(file_name)

    @staticmethod
    def hash_string(string: str) -> str:
        hasher = hashlib.blake2b()
        hasher.update(string.encode("utf-8"))
        return hasher.hexdigest()

    @staticmethod
    def get_free_port():
        sock = s.socket(s.AF_INET, s.SOCK_STREAM)
        sock.bind(("localhost", 0))
        _, port = sock.getsockname()
        sock.close()
        return port

    @staticmethod
    def find_browser(progid: str) -> dict:
        for browser in BROWSERS:
            if re.search(browser["name"], progid, re.IGNORECASE):
                return browser
        return None

    @staticmethod
    def get_default_browser() -> dict:
        progid = wr.QueryValueEx(
            wr.OpenKey(
                wr.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice",
            ),
            "ProgId",
        )[0]
        if not progid:
            raise Exception("No default browser found")
        browser = Utils.find_browser(progid.split(".")[0])
        if not browser:
            raise Exception("Unsupported browser")
        browser["path"] = wr.QueryValueEx(
            wr.OpenKey(wr.HKEY_CLASSES_ROOT, progid + "\shell\open\command"), ""
        )[0].split('"')[1]
        return browser

    @staticmethod
    def find_windows_process(process_name: str) -> bool:
        res = (
            sp.check_output(
                f"WMIC PROCESS WHERE \"name='{process_name}'\" GET ExecutablePath",
                stderr=sp.PIPE,
            )
            .decode()
            .strip()
        )
        return len(res) > 0

    @staticmethod
    def fetch_github_presences() -> dict:
        response = httpx.get(Constants.PRESENCES_ENDPOINT)
        if response.status_code == 200:
            contents = response.json()
            presences = {}
            for content in contents:
                main_raw = Utils.fetch_github_presence_content(
                    content["name"], "main.py"
                )
                config_raw = Utils.fetch_github_presence_content(
                    content["name"], "config.json"
                )
                presences[content["name"]] = {"main": main_raw, "config": config_raw}
            return presences
        else:
            raise ValueError("Error while getting presences from github repo")

    @staticmethod
    def fetch_github_presence_content(presence_name: str, file_name: str) -> str:
        response = httpx.get(
            Constants.PRESENCES_ENDPOINT_CONTENT.format(
                name=presence_name, file=file_name
            )
        )
        if response.status_code == 200:
            return response.text
        else:
            raise ValueError("Error while getting presence content from github repo")

    @staticmethod
    def open_remote_browser(port: int) -> None:
        """
        Open a remote browser instance.
        For more security we use a random port.
        """
        browser = Utils.get_default_browser()
        if Utils.find_windows_process(browser["process"]["win32"]):
            Logger.write(
                msg=f"Another instance of {browser['name']} is already running",
                origin=__name__,
                print=False,
            )
            Logger.write(
                msg=f"This instance is not from Presencify, please close it and try again",
                origin=__name__,
                print=False,
            )
            raise RuntimeError("Can't connect to remote browser")

        Logger.write(
            msg=f"Opening remote {browser['name']} instance...",
            origin=__name__,
        )
        sp.Popen(
            [
                browser["path"],
                "--remote-debugging-port={port}".format(port=port),
                "--remote-allow-origins=*",
                "--disable-sync",
            ],
            stdout=sp.DEVNULL,
            stderr=sp.DEVNULL,
        )
