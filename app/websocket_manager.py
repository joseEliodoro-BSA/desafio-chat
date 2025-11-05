from fastapi import WebSocket
import asyncio
from typing import Dict, List
import json
from app.pubsub_service import PubSub
from threading import Thread


class ConnectionData:
    def __init__(self, username, websocket):
        self.username: str = username
        self.websocket: WebSocket = websocket

Connections = Dict[str, ConnectionData]

class WebSocketManager:
    def __init__(self):
        self.clients_connected: Connections = {}
        self.look = asyncio.Lock()
        self.pubsub = PubSub()

    async def connect(self, websocket: WebSocket, socket_id, username: str):
        await websocket.accept()
        async with self.look:
            self.clients_connected[socket_id] = ConnectionData(username, websocket)

    async def broadcast(self, message, exclude_socket_id: List[str] | None = None):
        for socket_id, connection_data in self.clients_connected.items():
            if not (socket_id in exclude_socket_id):
                await connection_data.websocket.send_text(json.dumps(message))

    async def disconnect(self, socket_id: str):
        if socket_id in self.clients_connected:
            async with self.look:
                del self.clients_connected[socket_id]

    async def disconnect_all(self):
        for socket_id in self.clients_connected.keys():
            await self.disconnect(socket_id)
            
    async def send(self, socket_id, message: Dict):
        if socket_id in self.clients_connected:
            await self.clients_connected[socket_id].websocket.send_text(json.dumps(message, ensure_ascii=False))

    async def receive_geral(self, msg: Dict):
        if msg["channel"] == "geral":
            data = json.loads(msg["data"])
            socket_id = data["socket_id"]
            del data["socket_id"]
            await self.broadcast(data, exclude_socket_id=[socket_id])

    def find_client_by_username(self, username):
        for socket_id, connect in self.clients_connected.items():
            if connect.username == username:
                return socket_id

    async def receive_private(self, msg: Dict):
        if msg["channel"] == "private":
            data = json.loads(msg["data"])
            send_socket_id = data["socket_id"]
            
            username_receive = data["username_receive"]
            receive_socket_id = self.find_client_by_username(username=username_receive)
            del data["socket_id"]
            if receive_socket_id:
                await self.send(receive_socket_id, data)
            else:
                await self.send(send_socket_id, {"error": f"usuário {username_receive} não foi encontrado ou não conectado"})

    async def pub_message(self, channel: str, socket_id: str, msg: Dict):
        msg["socket_id"] = socket_id
        self.pubsub.pub(channel, msg)

    async def subscribes_channel(self):
        # Rodar subscribers em threads para não travar o event loop
        Thread(target=self.pubsub.sub, args=("geral", self.receive_geral), daemon=True).start()
        Thread(target=self.pubsub.sub, args=("private", self.receive_private), daemon=True).start()


websocket_manager = WebSocketManager()