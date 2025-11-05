from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from app.schemas import UserSchema, MessageGlobal, MessageCollection, UserCollection
from app.db import user_collection, chats_collection
from datetime import datetime
from app.websocket_manager import websocket_manager
from uuid import uuid4
import json

router = APIRouter()

def now():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")#.timestamp()#

@router.post("/create-user")
async def create(user: UserSchema):
    if await user_collection.find_one({"username": user.username}):
        raise HTTPException(404, "usuário ja cadastrado")
    new_user = user.model_dump(exclude=["_id"], exclude_none=True)
    result = await user_collection.insert_one(new_user)

    new_user["_id"] = f"{result.inserted_id}"

    return new_user

async def send_message_chat_geral(msgDto: MessageGlobal):

    if not await user_collection.find_one({"username": msgDto.username}):
        raise HTTPException(404, "usuário não encontrado")
    
    new_msg = {"date": now(), **msgDto.model_dump(exclude=["_id", "date", "username_receive"], exclude_none=True)}
    result = await chats_collection.insert_one(new_msg)
    new_msg["_id"] = f"{result.inserted_id}"
    
    return new_msg

async def send_message_chat_private(msgDto: MessageGlobal):

    if not await user_collection.find_one({"username": msgDto.username}):
        raise HTTPException(404, "usuário não encontrado")
    if not await user_collection.find_one({"username": msgDto.username_receive}):
        raise HTTPException(404, "destinatário não encontrado")
    
    new_msg = {"date": now(), **msgDto.model_dump(exclude=["_id", "date"], exclude_none=True)}
    result = await chats_collection.insert_one(new_msg)
    new_msg["_id"] = f"{result.inserted_id}"
    
    return new_msg

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

@router.websocket("/ws")
async def connect(websocket: WebSocket):
    socket_id = str(uuid4())
    username = websocket.query_params.get('username')
    try:
        await websocket_manager.connect(websocket, socket_id)
        await websocket_manager.send(socket_id, {"hello": "world"})
    
        while True:
            data: str = await websocket.receive_text()
            data_json: dict = json.loads(data)

            if not data_json.get('chat') or not data_json.get("msg"):
                await websocket_manager.send(socket_id, {"code": 400, "error": "requisição inválida"})
            
            chat = data_json['chat']
            msg = data_json["msg"]

            if(chat == "geral"):
                try:
                    await send_message_chat_geral(MessageGlobal(username=username, msg=msg, chat=chat))
                    await websocket_manager.send(socket_id, {"code": 200, "details": "mensagem enviada com sucesso"})
                except HTTPException as e:
                    await websocket_manager.send(socket_id, {"code": 400, "error": e.detail})
                    
            elif(chat == "private"):
                if not data_json.get("username_receive"):
                    await websocket_manager.send(socket_id, {"code": 400, "error": "requisição inválida"})
                try:
                    await send_message_chat_private(MessageGlobal(username=username, msg=msg, chat=chat, username_receive=data_json["username_receive"]))
                    await websocket_manager.send(socket_id, {"code": 200, "details": "mensagem enviada com sucesso"})
                except HTTPException as e:
                    await websocket_manager.send(socket_id, {"code": 400, "error": e.detail})

            # await websocket_manager.send(socket_id, data_json)

    except WebSocketDisconnect:
        await websocket_manager.disconnect(socket_id)
    
    except Exception as e:
        return HTTPException(400, e)