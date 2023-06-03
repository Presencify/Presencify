import re
import socket as s
import winreg as wr
import subprocess as sp
from .browsers import BROWSERS


class Utils:
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
