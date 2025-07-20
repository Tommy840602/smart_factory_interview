from fastapi import WebSocket,APIRouter,WebSocketDisconnect
from backend.core.discover_nodes import discover_opcua_nodes
from backend.schemas.opcua_streamer import OPCUAStreamer
import asyncio

robot_router = APIRouter(tags=["Robot"])

@robot_router.websocket("/ws/opcua")
async def websocket_robot_data(websocket: WebSocket, robot_id: str):
    await websocket.accept()
    streamer_dict = websocket.app.state.opcua_streamer_dict

    if robot_id not in streamer_dict:
        endpoint = "opc.tcp://localhost:4840/opcua/server/"
        nodes = await discover_opcua_nodes(endpoint, robot_id)
        streamer = OPCUAStreamer(endpoint=endpoint, node_ids=nodes)
        streamer_dict[robot_id] = streamer
    else:
        streamer = streamer_dict[robot_id]

    try:
        while True:
            data = await streamer.read_all()
            await websocket.send_json(data)
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        print(f"❌ WebSocket disconnected: {robot_id}")
