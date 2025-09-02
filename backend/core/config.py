from kafka import KafkaProducer
import json
import os
from pydantic_settings import BaseSettings
from pydantic import Extra
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
from psycopg2.pool import SimpleConnectionPool


Telegram_API_ID=22468436
Telegram_API_HASH="cc037d52e7b58664b9140e82f8aa73b5"

class Settings(BaseSettings):
    REDIS_URL: str = "redis://localhost:6379"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"  # 这里可以设置默认值，或留空让.env提供
    KAFKA_CLOUD_BOOTSTRAP: str = ""
    KAFKA_CLOUD_USER: str = ""
    KAFKA_CLOUD_PASS: str = ""
    OPCUA_NS_URI: str = ""
    TELEGRAM_API_ID: int = 22468436
    TELEGRAM_API_HASH: str = "cc037d52e7b58664b9140e82f8aa73b5"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = Extra.allow

settings = Settings()

#OPCUA


#MQTT Broker
MQTT_BROKER="localhost"
MQTT_PORT=1883
TOPIC_TEMP="sensor/temperature"
TOPIC_HUM="sensor/humidity"
TOPIC_AC="actuators/ac"
TOPIC_DEH="actuators/dehumidifier"

#kafka
def get_local_producer():
    return KafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: v.encode('utf-8') if isinstance(v, str) else v,
    )

#def get_cloud_producer():
#    return KafkaProducer(
#        bootstrap_servers=settings.KAFKA_CLOUD_BOOTSTRAP,
#        security_protocol="SASL_SSL",
#        sasl_mechanism="PLAIN",
#        sasl_plain_username=settings.KAFKA_CLOUD_USER,
#        sasl_plain_password=settings.KAFKA_CLOUD_PASS,
#        value_serializer=lambda v: v.encode('utf-8') if isinstance(v, str) else v,
#    )


ROBOT_IDS = [f"robot_{i}" for i in range(1, 5)]
TABLES = ["left_arm", "right_arm", "nicla"]
# Kafka broker URL
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

def create_robot_topics():
    admin_client = KafkaAdminClient(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        client_id="topic_initializer"
    )

    topic_names = [f"robot.{robot}.{typ}" for robot in ROBOT_IDS for typ in TABLES]
    existing_topics = admin_client.list_topics()

    new_topics = []
    for topic in topic_names:
        if topic not in existing_topics:
            new_topics.append(NewTopic(name=topic, num_partitions=1, replication_factor=1))
            print(f"🆕 Preparing to create topic: {topic}")
        else:
            print(f"✅ Topic already exists: {topic}")

    if new_topics:
        admin_client.create_topics(new_topics=new_topics, validate_only=False)
        print("🎉 All missing topics created successfully!")
    else:
        print("👌 All topics already exist. Nothing to create.")



pools = {
    str(i): SimpleConnectionPool(
        1, 5,
        dbname=f"robot_{i}",
        user="postgres",
        password="root",
        host="localhost",
        port="5432"
    ) for i in range(1, 5)
}
print("[Init] PostgreSQL pools 建立完成")


