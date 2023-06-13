import os
import sys
import json
import time
import uuid
import pypresence
import threading
import presencify


class Presence:
    data = {
        "start": time.time(),
        "end": time.time(),
    }

    def __init__(self, location: str = None):
        if location is None:
            raise ValueError("Location can't be None")
        self.id = str(uuid.uuid4())
        self.__rpc = self.__runtime = None
        self.__location = location
        self.__original_import = __import__
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

    def __check_imports(
        self, name, globals=None, locals=None, fromlist=(), level=0
    ) -> None:
        if name not in presencify.Constants.ALLOWED_MODULES:
            raise ImportError(f"Module {name} is not allowed")
        return presencify.Constants.ALLOWED_MODULES[name]

    def __execute_script(self) -> None:
        for module_name in presencify.Constants.ALLOWED_MODULES.keys():
            sys.modules[module_name] = presencify.Constants.ALLOWED_MODULES[module_name]
        sys.modules["builtins"].__import__ = self.__check_imports
        globals_dict = {
            "runtime": self.__runtime,
            "running": self.running,
            "update_rpc": self.update,
        }
        exec(self.__main_code, globals_dict)
        self.__on_script_end()

    def __reset_modules(self) -> None:
        sys.modules["builtins"].__import__ = self.__original_import

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

    @property
    def folder_name(self) -> str:
        return self.__location.split("/")[-1]

    @property
    def main_code(self) -> str:
        return self.__main_code

    @property
    def config_file(self) -> str:
        return self.__load_file("config.json")

    @property
    def uses_browser(self) -> bool:
        return self.__uses_browser

    @property
    def author(self) -> str:
        return self.__author

    def stop(self) -> None:
        try:
            self.__reset_modules()
        except Exception as exc:
            presencify.Logger.write(
                msg=f"When resetting modules for {self.name}: {exc}",
                level="error",
                origin=self,
            )
        self.running = False
        presencify.Logger.write(msg=f"Stopped {self.name}", origin=self)

    def disconnect(self) -> None:
        if self.connected:
            presencify.Logger.write(msg=f"Disconnecting {self.name}...", origin=self)
            try:
                self.__rpc.close()
            except Exception as exc:
                presencify.Logger.write(
                    msg=f"When disconnecting {self.name}: {exc}",
                    level="error",
                    origin=self,
                )
            self.connected = False
        if self.__uses_browser:
            presencify.Logger.write(
                msg=f"Disconnecting browser for {self.name}...", origin=self
            )
            if self.__runtime is None:
                presencify.Logger.write(
                    msg=f"Browser for {self.name} is not connected, skipping...",
                    origin=self,
                )
            else:
                self.__runtime.close()
        self.running = False
        presencify.Logger.write(
            msg=f"Disconnected {self.name} successfully", origin=self
        )

    def __connect_browser(self, port: int) -> None:
        if self.__uses_browser:
            presencify.Logger.write(
                msg=f"Connecting {self.__location} to browser",
                origin=self,
            )
            self.__runtime = presencify.Runtime(port=port)
            self.__runtime.connect()

    def start(self, port: int = None) -> None:
        if port is not None:
            self.__connect_browser(port)
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
        # TODO: valite kwargs
        self.data = kwargs
        self.data["large_text"] = f"{presencify.__title__} v{presencify.__version__}"
        presencify.Logger.write(
            msg=f"Local update for {self.name}: {kwargs}", origin=self, print=False
        )

    def __loop(self) -> None:
        while self.running:
            if self.connected:
                presencify.Logger.write(msg=f"Updating {self.name}", origin=self)
                presencify.Logger.write(
                    msg=f"Sending {self.data}", origin=self, print=False
                )
                self.__rpc.update(**self.data)
            time.sleep(15)
