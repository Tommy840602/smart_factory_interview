import asyncio
from asyncua import Client as UaClient
import paho.mqtt.client as mqtt
import time
from backend.core.config import OPCUA_URL,MQTT_BROKER, MQTT_PORT,TOPIC_AC,TOPIC_DEH,TOPIC_HUM,TOPIC_TEMP


TEMP_LO, TEMP_HI = 24.0, 26.0
HUM_LO,  HUM_HI  = 45.0, 55.0

async def ua_loop():
    # 建立 OPC UA Client
    ua_client = UaClient(OPCUA_URL)
    await ua_client.connect()
    # 取得 Node 物件
    node_temp = ua_client.get_node("ns=2;s=Temperature")
    node_hum  = ua_client.get_node("ns=2;s=Humidity")

    # 建立 MQTT Client 並連線
    mqtt_client = mqtt.Client()
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)

    try:
        while True:
            # 讀取感測值
            temp = await node_temp.read_value()
            hum  = await node_hum.read_value()

            # 決定開關狀態
            ac_on  = temp < TEMP_LO or temp > TEMP_HI
            deh_on = hum  < HUM_LO  or hum  > HUM_HI

            # 發佈至 MQTT topic
            mqtt_client.publish(TOPIC_TEMP, f"{temp:.2f}")
            mqtt_client.publish(TOPIC_HUM,  f"{hum:.2f}")
            mqtt_client.publish(TOPIC_AC,   "ON" if ac_on else "OFF")
            mqtt_client.publish(TOPIC_DEH,  "ON" if deh_on else "OFF")

            time.sleep(1)  # 每秒執行一次
    finally:
        await ua_client.disconnect()
        mqtt_client.disconnect()

if __name__ == "__main__":
    asyncio.run(ua_loop())
