from app.pubsub_service import RedisClient
from app.schemas import UserSchema, Chat
from redis.client import PubSub
from typing import Callable
from bson import ObjectId
from app.db import db
import asyncio
import logging

logger = logging.getLogger(__name__)

class CreateRoomService:
    def __init__(self):
        self.redis_client:RedisClient = RedisClient()
        self.task: asyncio.Task = None
        self.pubsub: PubSub = None
        self.room: str = None

    async def create_room(self, id_user, chat: Chat, callback: Callable | None = None, ):      
        if await db.chats.find_one({"name": chat.name}):
            raise Exception("chat já existe")
        
        await db.chats.insert_one(chat.model_dump(by_alias=True))

        if callback:
            await self.connect_room(
                id_user, 
                chat.name, 
                callback, 
                password=chat.password
            )
        
    async def connect_room(
            self, id_user: str, room: str, 
            callback: Callable, password: str=None
        ):
        if self.task:
            await self.disconnect(id_user)

        chat_data = await db.chats.find_one({"name": room})
        
        if not chat_data:
            raise Exception("Chat não existe")

        chat = Chat(**chat_data)
        if chat.limit == len(chat.users):
            raise Exception("Chat esta lotado")
        if chat.password and chat.password != password:
            raise Exception("Senha inválida")
        
        chat.users.append(id_user)

        self.task, self.pubsub = await self.redis_client.sub(room, callback)

        await db.chats.update_one(
            {"_id": ObjectId(chat.id)},
            {"$set": chat.model_dump(exclude="id", by_alias=True)}
        )

        await db.users.update_one(
            {"_id": ObjectId(id_user)}, 
            {"$set": {"in_chat": True}}
        )
        self.room = room
        logger.info(f"login feito na sala '{room}'")

    async def disconnect(self, id_user: str):
        if self.task:
            await self.pubsub.unsubscribe()
            self.task.cancel()
        self.task = None
        self.pubsub = None

        chat_data = await db.chats.find_one({"name": self.room, })
        chat = Chat(**chat_data)

        chat.users.remove(id_user)

        await db.chats.update_one(
            {"_id": ObjectId(chat.id)},
            {"$set": chat.model_dump(exclude="id", by_alias=True)}
        )

        await db.users.update_one(
            {"_id": ObjectId(id_user)}, 
            {"$set": {"in_chat": False}}
        )