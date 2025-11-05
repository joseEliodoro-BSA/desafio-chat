from fastapi import WebSocket
import asyncio
from typing import Dict, List, Set
import json

class manager:
    def __init__(self):
        self.clients: Dict[str, WebSocket] = {}
        self.look = asyncio.Lock()

    async def connect(self, websocket: WebSocket, client_id):
        await websocket.accept()
        async with self.look:
            self.clients[client_id] = websocket
    
    async def broadcast(self, message):
        for websocket in self.clients.values():
            await websocket.send_text(json.dumps(message))

    async def disconnect(self, client_id):
        if client_id in self.clients:
            async with self.look:
                del self.clients[client_id]

    async def send(self, socket_id, message):
        if socket_id in self.clients:
            await self.clients[socket_id].send_text(json.dumps(message, ensure_ascii=False))

websocket_manager = manager()