import sys,asyncio,json
import paho.mqtt.client as mqtt
from backend.utils import sparkplug_b_pb2 as sparkplug
from backend.api.robot_data import ws_clients

# ========= Config =========
BROKER = "localhost"
PORT = 1883
SP_NAMESPACE = "spBv1.0"
SP_GROUP_ID = "robotGroup"
SP_EDGE_ID = "robotEdge"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[MQTT] Connected")
        topic = f"{SP_NAMESPACE}/{SP_GROUP_ID}/DDATA/{SP_EDGE_ID}/#"
        client.subscribe(topic)
        print(f"[MQTT] Subscribed {topic}")
    else:
        print(f"[MQTT] Connect failed, code={rc}")

def on_message(client, userdata, msg):
    try:
        payload = sparkplug.Payload()
        payload.ParseFromString(msg.payload)

        data = {}
        for m in payload.metrics:
            if m.HasField("double_value"):
                data[m.name] = m.double_value
            elif m.HasField("string_value"):
                data[m.name] = m.string_value
            elif m.HasField("boolean_value"):
                data[m.name] = m.boolean_value
            else:
                data[m.name] = None

        device_id = msg.topic.split("/")[-1]
        robot, typ = device_id.split("_", 1)

        message = {
            "robot": robot,
            "typ": typ,
            "timestamp": payload.timestamp,
            "data": data,
        }

        # 廣播到 WebSocket
        path = f"{robot}/{typ}"
        if path in ws_clients:
            dead = []
            for ws in ws_clients[path]:
                try:
                    asyncio.run(ws.send_text(json.dumps(message)))
                except Exception:
                    dead.append(ws)
            for ws in dead:
                ws_clients[path].remove(ws)
    except Exception as e:
        print("[Decode error]", e, file=sys.stderr)

# ============ MQTT loop ============
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def subscriber_ws():
    """給 main.py 呼叫"""
    mqtt_client.connect(BROKER, PORT, 60)
    mqtt_client.loop_start()
    print("[Subscriber] MQTT loop started")