import threading, asyncio
import datetime
import logging
import numpy as np
import paho.mqtt.client as mqtt
from backend.core.config import (MQTT_BROKER, MQTT_PORT, TOPIC_AC, TOPIC_DEH, TOPIC_HUM, TOPIC_TEMP)
from kafka import KafkaProducer
import json, os
from zoneinfo import ZoneInfo
from copy import deepcopy
from dotenv import load_dotenv
from backend.core.config import get_local_producer, get_cloud_producer
from google.cloud import storage
import pandas as pd
import pyarrow as pa
from pymongo import MongoClient   # ✅ 熱儲存

# ====== 環境設定 ======
load_dotenv()
KAFKA_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC  = os.getenv("KAFKA_MQTT_TOPIC", "sensor")

# ====== 初始化 MongoDB (熱) ======
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["iot_data"]
collection = db["sensor_records"]

# ====== 初始化 GCS (冷) ======
gcs = storage.Client.from_service_account_json("plasma-creek-438010-s0-bbae490f4314.json")
bucket = gcs.bucket("sensor_cold")

# ====== JSON 序列化器 ======
def json_serializer(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

# ====== Kafka 發送 ======
def send_kafka(topic, payload):
    data = json.dumps(payload, default=json_serializer).encode("utf-8")
    local = get_local_producer()
    cloud = get_cloud_producer()
    if local:
        try:
            local.send(topic, data)
        except Exception as e:
            print(f"[本地Kafka] 發送失敗：{e}")
    if cloud:
        try:
            cloud.send(topic, data)
        except Exception as e:
            print(f"[CloudKafka] 發送失敗：{e}")

# ====== OU 模擬器 ======
def simulate_ou(dt, steps, C, y0, theta, sigma):
    y = np.zeros(steps)
    y[0] = y0
    for i in range(1, steps):
        y[i] = y[i-1] + theta * (C - y[i-1]) * dt + sigma * np.sqrt(dt) * np.random.randn()
    return y

# ====== Logging ======
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ====== MQTT callbacks ======
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info(f"✅ 连接到 MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    else:
        logger.error(f"❌ MQTT 连接失败，返回码 {rc}")

def on_disconnect(client, userdata, rc):
    logger.warning(f"⚠️ MQTT 已断开（code={rc}），尝试重连…")
    try:
        client.reconnect()
    except Exception as e:
        logger.error(f"🔄 connect failed：{e}")

def on_publish(client, userdata, mid):
    logger.debug(f"已发布消息，mid={mid}")

# ====== 冷儲存 (GCS 批次) ======
buffer = []
current_hour = None
lock = threading.Lock()

PARQUET_SCHEMA = pa.schema([
    ("timestamp", pa.string()),
    ("temperature", pa.float64()),
    ("humidity", pa.float64()),
    ("ac", pa.string()),
    ("dehumidifier", pa.string())
])

def flush_buffer():
    """將 buffer 轉為 Parquet 並上傳到 GCS (冷儲存)"""
    global buffer, current_hour
    if not buffer:
        return

    ts = datetime.datetime.now(ZoneInfo("Asia/Taipei"))
    date_str = ts.strftime("%Y%m%d")
    start_hour = current_hour
    end_hour = (current_hour + 1) % 24

    file_name = f"{start_hour:02d}00_to_{end_hour:02d}00.parquet"
    blob_name = f"mqtt_records/dt={date_str}/{file_name}"
    blob = bucket.blob(blob_name)

    df = pd.DataFrame([x["payload"] for x in buffer])
    tmp_file = f"/tmp/{file_name}"
    df.to_parquet(tmp_file, engine="pyarrow", index=False, schema=PARQUET_SCHEMA)

    blob.upload_from_filename(tmp_file, content_type="application/octet-stream")

    logger.info(f"☁️ (冷儲存) 批次上傳 {len(buffer)} 筆資料 → {blob_name}")
    buffer = []

# ====== 主迴圈 ======
async def start_background_mqtt_server():
    global buffer, current_hour

    mqtt_client = mqtt.Client()
    mqtt_client.on_connect    = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_publish    = on_publish
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
    mqtt_client.loop_start()
    logger.info("🔌 MQTT start")

    dt = 1.0
    steps = 100000
    temp_seq = simulate_ou(dt, steps, C=25.0, y0=38.0, theta=1/60, sigma=0.3)
    hum_seq  = simulate_ou(dt, steps, C=50.0, y0=90.0, theta=1/80, sigma=0.5)

    idx = 0
    current_hour = datetime.datetime.now(ZoneInfo("Asia/Taipei")).hour

    try:
        while True:
            now = datetime.datetime.now(ZoneInfo("Asia/Taipei"))
            temp = float(temp_seq[idx])
            hum  = float(hum_seq[idx])
            idx = (idx + 1) % steps

            ac_on  = temp < 24.0 or temp > 26.0
            deh_on = hum  < 45.0 or hum  > 55.0

            kafka_payload = {
                "source": "mqtt",
                "payload": {
                    "timestamp": now.isoformat(),
                    "temperature": round(temp, 2),
                    "humidity": round(hum, 2),
                    "ac": "ON" if ac_on else "OFF",
                    "dehumidifier": "ON" if deh_on else "OFF"
                }
            }

            # Kafka
            send_kafka(KAFKA_TOPIC, kafka_payload)

            # MQTT
            mqtt_client.publish(TOPIC_TEMP, f"{temp:.2f}", qos=0, retain=True)
            mqtt_client.publish(TOPIC_HUM, f"{hum:.2f}", qos=0, retain=True)
            mqtt_client.publish(TOPIC_AC, "ON" if ac_on else "OFF", qos=0, retain=True)
            mqtt_client.publish(TOPIC_DEH, "ON" if deh_on else "OFF", qos=0, retain=True)

            # 熱儲存 (MongoDB 即時存一筆)
            collection.insert_one(deepcopy(kafka_payload))

            # 冷儲存 (加入 Buffer)
            with lock:
                buffer.append(kafka_payload)

            # 小時切換 → flush
            if now.hour != current_hour:
                with lock:
                    flush_buffer()
                current_hour = now.hour

            logger.info(
                f"📡 發布 → temp={temp:.2f}, hum={hum:.2f}, "
                f"AC={'ON' if ac_on else 'OFF'}, DEH={'ON' if deh_on else 'OFF'}"
            )
            await asyncio.sleep(dt)

    finally:
        with lock:
            flush_buffer()
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        logger.info("🛑 Stop MQTT")











