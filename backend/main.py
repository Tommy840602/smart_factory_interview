from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn,subprocess,asyncio
from backend.api.power_supply import power_router
from backend.api.ups_info import ups_router
from backend.api.get_weather import weather_router
from backend.api.k_map import kmap_router
from backend.api.get_earthquake import earthquake_router
from backend.api.classify_image import grpc_router
from backend.api.robot_data import robot_router
from contextlib import asynccontextmanager
from backend.utils.ups_simulation import start_background_ups_simulator
from backend.core.redis import start_redis
from backend.services.grpc_server import start_background_grpc_server
from backend.services.mqtt_server import start_background_mqtt_server
from backend.services.db_server import start_background_db_server
from backend.core.config import create_robot_topics

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(start_background_db_server())
    subprocess.run(["pkill", "beam.smp"], check=False)
    subprocess.run(["lsof", "-i", ":1883"], check=False)
    subprocess.run(["brew", "services", "restart", "emqx"], check=True)
    create_robot_topics()  
    start_redis()
    start_background_ups_simulator()
    start_background_grpc_server()
    asyncio.create_task(start_background_mqtt_server())
    await asyncio.sleep(1)
    try:
        yield
    finally:
        pass


app=FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
    )

app.mount("/static",StaticFiles(directory="static"),name="static")

app.include_router(ups_router, prefix="/api")
app.include_router(power_router, prefix="/api")
app.include_router(weather_router, prefix="/api")
app.include_router(kmap_router, prefix="/api")
app.include_router(earthquake_router, prefix="/api")
app.include_router(grpc_router, prefix="/api")
app.include_router(robot_router)


if __name__=="__main__":
    uvicorn.run("main:app",reload=True)
