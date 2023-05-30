import time
import pypresence
import threading
import presencify


class Presence:
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
