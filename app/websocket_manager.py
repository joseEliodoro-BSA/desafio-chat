import asyncio

class WebsocketManager:
    def __init__(self):
        self._websocket_connected: dict = None
        self.look = asyncio.Lock()
        
    def add_ws():
        pass

    async def remove_ws(self, id: str):
        if id in self._websocket_connected:
            async with self.look:
                del self._websocket_connected[id]
    
    