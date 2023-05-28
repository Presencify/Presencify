import json
import websockets as ws
import asyncio
from .presence import Presence
from .constants import Constants
from .logger import Logger

class App:

    __slots__ = ("__host", "__port", "__ws", "__rpcs")

    def __init__(self, host: str = "localhost", port: int = 6996):
        self.__host, self.__port = host, port
        self.__ws, self.__rpcs = None, ()
    
    def __exception_handler(self, exc: Exception) -> None:
        Logger.write(msg=str(exc), level="error", origin=self)

    async def __aenter__(self) -> "App":
        try:
            self.__ws = await ws.serve(self.__handler, self.__host, self.__port)
            Logger.write(msg="initialized.", origin=self)
        except Exception as exc:
            self.__exception_handler(exc)

    async def __aexit__(
        self, exc_type: type, exc_value: Exception, traceback: type
    ) -> None:
        Logger.write(msg="Closing...", origin=self)
        self.__ws.close()
        await self.__ws.wait_closed()
        Logger.write(msg="Closed.", origin=self)


    def __new_rpc(self, client_id: str, name: str) -> Presence:
        presence = Presence(client_id, name)
        self.__rpcs += (presence,)
        return self.__rpcs[-1]

    def __get_rpc(self, client_id: str, name: str) -> Presence:
        for rpc in self.__rpcs:
            if rpc.client_id == client_id and rpc.name == name:
                return rpc
        return None

    async def __handler(self, websocket: ws.WebSocketServerProtocol, path: str) -> None:
        data = await websocket.recv()
        data = json.loads(data)
        if not "opcode" in data:
            Logger.write(
                msg=f"An invalid data was received from {websocket.remote_address}",
                origin=self,
            )
            return
        opcode = data["opcode"]
        if not opcode in Constants.OPCODES:
            Logger.write(
                msg=f"An invalid opcode was received from {websocket.remote_address}",
                origin=self,
            )
            return
        Logger.write(
            msg=f"Received {Constants.OPCODES[opcode]} from {websocket.remote_address} as {data['name']}",
            origin=self,
        )
        if opcode == 0:
            exist = self.__get_rpc(data["client_id"], data["name"])
            if exist:
                Logger.write(
                    msg=f"An RPC with the same name and client_id already exists.",
                    origin=self,
                )
                return
            rpc = self.__new_rpc(data["client_id"], data["name"])
            await rpc.__aenter__()
            await rpc.update(data["payload"])
            Logger.write(
                msg=f"{rpc} successfully added to the list.",
                origin=self,
            )
        elif opcode == 1:
            rpc = self.__get_rpc(data["client_id"], data["name"])
            if rpc is None:
                Logger.write(
                    msg=f"An invalid RPC was received from {websocket.remote_address}",
                    origin=self,
                )
                return
            await rpc.update(data["payload"])
            Logger.write(msg=f"{rpc} successfully updated", origin=self)
        elif opcode == 2:
            rpc = self.__get_rpc(data["client_id"], data["name"])
            if rpc is None:
                Logger.write(
                    msg=f"An invalid RPC was received from {websocket.remote_address}",
                    origin=self,
                )
                return
            asyncio.run_coroutine_threadsafe(rpc.close(), asyncio.get_event_loop())
            self.__rpcs = tuple(
                filter(lambda rpc: rpc.client_id != data["client_id"], self.__rpcs)
            )
            Logger.write(msg=f"{rpc} successfully closed", origin=self)
    

    async def run(self) -> None:
        async with self:
            Logger.write(msg=f"Started on {self.__host}:{self.__port}", origin=self)
            await self.__ws.wait_closed()
