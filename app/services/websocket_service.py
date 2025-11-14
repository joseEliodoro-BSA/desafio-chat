from fastapi import WebSocket, HTTPException

from typing import Dict
from datetime import datetime
import logging 
import json


from app.pubsub_service import RedisClient
from app.db import db
from app.schemas import Chat, Message
from app.websocket_manager import WebsocketManager
from app.services.create_room_service import CreateRoomService
from app.services.authenticate_service import AuthenticateService


logger = logging.getLogger(__name__)


class WebSocketService:
    
    def __init__(self, websocket: WebSocket, socket_id: str,):
        self.authenticate = AuthenticateService()
        self.redis_client:RedisClient = RedisClient()
        self.websocket_manager: WebsocketManager = WebsocketManager()
        self.websocket_id = socket_id 
        self.username = websocket.query_params.get("username")
        self.room = None
        self.user_id = None
        self.create_room_service = CreateRoomService()

    async def connect(self, websocket):
        try:

            await self.websocket_manager.connect(
                websocket=websocket, 
                id=self.websocket_id,
                username=self.username
            )
            logger.info("authenticando usuário")
            user = await self.authenticate.is_auth(self.username)
            self.user_id = user.id
            await self.websocket_manager.send(
                self.websocket_id, 
                {"code": 200, "details": "conexão iniciada com sucesso"}
            )
        except Exception as e:
            logger.error(e)
            await self.websocket_manager.send(self.websocket_id, {"error": str(e)})
            await self.websocket_manager.disconnect(self.websocket_id, True)
            
    async def save_message_geral(self, msgDto: Message):
        new_msg = {"date": datetime.now().timestamp(), **msgDto.model_dump(exclude=["_id", "date", "username_receive"], exclude_none=True)}
        
        result = await db.messages.insert_one(new_msg)
        new_msg["_id"] = f"{result.inserted_id}"
        
        return new_msg

    async def save_message_private(self, msgDto: Message):

        if not await db.users.find_one({"username": msgDto.username_receive}):
            raise HTTPException(404, "destinatário não encontrado")
        
        new_msg = {"date": datetime.now().timestamp(), **msgDto.model_dump(exclude=["_id", "date"], exclude_none=True)}
        result = await db.messages.insert_one(new_msg)
        new_msg["_id"] = f"{result.inserted_id}"
        
        return new_msg

    async def wait_command(self, websocket: WebSocket):
    
        while True:
            data: str = await websocket.receive_text() 
            print(data)
            await self.validate_command(data_json=json.loads(data))

    async def validate_command(self, data_json: Dict[str, object]):
        command = data_json["command"]
        if command == "send_message":
            if not self.room:
                await self.websocket_manager.send(
                    self.websocket_id, {"error": "se conecte a uma sala antes de enviar uma mensagem"}
                )
                return
            await self.check_room_type(
                data=data_json
                )
        elif command == "connect_room":
            try:
                self.room = data_json.get("room")
                if not self.room:
                    await self.websocket_manager.send(
                        self.websocket_id, 
                        {"error": "parametro 'room' não encontrado"}
                    )
                    return
                await self.create_room_service.connect_room(
                    self.user_id, 
                    self.room, 
                    self.receive, 
                    password=data_json.get("password")
                    )
                logger.info(self.room)
            except Exception as e:
                logger.error(e)
                await self.websocket_manager.send(self.websocket_id, {"error": str(e)})

        elif command == "disconnect_room":
            await self.create_room_service.disconnect(self.user_id)
            self.room = None
        elif command == "create_room":
            self.room = data_json["room"]
            try:
                await self.create_room_service.create_room(
                    id_user= [self.user_id],
                    chat=Chat(
                        name= self.room,
                        password=data_json.get("password")
                    ), 
                    callback=self.receive
                )
            except Exception as e:
                logger.warning(f"chat['{self.room}'] já existe")
                await self.websocket_manager.send(self.websocket_id, {"error": str(e)})
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
        await self.authenticate.disconnect(self.username)
        if self.room:
            await self.create_room_service.disconnect(self.user_id)
        await self.websocket_manager.disconnect(self.websocket_id)

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
        await self.redis_client.pub(self.room, msg)

