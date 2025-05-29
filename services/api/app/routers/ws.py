from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.ws_manager import manager

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for clients to receive scan progress updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection open; clients do not need to send messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)