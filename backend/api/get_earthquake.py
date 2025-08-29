#from fastapi import APIRouter,Depends
#from redis.asyncio import Redis
#from backend.api.deps import get_redis
#from backend.services.crawler_telegram import crawl_telegram

#earthquake_router = APIRouter(tags=["Weather"])

#@earthquake_router.get("/earthquake")
#async def get_earthquake_data(redis: Redis = Depends(get_redis)):
#    result = await crawl_telegram(redis)
 #   return result

