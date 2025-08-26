from backend.core.config import Telegram_API_HASH, Telegram_API_ID
import json
from redis.asyncio import Redis
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import pytz

def clean_text(raw: str) -> str:
    """
    清理地震訊息文字，移除不需要的尾巴內容
    """
    if not raw:
        return ""

    bad_keywords = [
        "地震報告圖",
        "氣象署連結",
    ]

    text = raw
    for bad in bad_keywords:
        text = text.replace(bad, "")

    return text.strip()

async def crawl_telegram(redis: Redis):
    channel_username = 'TWEarthquake'
    session_file = 'tw_earthquake_session'
    
    coutryname_value = await redis.get("country")
    if coutryname_value is None:
        return {"error": "No location data available. Please set location first using /weather endpoint."}
        
    try:
        if isinstance(coutryname_value, bytes):
            coutryname_value = coutryname_value.decode("utf-8")
        coutryname_data = json.loads(coutryname_value)
        coutryname = coutryname_data["CountyName"]
    except (json.JSONDecodeError, KeyError) as e:
        return {"error": f"Invalid location data format: {str(e)}"}

    keywords = [coutryname]
    client = TelegramClient(session_file, Telegram_API_ID, Telegram_API_HASH)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            return {"error": "尚未授權，請先在本機登入產生 tw_earthquake_session.session"}

        print(f"📡 連接頻道 @{channel_username}...")
        channel = await client.get_entity(channel_username)

        async for message in client.iter_messages(channel, limit=50):
            if message.message and any(keyword in message.message for keyword in keywords):
                # 轉換時區
                taipei_tz = pytz.timezone("Asia/Taipei")
                local_dt = message.date.astimezone(taipei_tz)

                # 取得 sender_name
                sender = await message.get_sender()
                if sender:
                    sender_name = getattr(sender, "username", None) or getattr(sender, "first_name", "Unknown")
                else:
                    sender_name = "頻道公告"

                first_msg = {
                    "id": message.id,
                    "utc_date": message.date.isoformat(),  # UTC ISO 格式
                    "date": local_dt.strftime("%Y-%m-%d %H:%M:%S"),  # 台北時間字串
                    "sender_id": str(message.sender_id) if message.sender_id else "N/A",
                    "sender_name": sender_name,
                    "text": clean_text(message.message)
                }

                # ✅ 找到第一筆直接回傳
                return {"success": True, "data": first_msg}

        return {"success": True, "data": None}  # 沒有符合條件的
    except SessionPasswordNeededError:
        return {"error": "帳號啟用了雙重驗證，請處理兩階段登入"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        await client.disconnect()


