import pypresence as pp
from .logger import Logger

class Presence:
    __slots__ = ("__client_id", "__rpc", "__name")

    def __init__(self, client_id: str, name: str = "Unknown"):
        self.__client_id = client_id
        self.__name = name
        self.__rpc = pp.AioPresence(client_id)

    def __repr__(self) -> str:
        return f"Presence({self.__name}, {self.__client_id})"

    async def __aenter__(self) -> "Presence":
        await self.__rpc.connect()
        return self
    
    async def __aexit__(self, exc_type: type, exc_value: Exception, traceback: type) -> None:
        await self.__rpc.close()
    
    async def close(self) -> None:
        await self.__rpc.close()

    async def update(self, data: dict) -> None:
        await self.__rpc.update(**data)
    
    @property
    def name(self) -> str:
        return self.__name
    
    @property
    def client_id(self) -> str:
        return self.__client_id