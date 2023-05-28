import websockets as ws
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

    async def __handler(self, websocket: ws.WebSocketServerProtocol, path: str) -> None:
        data = await websocket.recv()
        Logger.write(msg=f"Received data from a remote client: {data}", origin=self)

    async def run(self) -> None:
        async with self:
            Logger.write(msg=f"Started on {self.__host}:{self.__port}", origin=self)
            await self.__ws.wait_closed()
