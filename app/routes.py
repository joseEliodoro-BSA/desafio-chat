from fastapi import APIRouter, HTTPException
from app.schemas import UserSchema, Message
from app.db import user_collection, chats_collection
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/create-user")
async def create(user: UserSchema):
    if await user_collection.find_one({"username": user.username}):
        raise HTTPException(404, "usuário ja cadastrado")
    new_user = user.model_dump(exclude=["_id"], exclude_none=True)
    result = await user_collection.insert_one(new_user)

    new_user["_id"] = f"{result.inserted_id}"

    return new_user


@router.delete("/delete-all-message")
async def delete_all_message():
    logger.info("Excluindo todas as mensagem no banco")
    await chats_collection.delete_many({})
    return True


@router.delete("/delete-all-users")
async def delete_all_users():
    logger.info("Excluindo todos os usuários")
    await user_collection.delete_many({})
    return True


@router.get("/find-messages", response_model=List[Message])
async def list_message():
    return await chats_collection.find().to_list(100)


@router.get("/find-users", response_model=List[UserSchema])
async def list_users():
    return await user_collection.find().to_list(100)
