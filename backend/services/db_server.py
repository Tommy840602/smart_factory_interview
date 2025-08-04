import asyncio
import os
import psycopg2
import json
from datetime import datetime, timedelta
from kafka import KafkaProducer
from backend.core.config import get_local_producer, get_cloud_producer

ROBOT_IDS = [f"robot_{i}" for i in range(1, 5)]
TABLES = ["left_arm", "right_arm", "nicla"]

# 初始化 Kafka Producer
local_producer = get_local_producer()
cloud_producer = get_cloud_producer()

# 記錄每個表的最新 timestamp
latest_ts = {}

async def start_background_db_server(polling_interval: float = 0.5):
    while True:
        for robot in ROBOT_IDS:
            for typ in TABLES:
                try:
                    ts_key = (robot, typ)
                    last_time = latest_ts.get(ts_key, datetime.utcnow() - timedelta(seconds=5))

                    # 連線 PostgreSQL
                    conn = psycopg2.connect(
                        dbname=robot,
                        user=os.getenv("PG_USER", "postgres"),
                        password=os.getenv("PG_PASSWORD", "root"),
                        host="localhost",
                        port=os.getenv("PG_PORT", "5432")
                    )
                    cur = conn.cursor()
                    cur.execute(f"SELECT * FROM {typ} ORDER BY ctid OFFSET 0 LIMIT 1;")
                    cols = [desc[0] for desc in cur.description]

                    rows = cur.fetchall()
                    for row in rows:
                        record = dict(zip(cols, row))
                        ts = record.get("timestamp", datetime.utcnow())
                        latest_ts[ts_key] = ts

                        payload = json.dumps(record).encode("utf-8")
                        topic_name = f"robot.{robot}.{typ}"
                        key = f"{robot}_{typ}".encode("utf-8")

                        # 僅送到本地 producer
                        if local_producer:
                            try:
                                local_producer.send(topic_name, value=payload, key=key)
                                print(f"✅ 發送至 local: {topic_name}")
                            except Exception as e:
                                print(f"❌ 本地 Kafka 發送失敗: {e}")

                        # ⚠️ 若你還沒建立 cloud topic，可以註解這段
                        if cloud_producer:
                             try:
                                 cloud_producer.send(topic_name, value=payload, key=key)
                                 print(f"✅ 發送至 cloud: {topic_name}")
                             except Exception as e:
                                 print(f"❌ 雲端 Kafka 發送失敗: {e}")

                    cur.close()
                    conn.close()

                except Exception as e:
                    print(f"⚠️ 查詢失敗 {robot}.{typ}: {e}")

        await asyncio.sleep(polling_interval)


















