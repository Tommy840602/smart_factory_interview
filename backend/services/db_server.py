from kafka import KafkaConsumer
from psycopg2.pool import SimpleConnectionPool
import psycopg2
import pandas as pd
from google.cloud import storage
from datetime import datetime
import threading, time, json, io
from dateutil import parser
from datetime import datetime, timezone

# ===== PostgreSQL Connection Pools =====
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

# ===== Kafka Topics =====
TOPICS = [
    "robot.robot_1.left_arm", "robot.robot_1.right_arm", "robot.robot_1.nicla",
    "robot.robot_2.left_arm", "robot.robot_2.right_arm", "robot.robot_2.nicla",
    "robot.robot_3.left_arm", "robot.robot_3.right_arm", "robot.robot_3.nicla",
    "robot.robot_4.left_arm", "robot.robot_4.right_arm", "robot.robot_4.nicla",
]

# ===== GCS client =====
gcs = storage.Client.from_service_account_json("plasma-creek-438010-s0-bbae490f4314.json")
bucket = gcs.bucket("robot_arm_cold")

# ===== Export trigger =====
MAX_MB = 100
INTERVAL = 300  # 5 分鐘
TABLES = ["left_arm", "right_arm", "nicla"]

# ===== 欄位 mapping =====
FIELD_MAPPING = {
    "Actual Joint Positions": "actual_joint_positions",
    "Actual Joint Velocities": "actual_joint_velocities",
    "Actual Joint Currents": "actual_joint_currents",
    "Actual Cartesian Coordinates": "actual_cartesian_coordinates",
    "Actual Tool Speed": "actual_tool_speed",
    "Generalized Forces": "generalized_forces",
    "Temperature of Each Joint": "temperature_of_each_joint",
    "Execution Time": "execution_time",
    "Safety Status": "safety_status",
    "Tool Acceleration": "tool_acceleration",
    "Norm of Cartesian Linear Momentum": "norm_of_cartesian_linear_momentum",
    "Robot Current": "robot_current",
    "Joint Voltages": "joint_voltages",
    "Elbow Position": "elbow_position",
    "Elbow Velocity": "elbow_velocity",
    "Tool Current": "tool_current",
    "Tool Temperature": "tool_temperature",
    "TCP Force": "tcp_force",
    "Anomaly State": "anomaly_state",
    # Nicla
    "AccX": "accx", "AccY": "accy", "AccZ": "accz",
    "GyroX": "gyrox", "GyroY": "gyroy", "GyroZ": "gyroz",
    "MagX": "magx", "MagY": "magy", "MagZ": "magz"
}

def normalize_keys(data: dict) -> dict:
    return {FIELD_MAPPING.get(k, k): v for k, v in data.items()}

# ===== Consumer Worker =====
def consume_and_insert(topic: str):
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=["localhost:9092"],
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        group_id=f"pg-writer-{topic}"
    )
    print(f"[Thread-{topic}] KafkaConsumer 啟動")

    for msg in consumer:
        _, robot, table = msg.topic.split(".")
        robot_id = robot.split("_")[1]
        data = normalize_keys(msg.value)
        ts = data.get("timestamp") or datetime.now()

        conn = pools[robot_id].getconn()
        cur = conn.cursor()
        try:
            if table in ("left_arm", "right_arm"):
                cur.execute(f"""
                    INSERT INTO {table} (timestamp, actual_joint_positions, actual_joint_velocities,
                        actual_joint_currents, actual_cartesian_coordinates, actual_tool_speed,
                        generalized_forces, temperature_of_each_joint, execution_time,
                        safety_status, tool_acceleration, norm_of_cartesian_linear_momentum,
                        robot_current, joint_voltages, elbow_position,
                        elbow_velocity, tool_current, tool_temperature,
                        tcp_force, anomaly_state)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    ts,
                    json.dumps(data.get("actual_joint_positions")),
                    json.dumps(data.get("actual_joint_velocities")),
                    json.dumps(data.get("actual_joint_currents")),
                    json.dumps(data.get("actual_cartesian_coordinates")),
                    json.dumps(data.get("actual_tool_speed")),
                    json.dumps(data.get("generalized_forces")),
                    json.dumps(data.get("temperature_of_each_joint")),
                    data.get("execution_time"),
                    data.get("safety_status"),
                    json.dumps(data.get("tool_acceleration")),
                    data.get("norm_of_cartesian_linear_momentum"),
                    data.get("robot_current"),
                    json.dumps(data.get("joint_voltages")),
                    json.dumps(data.get("elbow_position")),
                    json.dumps(data.get("elbow_velocity")),
                    data.get("tool_current"),
                    data.get("tool_temperature"),
                    json.dumps(data.get("tcp_force")),
                    data.get("anomaly_state")
                ))
            elif table == "nicla":
                cur.execute(f"""
                    INSERT INTO {table} (timestamp, accx, accy, accz, gyrox, gyroy, gyroz, magx, magy, magz)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    ts,
                    data.get("accx"), data.get("accy"), data.get("accz"),
                    data.get("gyrox"), data.get("gyroy"), data.get("gyroz"),
                    data.get("magx"), data.get("magy"), data.get("magz")
                ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"[{topic}] ❌ DB error: {e}")
        finally:
            cur.close()
            pools[robot_id].putconn(conn)


# ===== Export Worker =====
def query_postgres(robot_id: str, table: str) -> pd.DataFrame:
    query = f"""
        SELECT *
        FROM {table}
        WHERE timestamp >= NOW() - INTERVAL '5 minutes'
    """
    conn = pools[robot_id].getconn()
    try:
        df = pd.read_sql(query, conn)
    finally:
        pools[robot_id].putconn(conn)
    return df

def upload_chunk(df: pd.DataFrame, robot_id: str, table: str, part_idx: int):
    buffer = io.BytesIO()
    df.to_parquet(buffer, engine="pyarrow", index=False)
    buffer_size = buffer.getbuffer().nbytes / (1024 * 1024)
    buffer.seek(0)
    filename = f"part_{part_idx}.parquet"
    blob = bucket.blob(f"robot_{robot_id}/{table}/dt={datetime.now().date()}/{filename}")
    blob.upload_from_file(buffer, content_type="application/octet-stream")

    print(f"✅ Uploaded {filename} ({buffer_size:.2f} MB, rows={len(df)})")

def poll_postgres():
    # 🔹 每個 DB × Table 都要有自己的 buffer & 狀態
    buffers = {f"robot_{i}_{t}": pd.DataFrame() for i in range(1, 5) for t in TABLES}
    part_idxs = {f"robot_{i}_{t}": 1 for i in range(1, 5) for t in TABLES}
    last_upload_times = {f"robot_{i}_{t}": time.time() for i in range(1, 5) for t in TABLES}
    current_day = datetime.now().date()

    while True:
        for robot_id in pools.keys():
            for table in TABLES:
                key = f"robot_{robot_id}_{table}"
                df = query_postgres(robot_id, table)
                if not df.empty:
                    buffers[key] = pd.concat([buffers[key], df], ignore_index=True)

                # 檢查跨天 reset
                today = datetime.now().date()
                if today != current_day:
                    print(f"📅 新的一天 {today}，reset part_idx=1 for all tables")
                    current_day = today
                    part_idxs = {k: 1 for k in part_idxs.keys()}

                # 檢查大小/時間條件
                size_mb = buffers[key].memory_usage(deep=True).sum() / (1024 * 1024)
                elapsed = time.time() - last_upload_times[key]

                if (size_mb >= MAX_MB) or (elapsed >= INTERVAL and not buffers[key].empty):
                    upload_chunk(buffers[key], robot_id, table, part_idxs[key])
                    buffers[key] = pd.DataFrame()
                    part_idxs[key] += 1
                    last_upload_times[key] = time.time()

        time.sleep(10)

if __name__ == "__main__":
    # 啟動 DB → GCS 上傳的背景執行緒
    db_thread = threading.Thread(target=poll_postgres, daemon=True)
    db_thread.start()
    print("[Init] PostgreSQL → GCS Export 啟動完成")

    # 啟動 Kafka Consumer threads
    consumer_threads = []
    for topic in TOPICS:
        t = threading.Thread(target=consume_and_insert, args=(topic,), daemon=True)
        t.start()
        consumer_threads.append(t)
        print(f"[Init] Consumer thread 啟動: {topic}")

    # main thread 等待子執行緒
    for t in consumer_threads:
        t.join()



