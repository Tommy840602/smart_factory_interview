from backend.core.config import Telegram_API_HASH,Telegram_API_ID
import json,redis
from redis.asyncio import Redis
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

async def crawl_telegram(redis: Redis):
    channel_username = 'TWEarthquakee'
    session_file = 'tw_earthquake_session'
    
    coutryname_value = await redis.get("country")
    
    if coutryname_value is None:
        return {"Error": "No location data available. Please set location first using /weather endpoint."}
        
    try:
        coutryname_data = json.loads(coutryname_value)
        coutryname = coutryname_data["CountyName"]
    except (json.JSONDecodeError, KeyError) as e:
        return {"Error": f"Invalid location data format: {str(e)}"}

    keywords = [coutryname]
    client = TelegramClient(session_file, Telegram_API_ID, Telegram_API_HASH)

    result = []

    try:
        await client.connect()
        if not await client.is_user_authorized():
            await client.start()  # 第一次需登入，會卡住

        print(f"📡 連接頻道 @{channel_username}...")
        channel = await client.get_entity(channel_username)

        async for message in client.iter_messages(channel, limit=200):
            if message.message:
                if any(keyword in message.message for keyword in keywords):
                    result.append({
                        'date': message.date.isoformat(),
                        'sender_id': str(message.sender_id),
                        'text': message.message
                    })

        # 儲存 JSON 檔（可選）
        with open("filtered_earthquake_messages.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "count": len(result),
            "data": result
        }

    except SessionPasswordNeededError:
        return {"error": "帳號啟用了雙重驗證，請處理兩階段登入"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        await client.disconnect()
