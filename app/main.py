from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from uuid import uuid4

from app.db import user_collection, chats_collection
from app.websocket_manager import websocket_manager
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


@app.websocket("/ws/{room}")
async def connect(websocket: WebSocket, room:str | None = None):
    socket_id = str(uuid4())
    username = websocket.query_params.get('username')
    room = websocket.path_params.get("room")
    
    try:
        await websocket_manager.connect(websocket, socket_id, username)
        #wait_command()
        #validate_command()
        await websocket_manager.wait_command(websocket, socket_id, username)
        
    except WebSocketDisconnect:
        await websocket_manager.disconnect(socket_id)
        #check_room_finisher()
    
    except Exception as e:
        return HTTPException(400, e)
    
rooms = {}
