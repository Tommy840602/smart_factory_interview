# stream_mqtt_sparkplug.py
import os
import sys
import json
import time
import signal
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import paho.mqtt.client as mqtt

# Sparkplug B protobuf
from backend.utils import sparkplug_b_pb2 as sparkplug

# Kafka Producers
from backend.core.config import get_local_producer, get_cloud_producer

# Data Generators
from backend.utils.robot_generator import generate_record, generate_nicla_record


# ========= Config =========
ROBOTS = [1, 2, 3, 4]
DEVICES = ["left_arm", "right_arm", "nicla"]
INTERVAL = float(os.getenv("GEN_INTERVAL_SEC", "0.5"))
TZ = ZoneInfo("Asia/Taipei")
RUNNING = True

# MQTT / Sparkplug
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
SP_GROUP_ID = os.getenv("SP_GROUP_ID", "robotGroup")
SP_EDGE_ID = os.getenv("SP_EDGE_ID", "robotEdge")
SP_NAMESPACE = os.getenv("SP_NAMESPACE", "spBv1.0")

# Kafka
local_producer = None
cloud_producer = None
if callable(get_local_producer):
    try:
        local_producer = get_local_producer()
    except Exception as e:
        sys.stderr.write(f"[Kafka local init error] {e}\n")
else:
    local_producer = get_local_producer

if callable(get_cloud_producer):
    try:
        cloud_producer = get_cloud_producer()
    except Exception as e:
        sys.stderr.write(f"[Kafka cloud init error] {e}\n")
else:
    cloud_producer = get_cloud_producer


# ========= Sparkplug helpers =========
def _resolve_datatype_enum(sparkplug_mod):
    for path in (
        ("Payload", "Metric", "Datatype"),
        ("Metric", "Datatype"),
        ("DataType",),
    ):
        node = sparkplug_mod
        ok = True
        for name in path:
            if hasattr(node, name):
                node = getattr(node, name)
            else:
                ok = False
                break
        if ok:
            return node
    raise AttributeError("Cannot locate Sparkplug Datatype enum in sparkplug_b_pb2")

DT = _resolve_datatype_enum(sparkplug)


def build_sp_payload(record: dict) -> bytes:
    payload = sparkplug.Payload()
    payload.timestamp = int(time.time() * 1000)

    for k, v in record.items():
        if isinstance(v, (int, float)):
            m = payload.metrics.add()
            m.name = k
            m.datatype = DT.Double
            m.double_value = float(v)
        elif isinstance(v, list):
            for idx, val in enumerate(v, start=1):
                m = payload.metrics.add()
                m.name = f"{k}_{idx}"
                m.datatype = DT.Double
                m.double_value = float(val)
        else:
            m = payload.metrics.add()
            m.name = k
            m.datatype = DT.String
            m.string_value = str(v)
    return payload.SerializeToString()


# ========= Kafka send =========
def send_kafka(topic: str, key: str, record: dict):
    data = json.dumps(record, ensure_ascii=False).encode("utf-8")
    k = key.encode("utf-8")
    if local_producer:
        try:
            local_producer.send(topic, value=data, key=k)
        except Exception as e:
            sys.stderr.write(f"[Kafka local send error] {topic}: {e}\n")
    if cloud_producer:
        try:
            cloud_producer.send(topic, value=data, key=k)
        except Exception as e:
            sys.stderr.write(f"[Kafka cloud send error] {topic}: {e}\n")


# ========= MQTT init =========
mqtt_client = mqtt.Client()

def init_mqtt():
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=30)
    mqtt_client.loop_start()


# ========= Worker =========
def worker(robot_id: int, device: str):
    sp_device = f"robot_{robot_id}_{device}"
    sp_topic = f"{SP_NAMESPACE}/{SP_GROUP_ID}/DDATA/{SP_EDGE_ID}/{sp_device}"

    kafka_topic = f"robot.robot_{robot_id}.{device}"
    kafka_key = f"robot_{robot_id}_{device}"

    gen = generate_record if device in ("left_arm", "right_arm") else generate_nicla_record
    ts = datetime.now(TZ)

    while RUNNING:
        rec = gen(ts)
        rec["robot_id"] = robot_id
        rec["device"] = device
        rec["timestamp"] = ts.isoformat()

        # MQTT
        try:
            mqtt_client.publish(sp_topic, build_sp_payload(rec), qos=0, retain=False)
        except Exception as e:
            sys.stderr.write(f"[MQTT publish error] {sp_topic}: {e}\n")

        # Kafka
        try:
            send_kafka(kafka_topic, kafka_key, rec)
        except Exception as e:
            sys.stderr.write(f"[Kafka publish error] {kafka_topic}: {e}\n")

        ts += timedelta(seconds=INTERVAL)
        time.sleep(INTERVAL)


# ========= Lifecycle =========
threads = []

def start_all():
    init_mqtt()
    total = len(ROBOTS) * len(DEVICES)
    print(f"[Runner] MQTT(Sparkplug B) + Kafka(JSON) | {total} streams @ {INTERVAL}s")
    for rid in ROBOTS:
        for dev in DEVICES:
            t = threading.Thread(target=worker, args=(rid, dev), daemon=True)
            t.start()
            threads.append(t)

def stop_all(*_):
    global RUNNING
    RUNNING = False
    time.sleep(0.6)
    try:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
    except Exception:
        pass
    for t in threads:
        t.join(timeout=2)   # 等待 thread 收尾
    print("[Runner] shutdown complete.")
    sys.exit(0)























