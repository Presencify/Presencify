import os
import json
import time
import uuid
import pypresence
import threading
import presencify


class Presence:
    """
    Deprecated, use PresenceEx instead
    """

    data = {}

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.running = False
        self.uses_browser = kwargs.get("uses_browser", False)
        self.rpc = pypresence.Presence(self.client_id)
        self.code_t = None
        self.rpc_t = None
        self.running_event = threading.Event()

    def start(self):
        try:
            self.rpc.connect()
        except Exception as e:
            presencify.Logger.write(msg=e, level="error", origin=self)
            return
        if not presencify.Runtime.enable() and self.uses_browser:
            presencify.Logger.write(
                msg="Runtime not enabled, can't start presence",
                level="error",
                origin=self,
            )
            return
        self.running = True
        globals_dict = {"running": self.running, "update": self.update}
        globals_dict["running_event"] = self.running_event
        self.code_t = threading.Thread(
            target=exec, args=(self.main_code, globals_dict), daemon=True
        )
        self.rpc_t = threading.Thread(target=self.loop, daemon=True)
        self.code_t.start()
        self.rpc_t.start()

    def loop(self):
        presencify.Logger.write(msg=f"Started loop RPC for {self}", origin=self)
        while self.running:
            self.rpc.update(**self.data)
            time.sleep(15)
        self.rpc.close()
        presencify.Logger.write(msg=f"Stopped loop RPC for {self}", origin=self)

    def stop(self):
        presencify.Logger.write(msg=f"Stopping presence {self}", origin=self)
        self.running = False
        self.running_event.set()
        presencify.Logger.write(msg=f"Stopped presence {self}", origin=self)

    def update(self, data):
        self.data = data

    def __repr__(self):
        return f"Presence({self.name})"


class PresenceEx:
    data = {}

    def __init__(self, location: str = None):
        if location is None:
            raise ValueError("Location can't be None")
        self.id = str(uuid.uuid4())
        self.__rpc = None
        self.__location = location
        self.__script_thread = self.__rpc_thread = None
        self.connected = self.loaded = self.running = False
        try:
            self.__load()
        except Exception as exc:
            presencify.Logger.write(
                msg=f"When loading {self.__location}: {exc}",
                level="error",
                origin=self,
            )

    def __load_file(self, filename: str) -> str:
        with open(f"{self.__location}/{filename}", "r") as file:
            return file.read()

    def __load_config(self, config: dict) -> None:
        try:
            self.__name = config["name"]
            self.__author = config["author"]
            self.__version = config["version"]
            self.__client_id = config["client_id"]
            self.__uses_browser = config["uses_browser"]
            self.__rpc = pypresence.Presence(self.__client_id)
        except KeyError as exc:
            raise ValueError(f"Missing key {exc} in config.json")

    def __load(self):
        if self.loaded:
            return
        files = os.listdir(self.__location)
        if len(files) == 0:
            raise ValueError(f"No files found in {self.__location}")
        try:
            self.__main_code = self.__load_file("main.py")
            config = json.loads(self.__load_file("config.json"))
            self.__load_config(config)
        except FileNotFoundError as exc:
            raise ValueError(f"Missing file {exc.filename}")
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in config.json ({exc})")
        presencify.Logger.write(
            msg=f"Loaded {self.__name} v{self.__version} by {self.__author}",
            origin=self,
        )
        self.loaded = True

    def __execute_script(self) -> None:
        globals_dict = {
            "running": self.running,
            "update_rpc": self.update,
        }
        exec(self.__main_code, globals_dict)
        self.__on_script_end()

    def __on_script_end(self) -> None:
        presencify.Logger.write(msg=f"Script for {self.name} has ended", origin=self)
        self.stop()

    def __eq__(self, other) -> bool:
        if not isinstance(other, PresenceTwo):
            return False
        if self.id == other.id:
            return False
        return self.name == other.name or self.client_id == other.client_id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def client_id(self) -> str:
        return self.__client_id

    def stop(self) -> None:
        if not self.running and not self.connected:
            return
        self.running = False
        if self.connected:
            presencify.Logger.write(
                msg=f"Disconnecting RPC for {self.name}", origin=self
            )
            self.__rpc.close()
            self.connected = False
        presencify.Logger.write(msg=f"Stopped loop RPC for {self.name}", origin=self)

    def start(self) -> None:
        if not presencify.Runtime.enable() and self.__uses_browser:
            presencify.Logger.write(
                msg=f"Runtime not enabled, can't start presence {self.name}",
                level="error",
                origin=self,
            )
            return
        self.__rpc.connect()
        self.connected = True
        self.running = True
        globals_dict = {
            "running": self.running,
            "update_rpc": self.update,
        }
        self.__script_thread = threading.Thread(
            target=self.__execute_script, daemon=True
        )
        self.__rpc_thread = threading.Thread(target=self.__loop, daemon=True)
        self.__script_thread.start()
        self.__rpc_thread.start()

    def update(self, **kwargs) -> None:
        # TODO:valite kwargs
        presencify.Logger.write(
            msg=f"Updating {self.name}: {kwargs}", origin=self, _print=False
        )
        self.data = kwargs

    def __loop(self) -> None:
        self.__rpc.update(**self.data)
        while self.running:
            time.sleep(15)
            if not self.connected:
                continue
            self.__rpc.update(**self.data)
