from app.pubsub_service import RedisClient
from app.schemas import UserSchema
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

    async def connect_room(self, id_user: str, room: str, callback: callable):
        if self.task:
            await self.disconnect()

        self.task, self.pubsub = await self.redis_client.sub(room, callback)
        await db.users.update_one({"_id": ObjectId(id_user)}, {"$set": {"in_chat": True}})
        logger.info(f"login feito na sala '{room}'")

    async def disconnect(self, id_user: str):
        if self.task:
            await self.pubsub.unsubscribe()
            self.task.cancel()
        self.task = None
        self.pubsub = None

        await db.users.update_one({"_id": ObjectId(id_user)}, {"$set": {"in_chat": False}})