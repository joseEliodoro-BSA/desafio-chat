from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from uuid import uuid4

from app.services.websocket_service import WebSocketService
from app.routes import router

from app.logger_config import setup_logging

setup_logging()

app = FastAPI()
app.include_router(router)


@app.websocket("/ws/{room}")
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
