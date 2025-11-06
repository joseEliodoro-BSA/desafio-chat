from fastapi import WebSocket, HTTPException

from typing import Dict, List
from threading import Thread
from datetime import datetime
import asyncio
import json


from app.pubsub_service import PubSub
from app.db import user_collection, chats_collection
from app.schemas import Message

# from app.singleton import get_websocket_manager_singleton

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
        #self.username =
        #self.websocket_id =
    
    async def connect(self, websocket: WebSocket, socket_id: str, username: str):
        # get_websocket_manager_singleton().add_ws()
        await websocket.accept()
        async with self.look:
            self.clients_connected[socket_id] = ConnectionData(username, websocket)
        if not await user_collection.find_one({"username": username}):
            await self.send(socket_id, {"error": f"usuário {username} não foi encontrado ou não conectado"})
            await self.disconnect(socket_id)
        else:
            await self.send(socket_id, {"code": 200, "details": "conexão iniciada com sucesso"})

    async def save_message_geral(self, msgDto: Message):
        new_msg = {"date": datetime.now().timestamp(), **msgDto.model_dump(exclude=["_id", "date", "username_receive"], exclude_none=True)}
        result = await chats_collection.insert_one(new_msg)
        new_msg["_id"] = f"{result.inserted_id}"
        
        return new_msg

    async def save_message_private(self, msgDto: Message):

        if not await user_collection.find_one({"username": msgDto.username_receive}):
            raise HTTPException(404, "destinatário não encontrado")
        
        new_msg = {"date": datetime.now().timestamp(), **msgDto.model_dump(exclude=["_id", "date"], exclude_none=True)}
        result = await chats_collection.insert_one(new_msg)
        new_msg["_id"] = f"{result.inserted_id}"
        
        return new_msg

    async def wait_command(self, websocket: WebSocket, socket_id: str, username: str, room):
        websocket: WebSocket = self.clients_connected[socket_id].websocket

        while True:
            data: str = await websocket.receive_text()
            data_json: dict = json.loads(data)
            if data_json["command"] == "send_message":

                await self.check_room_type(
                    room=room,
                    socket_id=socket_id,
                    username=username,
                    data=data_json
                    )
                #handle_general_room()
                #handle_private_room()
                #handle_specific_room()
                
            
            elif data_json.get("command") == "find":
                await self.send(socket_id, {"code": 200, "detail": "hello word"})
            else:
                await self.send(socket_id, {"code": 400, "error": "inválid command"})

    async def check_room_type(self, room:str, socket_id: str, username:str, data: Dict):
        msg = data["msg"]
        if(room == "geral"):
            await self.handle_general_room(socket_id, username, msg, room)                  
        elif(room == "private"):
            await self.handle_private_room(socket_id, username, msg, room)                    
        else:
            await self.handle_specific_room()

    async def handle_general_room(self, socket_id: str, username: str, msg: str, room: str):
        try:
            message = await self.save_message_geral(Message(username=username, msg=msg, chat=room))
            await self.pub_message(
                channel="geral", 
                socket_id=socket_id,
                msg=message
            )
        except HTTPException as e:
            await self.send(socket_id, {"code": 400, "error": e.detail})    

    async def handle_private_room(self, socket_id: str, username: str, msg: str, room: str, data: Dict):
        username_receive = data["username_receive"]
        
        if not username_receive:
            await self.send(socket_id, {"code": 400, "error": "requisição inválida"}) 
            return False
        try:
            message = await self.save_message_private(Message(
                username=username, 
                msg=msg, chat=room, 
                username_receive=username_receive
            ))
            await self.pub_message(
                channel="private",
                socket_id=socket_id,
                msg=message
            )
        
        except HTTPException as e:
            await self.send(socket_id, {"code": 400, "error": e.detail})

    async def handle_specific_room(self):
        pass


    async def broadcast(self, message: Dict, exclude_socket_id: List[str] | None = None):
        for socket_id, connection_data in self.clients_connected.items():
            if not (socket_id in exclude_socket_id):
                await connection_data.websocket.send_text(json.dumps(message, ensure_ascii=False))

    async def disconnect(self, socket_id: str):
        # get_websocket_manager_singleton().remove_ws(socket_id)
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

    async def subscribe_channel(self, room):
        Thread(target=self.pubsub.sub, args=(room, self.receive_private), daemon=True).start()


websocket_manager = WebSocketManager()