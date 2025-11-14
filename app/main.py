from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from uuid import uuid4

from app.services import WebSocketService
from app.routes import router

from app.logger_config import setup_logging
from contextlib import asynccontextmanager
from app.db import db

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.users.update_many({}, {"$set": {"in_chat":False, "online":False}})
    await db.chats.update_many({}, {"$set": {"users": []}})

    yield
    pass
app = FastAPI(lifespan=lifespan)
app.include_router(router)


@app.websocket("/ws")
async def connect(websocket: WebSocket):
    try:

        websocket_service = WebSocketService(
            socket_id=str(uuid4()),
            websocket=websocket
        )
        await websocket_service.connect(websocket)
        # validate_command()
        await websocket_service.wait_command(websocket)

    except WebSocketDisconnect:
        await websocket_service.disconnect()

    except Exception as e:
        return Exception(400, e)
