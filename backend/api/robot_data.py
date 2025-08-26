from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.schemas.robot import register_ws_client,unregister_ws_client
import asyncio

robot_router = APIRouter(tags=["Robot"])

ws_clients: dict[str, list[WebSocket]] = {}

@robot_router.websocket("/ws/robot/{robot}/{typ}")
async def websocket_endpoint(websocket: WebSocket, robot: str, typ: str):
    """每個 robot/type 一個 WebSocket channel"""
    await websocket.accept()
    path = f"{robot}/{typ}"
    ws_clients.setdefault(path, []).append(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        ws_clients[path].remove(websocket)
