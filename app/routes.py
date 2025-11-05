from fastapi import APIRouter, HTTPException
from app.schemas import UserSchema, MessageCollection, UserCollection
from app.db import user_collection, chats_collection

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
    await chats_collection.delete_many({})
    return True

@router.get("/find-messages")
async def list_message():
    return MessageCollection(messages=await chats_collection.find().to_list(100))

@router.get("/find-users")
async def list_message():
    return UserCollection(messages=await user_collection.find().to_list(100))



