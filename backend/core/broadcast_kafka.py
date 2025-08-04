import asyncio
import json, os
from kafka import KafkaConsumer
from dotenv import load_dotenv
from backend.schemas.robot import register_ws_client, unregister_ws_client, ws_clients

load_dotenv()
KAFKA_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC  = os.getenv("KAFKA_DB_TOPIC", "robot")

async def broadcast_kafka_to_ws(topics=None, bootstrap_servers=KAFKA_SERVER):
    topics = topics or [KAFKA_TOPIC]
    consumer = KafkaConsumer(
        *topics,
        bootstrap_servers=bootstrap_servers,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
        group_id="ws-broadcast-group",
        auto_offset_reset="latest"
    )

    def poll_kafka():
        return consumer.poll(timeout_ms=1000)

    while True:
        try:
            records = await asyncio.to_thread(poll_kafka)
            for partition in records.values():
                for record in partition:
                    topic = record.topic
                    message = {"key": record.key, "value": record.value}
                    await broadcast_to_topic_clients(topic, message)
        except Exception as e:
            print(f"⚠️ Kafka Consumer Failed: {e}")

        await asyncio.sleep(0.1)

async def broadcast_to_topic_clients(topic: str, message: dict):
    to_remove = set()
    for ws in ws_clients.get(topic, []):
        try:
            await ws.send_text(json.dumps(message))
        except Exception:
            to_remove.add(ws)

    for ws in to_remove:
        unregister_ws_client(topic, ws)  # ✅ 正確語法
