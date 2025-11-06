from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from uuid import uuid4

from app.websocket_repository import WebSocketService
from app.routes import router

from contextlib import asynccontextmanager
from app.singleton import get_websocket_manager_singleton
import asyncio

ROOMS = {}
lock = asyncio.Lock()

# função executada no inicio do ciclo de vida da aplicação e no final
@asynccontextmanager
async def lifespan(app):
    yield 
    for room in ROOMS.values():
        room.cancel()
    
    await get_websocket_manager_singleton.disconnect_all()


app = FastAPI(lifespan=lifespan)
app.include_router(router)


@app.websocket("/ws/{room}")
async def connect(websocket: WebSocket):
    
    websocket_service = WebSocketService(
        socket_id = str(uuid4()),
        websocket=websocket
    )
    # if room not in ["geral", "private"]:
    #     async with lock:
    #         if not room in ROOMS:
    #             ROOMS[room] = asyncio.create_task(websocket_service.subscribe_channel(room))
    
    try:
        await websocket_service.connect(websocket)
        
        #validate_command()
        await websocket_service.wait_command(websocket)
        
    except WebSocketDisconnect:
        await websocket_service.disconnect()
        # async with lock:
        #     await websocket_service.check_room_finisher(ROOMS)
    except Exception as e:
        return HTTPException(400, e)
    

