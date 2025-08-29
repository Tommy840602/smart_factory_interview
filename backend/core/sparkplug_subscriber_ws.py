# backend/core/sparkplug_subscriber_ws.py
from __future__ import annotations
import sys, asyncio
import os
import paho.mqtt.client as mqtt
from datetime import datetime, timezone
from typing import Optional, Tuple
from zoneinfo import ZoneInfo
TZ_TAIPEI = ZoneInfo("Asia/Taipei")
from backend.utils import sparkplug_b_pb2 as sparkplug
from backend.schemas.ws_manager import get_ws_hub, get_app_loop

# ========= Config（支援環境變數覆蓋） =========
BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", "1883"))
SP_NAMESPACE = os.getenv("SP_NAMESPACE", "spBv1.0")
SP_GROUP_ID = os.getenv("SP_GROUP_ID", "robotGroup")
SP_EDGE_ID = os.getenv("SP_EDGE_ID", "robotEdge")

# ========= 工具 =========
def _metric_to_py(m):
    if m.HasField("double_value"):   return m.double_value
    if m.HasField("float_value"):    return float(m.float_value)
    if m.HasField("int_value"):      return int(m.int_value)
    if m.HasField("long_value"):     return int(m.long_value)
    if m.HasField("string_value"):   return m.string_value
    if m.HasField("boolean_value"):  return bool(m.boolean_value)
    if m.HasField("bytes_value"):
        try:
            return m.bytes_value.decode("utf-8", errors="ignore")
        except Exception:
            return None
    return None

def _ts_to_iso_local(ts: int | None) -> str | None:
    """
    將 Sparkplug 的 timestamp 轉成 Asia/Taipei ISO8601（帶 +08:00）
    自動容錯：若收到秒級 timestamp 會自動乘 1000。
    """
    if ts is None:
        return None
    # 秒 -> 毫秒 的簡易判斷
    if ts < 10_000_000_000:  # 10-digit -> seconds
        ts *= 1000
    try:
        dt_utc = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        return dt_utc.astimezone(TZ_TAIPEI).isoformat(timespec="seconds")
    except Exception:
        return None

def _parse_device_from_topic(topic: str) -> Tuple[str, str]:
    """
    spBv1.0/<group>/DDATA/<edge>/<device>
    device 命名 ex: robot_1_left_arm -> (robot_1, left_arm)
    """
    parts = topic.split("/")
    device_id = parts[-1] if len(parts) >= 5 else topic.rsplit("/", 1)[-1]
    segs = device_id.split("_", 2)
    if len(segs) >= 3:
        return "_".join(segs[:2]), segs[2]
    return device_id, "default"

# ========= MQTT callbacks =========
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        topic = f"{SP_NAMESPACE}/{SP_GROUP_ID}/DDATA/{SP_EDGE_ID}/#"
        client.subscribe(topic)
        print(f"[MQTT Subscriber] ✅ Connected, subscribed {topic}")
    else:
        print(f"[MQTT Subscriber] ❌ Connect failed, code={rc}")

def on_message(client, userdata, msg):
    try:
        payload = sparkplug.Payload()
        payload.ParseFromString(msg.payload)

        data = {}
        for m in payload.metrics:
            data[m.name] = _metric_to_py(m)

        robot_id, typ = _parse_device_from_topic(msg.topic)

        message = {
            "robot": robot_id,
            "typ": typ,
            "timestamp": _ts_to_iso_local(payload.timestamp),
            "data": data,
        }
        path = f"{robot_id}/{typ}"

        loop = get_app_loop()   # 若未 init，這裡會丟 RuntimeError（啟動期就能看見）
        hub  = get_ws_hub()
        asyncio.run_coroutine_threadsafe(hub.publish(path, message), loop)

        keys = list(data.keys())[:3]
        print(f"[Subscriber] Broadcast {path} -> {keys} ...")

    except Exception as e:
        print("[Decode error]", e, file=sys.stderr)

def on_disconnect(client, userdata, rc, properties=None):
    print(f"[MQTT Subscriber] Disconnected rc={rc}")

# ========= 啟動 / 停止 =========
_mqtt_client: Optional[mqtt.Client] = None

def subscriber_ws():
    # ★ 啟動前強制檢查，沒 init 就丟錯（避免 APP_LOOP not set）
    _ = get_app_loop()
    _ = get_ws_hub()

    global _mqtt_client
    if _mqtt_client is not None:
        print("[MQTT Subscriber] ⚠ already started; skip")
        return

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.enable_logger()

    client.reconnect_delay_set(min_delay=1, max_delay=30)
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()
    _mqtt_client = client
    print("[Subscriber] MQTT loop started")









