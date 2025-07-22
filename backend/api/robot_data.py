# backend/api/robot_data.py
from fastapi import WebSocket, APIRouter, WebSocketDisconnect
from starlette.websockets import WebSocketState
from fastapi.encoders import jsonable_encoder
import asyncio, traceback
from backend.core.opcua_client_pool import get_or_create_client
from backend.core.discover_nodes import discover_opcua_nodes
from backend.schemas.opcua_streamer import OPCUAStreamer

robot_router = APIRouter(tags=["Robot"])
ENDPOINT = "opc.tcp://localhost:4840/opcua/server/"

@robot_router.websocket("/ws/opcua/{robot_id}")
async def websocket_robot_data(websocket: WebSocket, robot_id: str):
    await websocket.accept()
    rid = robot_id.lower()  # 例如 robot_1
    print(f"🔗 WebSocket 已連線：{rid}")

    if not hasattr(websocket.app.state, "opcua_streamer_dict"):
        websocket.app.state.opcua_streamer_dict = {}
    cache = websocket.app.state.opcua_streamer_dict

    try:
        if rid not in cache:
            try:
                client = await get_or_create_client(ENDPOINT)
                print(f"✅ 已連接到 OPC UA 伺服器：{rid}，位址 {ENDPOINT}")
            except Exception as e:
                error_msg = f"無法連接到 OPC UA 伺服器（{rid}:{str(e)}"
                print(f"❌ {error_msg}")
                await websocket.send_json({"error": error_msg})
                return

            flat_map, ns_idx, _ = await discover_opcua_nodes(client=client, robot=rid)
            if not flat_map:
                error_msg = f"未找到 {rid} 下的變數"
                print(f"⚠️ {error_msg}")
                await websocket.send_json({"error": error_msg})
                return
            node_ids = list(flat_map.values())
            cache[rid] = OPCUAStreamer(client, node_ids)
            print(f"✅ 已初始化 OPCUAStreamer：{rid}，節點：{node_ids}")

        streamer = cache[rid]

        while True:
            try:
                data = await streamer.read_all()
                await websocket.send_json(jsonable_encoder(data))
                await asyncio.sleep(0.5)
            except Exception as e:
                error_msg = f"讀取 {rid} 資料時發生錯誤：{str(e)}"
                print(f"❌ {error_msg}")
                await websocket.send_json({"error": error_msg})
                break  # 發生讀取錯誤時退出迴圈，防止無限重試

    except WebSocketDisconnect:
        print(f"🔌 WebSocket 已斷開：{rid}")
    except Exception as e:
        error_msg = f"WebSocket 錯誤（{rid}）：{str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        await websocket.send_json({"error": error_msg})
    finally:
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close()
            print(f"🔌 WebSocket 已關閉：{rid}")


