"""
Note, this is a beta feature and may not work as expected.
"""
import json
import urllib.request as request
from websocket import create_connection
from .constants import Constants


class Runtime:
    pages = []

    @staticmethod
    def enable():
        try:
            with request.urlopen(Constants.REMOTE_URL) as response:
                return True
        except:
            return False

    @staticmethod
    def execute(code):
        if not Runtime.enable():
            return None
        with request.urlopen(Constants.REMOTE_URL) as response:
            data = json.loads(response.read())
        page = list(filter(lambda page: page["type"] == "page", data))[0]
        ws = create_connection(page["webSocketDebuggerUrl"])
        ws.send(
            json.dumps(
                {"id": 1, "method": "Runtime.evaluate", "params": {"expression": code}}
            )
        )
        result = json.loads(ws.recv())["result"]["result"]["value"]
        ws.close()
        return result
