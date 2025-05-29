"""
WebSocket connection manager for broadcasting progress updates.
"""
from typing import List
from fastapi import WebSocket

class ConnectionManager:
    """Manages active WebSocket connections and broadcasts messages."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Send a JSON message to all active connections."""
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                # Remove closed connections
                self.disconnect(connection)

# Singleton manager instance
manager = ConnectionManager()