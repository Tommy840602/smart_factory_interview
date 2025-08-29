from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.schemas.ws_manager import ws_clients

robot_router = APIRouter(tags=["Robot"])

@robot_router.websocket("/ws/robot/{robot}/{typ}")
async def websocket_endpoint(websocket: WebSocket, robot: str, typ: str):
    """
    每個 robot/type 一個 WebSocket channel
    e.g. /ws/robot/robot_1/left_arm
    """
    await websocket.accept()
    path = f"{robot}/{typ}"
    ws_clients.setdefault(path, []).append(websocket)

    print(f"[WebSocket] Client connected {path} -> {len(ws_clients[path])} clients")

    try:
        while True:
            # 前端可能會發 ping/keep-alive 訊息過來
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_clients[path].remove(websocket)
        print(f"[WebSocket] Client disconnected {path} -> {len(ws_clients[path])} clients")

