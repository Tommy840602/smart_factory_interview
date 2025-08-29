from fastapi import FastAPI,WebSocketDisconnect,WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn,subprocess,asyncio,threading
from backend.api.power_supply import power_router
from backend.api.ups_info import ups_router
from backend.api.get_weather import weather_router
from backend.api.k_map import kmap_router
from backend.api.classify_image import grpc_router
from contextlib import asynccontextmanager
from backend.utils.ups_simulation import start_background_ups_simulator
from backend.core.redis import start_redis
from backend.services.grpc_server import start_background_grpc_server
from backend.services.mqtt_server import start_background_mqtt_server
from backend.core.config import create_robot_topics
from backend.services.sparkplug_server import start_sparkplug_streams
from backend.services.db_server import start_workers
from backend.core.sparkplug_subscriber_ws import subscriber_ws
from backend.schemas.ws_manager import init_ws_hub, get_ws_hub


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_ws_hub(asyncio.get_running_loop())
    # === 前置處理：關閉 EMQX 佔用的進程並重啟 ===
    subprocess.run(["pkill", "beam.smp"], check=False)
    subprocess.run(["lsof", "-i", ":1883"], check=False)
    subprocess.run(["brew", "services", "restart", "emqx"], check=True)

    # === 其他服務初始化 ===
    create_robot_topics()  
    start_redis()
    start_background_ups_simulator()
    start_background_grpc_server()
    asyncio.create_task(start_background_mqtt_server())

    # === 整合 Sparkplug 與 DB Server ===
    asyncio.create_task(start_sparkplug_streams())
    # 啟動 Kafka Consumer workers
    start_workers()
    # === Sparkplug Subscriber 啟動 ===
    subscriber_ws()

    # 給一點時間啟動
    await asyncio.sleep(1)
    try:
        yield
    finally:
        pass


app=FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
    )


# ===== WebSocket Endpoints =====
# 建議用這個（符合你之前連的樣式）
@app.websocket("/ws/robot/{robot}/{typ}")
async def websocket_robot_prefixed(websocket: WebSocket, robot: str, typ: str):
    await _ws_handler(websocket, f"{robot}/{typ}")

# 也支援簡短版：/ws/{robot}/{typ}
@app.websocket("/ws/{robot}/{typ}")
async def websocket_robot_short(websocket: WebSocket, robot: str, typ: str):
    await _ws_handler(websocket, f"{robot}/{typ}")

# 你之前日誌有 "Root client connected"；保留一個 root 監看端點（不訂閱特定 path）
@app.websocket("/ws/robot/")
async def websocket_root(websocket: WebSocket):
    await websocket.accept()
    print("[WebSocket] Root client connected")
    try:
        while True:
            # 若前端不會送資料，就保活即可
            await asyncio.sleep(60)
    except WebSocketDisconnect:
        print("[WebSocket] Root client disconnected")

# 共用處理邏輯
async def _ws_handler(websocket: WebSocket, path: str):
    hub = get_ws_hub()
    await websocket.accept()
    await hub.attach(path, websocket)
    try:
        # 若前端會送 ping，可改成 receive_text()
        while True:
            await asyncio.sleep(60)
    except WebSocketDisconnect:
        pass
    finally:
        await hub.detach(path, websocket)


app.mount("/static",StaticFiles(directory="static"),name="static")

app.include_router(ups_router, prefix="/api")
app.include_router(power_router, prefix="/api")
app.include_router(weather_router, prefix="/api")
app.include_router(kmap_router, prefix="/api")
app.include_router(grpc_router, prefix="/api")

#print("\n🚀 Registered routes:")
#pprint.pprint([
#    {
#        "path": route.path,
#        "methods": getattr(route, "methods", None),
#        "name": route.name
#    }
#    for route in app.router.routes
#])

if __name__=="__main__":
    uvicorn.run("main:app",reload=True)
