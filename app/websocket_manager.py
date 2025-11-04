from fastapi import WebSocket
import asyncio
from typing import Dict, List, Set
import json

class manager:
    def __init__(self):
        self.clients: Dict[str, WebSocket] = {}
        self.rooms: Dict[str, Set[str]]
    
    async def connect(self, websocket: WebSocket, client_id):
        await websocket.accept()
        self.clients[client_id] = websocket
    
    async def broadcast(self, message):
        for _, websocket in self.clients.items():
            await websocket.send_text(json.dumps(message))

    async def disconnect(self, client_id):
        if client_id in self.clients:
            del self.clients[client_id]

    async def send(self, client_id, message):
        if client_id in self.clients:
            await self.clients[client_id].send_text(json.dumps(message))

websocket_manager = manager()