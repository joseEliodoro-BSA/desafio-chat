from fastapi import WebSocket, HTTPException

from typing import Dict, List
from threading import Thread
from datetime import datetime
import asyncio
import json


from app.pubsub_service import PubSub
from app.db import user_collection, chats_collection
from app.schemas import Message
from app.websocket_manager import WebsocketManager


class WebSocketService:
    
    def __init__(self, websocket: WebSocket, socket_id: str,):
        self.pubsub = PubSub()
        self.websocket_manager: WebsocketManager = WebsocketManager()
        self.websocket_id = socket_id 
        self.username = websocket.query_params.get("username")
        self.room = websocket.path_params.get("room")
    
        self.sub_private_room = asyncio.create_task(self.subscribe_channel("private"))
        self.sub_geral_room = asyncio.create_task(self.subscribe_channel("geral"))
        self.sub_room = asyncio.create_task(self.subscribe_channel())

    async def connect(self, websocket):

        await self.websocket_manager.connect(
            websocket=websocket, 
            id=self.websocket_id,
            username=self.username
        )

        if (not await user_collection.find_one({"username": self.username})):
            await self.websocket_manager.send(self.websocket_id, {"error": f"usuário '{self.username}' não foi encontrado"})
            await self.websocket_manager.disconnect(self.websocket_id)

        await self.websocket_manager.send(self.websocket_id, {"code": 200, "details": "conexão iniciada com sucesso"})

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

    async def wait_command(self, websocket: WebSocket):
    
        while True:
            data: str = await websocket.receive_text()
            data_json: dict = json.loads(data)
            
            if data_json["command"] == "send_message":

                await self.check_room_type(
                    data=data_json
                    )
            # adicionar outros comandos
            elif data_json.get("command") == "find":
                await self.websocket_manager.send(
                    self.websocket_id, 
                    {"code": 200, "detail": "hello word"}
                )
            else:
                await self.websocket_manager.send(
                    self.websocket_id, 
                    {"code": 400, "error": "inválid command"}
                )

    async def check_room_type(self, data: Dict):
        msg = data["msg"]           
        message = None
        if(self.room == "private"):
            message = await self.handle_private_room(msg, data)                    
        else:
            message = await self.handle_specific_room(msg)
        
        await self.pub_message(
            msg=message
        )

    async def handle_private_room(self, msg: str, data: Dict):
        username_receive = data["username_receive"]
        
        if not username_receive:
            await self.websocket_manager.send(self.websocket_id, {"code": 400, "error": "requisição inválida"}) 
            return False
        try:
            return await self.save_message_private(Message(
                username=self.username, 
                msg=msg, chat=self.room, 
                username_receive=username_receive
            ))
        
        except HTTPException as e:
            await self.websocket_manager.send(self.websocket_id, {"code": 400, "error": e.detail})

    async def handle_specific_room(self, msg):
        try:
            return await self.save_message_geral(Message(
                username=self.username, 
                msg=msg, chat=self.room,
            ))
        
        except HTTPException as e:
            await self.websocket_manager.send(self.websocket_id, {"code": 400, "error": e.detail})
            
    async def disconnect(self):
        await self.websocket_manager.disconnect(self.websocket_id)
        self.sub_room.cancel()

    async def receive(self, msg: Dict):
        data = json.loads(msg["data"])
        send_socket_id = data["socket_id"]
        del data["socket_id"]

        if msg["channel"] == "private":
            
            username_receive = data["username_receive"]
            if username_receive == self.username:
                await self.websocket_manager.send(self.websocket_id, data)
                
        else: 
            if send_socket_id != self.websocket_id:
                await self.websocket_manager.send(self.websocket_id, data)

    async def pub_message(self, msg: Dict):
        msg["socket_id"] = self.websocket_id
        self.pubsub.pub(self.room, msg)

    async def subscribe_channel(self, room: str | None = None):
        if not room:
            room = self.room
        Thread(target=self.pubsub.sub, args=(room, self.receive), daemon=True).start()
