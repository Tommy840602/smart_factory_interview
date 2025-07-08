import pydantic 

Telegram_API_ID=22468436
Telegram_API_HASH="cc037d52e7b58664b9140e82f8aa73b5"

class Settings():
    REDIS_URL: str = "redis://localhost:6379"

    class Config:
        env_file = ".env"

settings = Settings()

#OPCUA
OPCUA_URL="opc.tcp://MacBookAir.lan:53530/OPCUA/SimulationServer"

#MQTT Broker
MQTT_BROKER="localhost"
MQTT_PORT=1883
TOPIC_TEMP="sensor/temperature"
TOPIC_HUM="sensor/humidity"
TOPIC_AC="actuators/ac"
TOPIC_DEH="actuators/dehumidifier"




