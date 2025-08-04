from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.schemas.robot import register_ws_client,unregister_ws_client
import asyncio

robot_router = APIRouter()


@robot_router.websocket("/ws/opcua/{robot_id}/{typ}")
async def robot_module_ws(websocket: WebSocket, robot_id: str, typ: str):
    topic = f"robot.{robot_id}.{typ}"  # 範例: robot.robot_1.nicla
    await websocket.accept()
    register_ws_client(topic, websocket)
    print(f"✅ WebSocket connected: {topic}")
    try:
        while True:
            await asyncio.sleep(1000)  # 或維持心跳、無需 loop 發送（由 broadcast 推資料）
    except WebSocketDisconnect:
        unregister_ws_client(topic, websocket)
        print(f"❌ Disconnected: {topic}")





