from fastapi import WebSocket

from typing import Dict, List
from threading import Lock
import json

class Singleton(type):

    _instances = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

class ConnectionData:
    def __init__(self, username, websocket):
        self.username: str = username
        self.websocket: WebSocket = websocket

Connections = Dict[str, ConnectionData]

class WebsocketManager(metaclass=Singleton):
    def __init__(self):
        self._websocket_connected: Connections = {}
        self.look = Lock()
        
    @property
    def websocket_connected(self):
        return self._websocket_connected
    
    async def connect(self, id: str, websocket: WebSocket, username: str):
        await websocket.accept()

        is_connect = self.find_client_by_username(username) 

        with self.look:
            self._websocket_connected[id] = ConnectionData(
                username=username, websocket= websocket
            )

        if (is_connect):
            await self.send(id, {"error": f"usuário já conectado"})
            await self.disconnect(id)

    async def disconnect(self, id: str):
        if id in self.websocket_connected:
            with self.look:
                websocket: WebSocket = self._websocket_connected.pop(id).websocket
                await websocket.close()
    
    def find_client_by_username(self, username):
        for socket_id, connection in self.websocket_connected.items():
            if connection.username == username:    
                return socket_id
    
    async def broadcast(self, message: Dict, exclude_socket_id: List[str] | None = None):
        for socket_id, connection in self.websocket_connected.items():
            if not (socket_id in exclude_socket_id):
                await connection.websocket.send_text(json.dumps(message, ensure_ascii=False))

    async def disconnect_all(self):
        for socket_id in self.websocket_connected.keys():
            await self.disconnect(socket_id)
    
    async def send(self, socket_id, message: Dict):
        if socket_id in self.websocket_connected:
            await self.websocket_connected[socket_id].websocket.send_text(
                json.dumps(message, ensure_ascii=False)
            )

    def find_client_connect_room(self, room):
        client_connects_room = []
        for connection in self.clients_connected.values():
            websocket = connection.websocket
            if room == websocket.path_params.get("room"):
                socket_id = self.find_client_by_username(websocket.query_params.get("username"))
                client_connects_room.append(socket_id)
        return client_connects_room