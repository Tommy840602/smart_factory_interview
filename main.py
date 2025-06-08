from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from backend.api.power_supply import power_router
from backend.api.ups_info import ups_router
from backend.api.get_weather import weather_router
from backend.api.k_map import kmap_router
from backend.api.get_earthquake import earthquake_router
from contextlib import asynccontextmanager
from backend.utils.ups_simulation import start_background_ups_simulator

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_background_ups_simulator()
    yield

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

if __name__=="__main__":
    uvicorn.run("main:app",reload=True)