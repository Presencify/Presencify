import os
import json
import time
import uuid
import pypresence
import threading
import presencify


class Presence:
    data = {}

    def __init__(self, location: str = None):
        if location is None:
            raise ValueError("Location can't be None")
        self.id = str(uuid.uuid4())
        self.__rpc = self.__runtime = None
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
            if self.__uses_browser:
                presencify.Logger.write(
                    msg=f"Connecting {self.__location} to browser",
                    origin=self,
                )
                self.__runtime = presencify.Runtime()
                self.__runtime.connect()
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
            "runtime": self.__runtime,
            "running": self.running,
            "update_rpc": self.update,
        }
        exec(self.__main_code, globals_dict)
        self.__on_script_end()

    def __on_script_end(self) -> None:
        presencify.Logger.write(msg=f"Script for {self.name} has ended", origin=self)
        self.stop()

    def __eq__(self, other) -> bool:
        if not isinstance(other, Presence):
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
        if self.__uses_browser:
            presencify.Logger.write(
                msg=f"Disconnecting browser for {self.name}", origin=self
            )
            self.__runtime.close()
        presencify.Logger.write(msg=f"Stopped loop RPC for {self.name}", origin=self)

    def start(self) -> None:
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
        self.data = kwargs

    def __loop(self) -> None:
        while self.running:
            time.sleep(15)
            if not self.connected:
                continue
            presencify.Logger.write(
                msg=f"Updating {self.name}: {self.data}", origin=self
            )
            self.__rpc.update(**self.data)
