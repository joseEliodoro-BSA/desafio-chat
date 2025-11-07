from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from uuid import uuid4

from app.websocket_repository import WebSocketService
from app.routes import router

from contextlib import asynccontextmanager
import asyncio

ROOMS = {}
lock = asyncio.Lock()

# função executada no inicio do ciclo de vida da aplicação e no final

app = FastAPI()
app.include_router(router)

@app.websocket("/ws/{room}")
async def connect(websocket: WebSocket):
    
   
    # if room not in ["geral", "private"]:
    #     async with lock:
    #         if not room in ROOMS:
    #             ROOMS[room] = asyncio.create_task(websocket_service.subscribe_channel(room))
    
    try:

        websocket_service = WebSocketService(
            socket_id = str(uuid4()),
            websocket=websocket
        )

        await websocket_service.connect(websocket)
        
        #validate_command()
        await websocket_service.wait_command(websocket)
        
    except WebSocketDisconnect:
        await websocket_service.disconnect()
        # async with lock:
        #     await websocket_service.check_room_finisher(ROOMS)
    except Exception as e:
        return HTTPException(400, e)
    

