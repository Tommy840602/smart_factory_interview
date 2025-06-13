import pydantic 

Telegram_API_ID=22468436
Telegram_API_HASH="cc037d52e7b58664b9140e82f8aa73b5"

class Settings():
    REDIS_URL: str = "redis://localhost:6379"

    class Config:
        env_file = ".env"

settings = Settings()


