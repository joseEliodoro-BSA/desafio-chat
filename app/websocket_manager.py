from fastapi import WebSocket
import asyncio
from typing import Dict, List, Set
import json
from app.pubsub_service import PubSub
from threading import Thread

class manager:
    def __init__(self):
        self.clients: Dict[str, WebSocket] = {}
        self.look = asyncio.Lock()
        self.pubsub = PubSub()

    async def connect(self, websocket: WebSocket, client_id):
        await websocket.accept()
        async with self.look:
            self.clients[client_id] = websocket
    
    # async def broadcast(self, message):
    #     for websocket in self.clients.values():
    #         await websocket.send_text(json.dumps(message))

    async def broadcast(self, message, exclude_socket_id: str | None = None):
        for socket_id, websocket in self.clients.items():
            if not (socket_id == exclude_socket_id):
                await websocket.send_text(json.dumps(message))

    async def disconnect(self, client_id):
        if client_id in self.clients:
            async with self.look:
                del self.clients[client_id]

    async def disconnect_all(self):
        for socket_id in self.clients.keys():
            await self.disconnect(socket_id)
            
    async def send(self, socket_id, message):
        if socket_id in self.clients:
            await self.clients[socket_id].send_text(json.dumps(message, ensure_ascii=False))

    async def receive_geral(self, msg: Dict):
        if msg["channel"] == "geral":
            data = json.loads(msg["data"])
            socket_id = data["socket_id"]
            del data["socket_id"]
            await self.broadcast(data, exclude_socket_id=socket_id)

    async def send_geral(self, socket_id: str, msg: Dict):
        msg["socket_id"] = socket_id
        self.pubsub.pub("geral", msg)

    async def subscribes_channel(self):
        # Rodar subscribers em threads para não travar o event loop
        Thread(target=self.pubsub.sub, args=("geral", self.receive_geral), daemon=True).start()
        Thread(target=self.pubsub.sub, args=("private", self.broadcast), daemon=True).start()


websocket_manager = manager()