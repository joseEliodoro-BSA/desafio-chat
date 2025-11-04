from fastapi import APIRouter, HTTPException, WebSocket
from app.schemas import UserSchema, MessageGlobal, MessageCollection
from app.db import user_collection, chats_collection
from datetime import datetime
from app.websocket_manager import websocket_manager
router = APIRouter()

def now():
    return datetime.now().timestamp()#.strftime("%d/%m/%Y %H:%M:%S")

@router.post("/create-user")
async def create(user: UserSchema):
    if await user_collection.find_one({"username": user.username}):
        raise HTTPException(404, "usuário ja cadastrado")
    new_user = user.model_dump(exclude=["id"])
    result = await user_collection.insert_one(new_user)

    new_user["_id"] = f"{result.inserted_id}"

    return new_user

@router.post("/geral-chat")
async def geral_chat(msgDto: MessageGlobal):

    if not await user_collection.find_one({"username": msgDto.username}):
        raise HTTPException(404, "usuário não encontrado")
    
    new_msg = {"date": now(), **msgDto.model_dump(exclude=["id", "date"])}
    result = await chats_collection.insert_one(new_msg)
    new_msg["_id"] = f"{result.inserted_id}"

    return new_msg


@router.get("/find-messages")
async def list_message():
    return MessageCollection(messages=await chats_collection.find().to_list(100))

from uuid import uuid4

@router.websocket("/ws")
async def connect(websocket: WebSocket):
    id = str(uuid4)
    await websocket_manager.connect(websocket, id)
    try:
        await websocket_manager.send(id, {"hello": "world"})
    except:
        await websocket_manager.disconnect(id)