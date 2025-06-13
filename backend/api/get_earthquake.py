from fastapi import APIRouter,Depends
from redis.asyncio import Redis
from backend.api.deps import get_redis
from backend.services.crawl_telegram import crawl_telegram

earthquake_router = APIRouter(tags=["Weather"])

@earthquake_router.get("/get_earthquake")
async def get_earthquake_data(redis: Redis = Depends(get_redis)):
    result = await crawl_telegram(redis)
    return result

