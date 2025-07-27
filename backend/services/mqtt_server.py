import threading,asyncio
import time
import logging
import numpy as np
import paho.mqtt.client as mqtt
from backend.core.config import (MQTT_BROKER, MQTT_PORT, TOPIC_AC, TOPIC_DEH, TOPIC_HUM, TOPIC_TEMP)
from kafka import KafkaProducer
import json,os
import time
from dotenv import load_dotenv
from backend.core.config import  get_local_producer,get_cloud_producer

load_dotenv()
KAFKA_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC  = os.getenv("KAFKA_MQTT_TOPIC","sensor")

def send_kafka(topic, payload):
    data = json.dumps(payload).encode("utf-8") if not isinstance(payload, bytes) else payload
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

# 温湿度上下限
TEMP_LO, TEMP_HI = 24.0, 26.0
HUM_LO, HUM_HI   = 45.0, 55.0

def simulate_ou(dt, steps, C, y0, theta, sigma):
    """
    Ornstein–Uhlenbeck 过程模拟，支持自定义初始值
    dt: 时间步长（秒）
    steps: 总步数
    C: 平均回归值
    y0: 初始值
    theta: 回归速度 (1/τ)
    sigma: 噪声强度
    返回长度为 steps 的序列
    """
    y = np.zeros(steps)
    y[0] = y0
    for i in range(1, steps):
        y[i] = y[i-1] + theta * (C - y[i-1]) * dt + sigma * np.sqrt(dt) * np.random.randn()
    return y

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

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

async def start_background_mqtt_server():
    # 1. 初始化 MQTT 客户端
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect    = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_publish    = on_publish

    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
    mqtt_client.loop_start()
    logger.info("🔌 MQTT start")

    # OU 参数，指定初始温度为 38°C，初始湿度为 90%
    dt = 1.0           # 步长1秒
    steps = 100000     # 总步数
    temp_seq = simulate_ou(dt, steps, C=25.0, y0=38.0, theta=1/60, sigma=0.3)
    hum_seq  = simulate_ou(dt, steps, C=50.0, y0=90.0, theta=1/80, sigma=0.5)

    idx = 0
    try:
        while True:
            temp = float(temp_seq[idx])
            hum  = float(hum_seq[idx])
            idx = (idx + 1) % steps

            # 计算开关
            ac_on  = temp < TEMP_LO or temp > TEMP_HI
            deh_on = hum  < HUM_LO  or hum  > HUM_HI

            # 发布
            kafka_payload = {
                "source": "mqtt",
                "payload": {
                    "temperature": round(temp, 2),
                    "humidity": round(hum, 2),
                    "ac": "ON" if ac_on else "OFF",
                    "dehumidifier": "ON" if deh_on else "OFF"
                }
            }
            send_kafka(KAFKA_TOPIC, kafka_payload)
            mqtt_client.publish(TOPIC_TEMP, f"{temp:.2f}", qos=0, retain=True)
            mqtt_client.publish(TOPIC_HUM, f"{hum:.2f}", qos=0, retain=True)
            mqtt_client.publish(TOPIC_AC, "ON" if ac_on else "OFF", qos=0, retain=True)
            mqtt_client.publish(TOPIC_DEH, "ON" if deh_on else "OFF", qos=0, retain=True)

            logger.info(
                f"📡 發布 → temp={temp:.2f}, hum={hum:.2f}, "
                f"AC={'ON' if ac_on else 'OFF'}, DEH={'ON' if deh_on else 'OFF'}"
            )
            await asyncio.sleep(dt)

    finally:
        logger.info("🛑 Stop MQTT")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()









