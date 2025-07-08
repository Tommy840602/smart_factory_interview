import redis.asyncio as redis
from backend.core.config import settings
import os,subprocess

def start_redis():
    redis_path = "/Users/huangyanwei/redis-7.0.14/src/redis-server"
    if not os.path.isfile(redis_path):
        raise FileNotFoundError(f"找不到 redis-server:{redis_path}")
    subprocess.run([redis_path,'--daemonize', "yes"], check=True)


redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)