from kafka import KafkaProducer
import json
import os
from pydantic_settings import BaseSettings
from pydantic import Extra

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

def get_cloud_producer():
    return KafkaProducer(
        bootstrap_servers=settings.KAFKA_CLOUD_BOOTSTRAP,
        security_protocol="SASL_SSL",
        sasl_mechanism="PLAIN",
        sasl_plain_username=settings.KAFKA_CLOUD_USER,
        sasl_plain_password=settings.KAFKA_CLOUD_PASS,
        value_serializer=lambda v: v.encode('utf-8') if isinstance(v, str) else v,
    )

#BOOTSTRAP_SERVERS='pkc-l7j7w.asia-east1.gcp.confluent.cloud:9092'  # 替換為您的 Bootstrap Server
#API_KEY='XOYQOIR2SGXPDPKG'  # 替換為您的 API Key
#API_SECRET='WxPIE0xCxQkM/NUkBqn60RLSUmNKhJeYjRJexQE7UVsjMbpfS2m9cPFLij9vN04O'  # 替換為您的 API Secret
#KAFKA_TOPIC=robotic_arm_data
#KAFKA_GROUP=robotic_arm_consumer_group
