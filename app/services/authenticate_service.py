from app.db import db
from app.websocket_manager import WebsocketManager
from app.schemas import UserSchema
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


class AuthenticateService:
    def __init__(self):
        self.websocket_manager: WebsocketManager = WebsocketManager()

    async def is_auth(self, username):
        
        user_data = await db.users.find_one({"username": username})
        if not user_data: 
            raise Exception(f"usuário '{username}' não foi encontrado")
        
        user = UserSchema(**user_data)

        if(user.online):
            logger.error("usuário já possui uma seção ativa")
            raise Exception("usuário já conectado")
         
        await db.users.update_one({"_id": ObjectId(user.id)}, {"$set": {"online": True}})
        return user
    
    async def disconnect(self, username):
        
        user_data = await db.users.find_one({"username": username})
        if not user_data: 
            return False
        
        user = UserSchema(**user_data)
        user.online = False
        user.in_chat = False
        
        await db.users.update_one(
            {"_id": ObjectId(user.id)}, 
            {"$set": user.model_dump(exclude="id")}
        )
        
        return user






