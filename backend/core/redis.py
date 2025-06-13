import redis.asyncio as redis
from backend.core.config import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)