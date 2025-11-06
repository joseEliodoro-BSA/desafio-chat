from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from uuid import uuid4

from app.db import user_collection, chats_collection
from app.websocket_repository import websocket_manager
from app.schemas import Message
from app.routes import router

from contextlib import asynccontextmanager
from datetime import datetime
import json
import asyncio

broadcast_task = None

# função executada no inicio do ciclo de vida da aplicação e no final
@asynccontextmanager
async def lifespan(app):
  
  global broadcast_task

  # antes do app iniciar
  broadcast_task = asyncio.create_task(websocket_manager.subscribes_channel())

  yield 
  broadcast_task.cancel()
  for room in rooms.values():
    room.cancel()
    
  await websocket_manager.disconnect_all()


app = FastAPI(lifespan=lifespan)
app.include_router(router)


def now():
    return datetime.now().timestamp()

async def save_message_geral(msgDto: Message):

    if not await user_collection.find_one({"username": msgDto.username}):
        raise HTTPException(404, "usuário não encontrado")
    
    new_msg = {"date": now(), **msgDto.model_dump(exclude=["_id", "date", "username_receive"], exclude_none=True)}
    result = await chats_collection.insert_one(new_msg)
    new_msg["_id"] = f"{result.inserted_id}"
    
    return new_msg

async def save_message_private(msgDto: Message):

    if not await user_collection.find_one({"username": msgDto.username}):
        raise HTTPException(404, "usuário não encontrado")
    if not await user_collection.find_one({"username": msgDto.username_receive}):
        raise HTTPException(404, "destinatário não encontrado")
    
    new_msg = {"date": now(), **msgDto.model_dump(exclude=["_id", "date"], exclude_none=True)}
    result = await chats_collection.insert_one(new_msg)
    new_msg["_id"] = f"{result.inserted_id}"
    
    return new_msg

@app.websocket("/ws")
async def connect(websocket: WebSocket):
    socket_id = str(uuid4())
    username = websocket.query_params.get('username')
    try:
        await websocket_manager.connect(websocket, socket_id, username)
        await websocket_manager.send(socket_id, {"code": 200, "details": "conexão iniciada com sucesso"})
    
        #connect + send
        #wait_command()
        #validate_command()


        while True:
            data: str = await websocket.receive_text()
            data_json: dict = json.loads(data)

            if data_json["command"] == "send_message":
                if not data_json.get('chat') or not data_json.get("msg"):
                    await websocket_manager.send(socket_id, {"code": 400, "error": "requisição inválida"})
                    continue

                chat = data_json['chat']
                msg = data_json["msg"]

                #check_room_type(room_type)
                #handle_general_room()
                #handle_private_room()
                #handle_specific_room()
                
                if(chat == "geral"):
                    try:
                        message = await save_message_geral(Message(username=username, msg=msg, chat=chat))
                        await websocket_manager.pub_message(
                            channel="geral", 
                            socket_id=socket_id,
                            msg=message
                        )
                    except HTTPException as e:
                        await websocket_manager.send(socket_id, {"code": 400, "error": e.detail})                       
                elif(chat == "private"):
                    if not data_json.get("username_receive"):
                        await websocket_manager.send(socket_id, {"code": 400, "error": "requisição inválida"}) 
                        continue
                    try:
                        message = await save_message_private(Message(
                            username=username, 
                            msg=msg, chat=chat, 
                            username_receive=data_json["username_receive"]
                        ))
                        await websocket_manager.pub_message(
                            channel="private",
                            socket_id=socket_id,
                            msg=message
                        )
                    
                    except HTTPException as e:
                        await websocket_manager.send(socket_id, {"code": 400, "error": e.detail})
            
            elif data_json.get("command") == "test":
                await websocket_manager.send(socket_id, {"code": 200, "detail": "hello word"})
            else:
                await websocket_manager.send(socket_id, {"code": 400, "error": "inválid command"})
    except WebSocketDisconnect:
        await websocket_manager.disconnect(socket_id)
        #check_room_finisher()
    
    except Exception as e:
        return HTTPException(400, e)
    
rooms = {}

@app.websocket("/ws/{room}")
async def chat_rooms(websocket: WebSocket, room: str):
    
    global rooms

    socket_id = str(uuid4())
    username = websocket.query_params.get('username')
    try:
        await websocket_manager.connect(websocket, socket_id, username)
        await websocket_manager.send(socket_id, {"code": 200, "details": "conexão iniciada com sucesso"})

        if(room and not(room in rooms)):
            rooms[room] = asyncio.create_task(websocket_manager.subscribe_channel(room))

        while True:
            data: str = await websocket.receive_text()
            data_json: dict = json.loads(data)

            if data_json["command"] == "send_message":
                if not data_json.get('chat') or not data_json.get("msg"):
                    await websocket_manager.send(socket_id, {"code": 400, "error": "requisição inválida"})
                    continue

                msg = data_json["msg"]
                try:
                    message = await save_message_geral(Message(username=username, msg=msg, chat=room))
                    await websocket_manager.pub_message(
                        channel=room, 
                        socket_id=socket_id,
                        msg=message
                    )
            
                except HTTPException as e:
                    await websocket_manager.send(socket_id, {"code": 400, "error": e.detail})

    except WebSocketDisconnect:
        await websocket_manager.disconnect(socket_id)
    
    except Exception as e:
        return HTTPException(400, e)