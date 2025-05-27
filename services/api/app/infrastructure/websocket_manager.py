from typing import List
from fastapi import WebSocket
import logging

from ..domain.entities import WebSocketMessage
from ..domain.services import WebSocketService

logger = logging.getLogger(__name__)


class FastAPIWebSocketService(WebSocketService):
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect_client(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect_client(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast_message(self, message: WebSocketMessage) -> None:
        message_dict = {
            "type": message.type,
            "scan_id": message.scan_id,
            "status": message.status,
            "score": message.score,
            "answers": message.answers,
            "error": message.error
        }
        
        # Remove None values
        message_dict = {k: v for k, v in message_dict.items() if v is not None}
        
        for connection in self.active_connections.copy():
            try:
                await connection.send_json(message_dict)
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket client: {e}")
                self.disconnect_client(connection)