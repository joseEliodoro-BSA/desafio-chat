from app.websocket_manager import WebsocketManager


def get_websocket_manager_singleton():
    return WebsocketManager()