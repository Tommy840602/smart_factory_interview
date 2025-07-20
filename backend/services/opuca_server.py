# backend/services/opuca_server.py
from asyncua import Server
import pandas as pd
import asyncio, os, re, json
from kafka import KafkaProducer
from dotenv import load_dotenv

load_dotenv()
KAFKA_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_OPCUA_TOPIC", "robot")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

data_nodes = {}
dataframes = {}

def extract_floats(val: str):
    try:
        return [float(x) for x in re.findall(r'-?\d+\.\d+(?:[eE][-+]?\d+)?', val)]
    except Exception as e:
        print(f"⚠️ 無法解析: {val} → {e}")
        return []

async def init_opcua_server():
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/opcua/server/")
    server.set_server_name("Async OPC UA Server")
    uri = "http://example.com/robots"
    idx = await server.register_namespace(uri)

    objects = server.nodes.objects
    robot_group = await objects.add_object(idx, "RobotGroup")

    for i in range(1, 5):
        robot = f"robot_{i}"
        robot_obj = await robot_group.add_object(idx, robot)
        for part in ["left_arm", "right_arm", "nicla"]:
            part_obj = await robot_obj.add_object(idx, part)
            csv_file = f"{robot}_{part}.csv"
            if not os.path.exists(csv_file):
                continue
            df = pd.read_csv(csv_file)
            dataframes[(robot, part)] = df

            for col in df.columns:
                first_val = str(df[col].iloc[0])
                if "[" in first_val:
                    arr = extract_floats(first_val)
                    for i in range(len(arr)):
                        new_col = f"{col}_{i}"
                        node = await part_obj.add_variable(idx, new_col, 0.0)
                        await node.set_writable()
                        data_nodes[(robot, part, new_col)] = node
                else:
                    node = await part_obj.add_variable(idx, col, 0.0)
                    await node.set_writable()
                    data_nodes[(robot, part, col)] = node

    return server

async def play_robot(robot):
    idx = 0
    while True:
        for part in ["left_arm", "right_arm", "nicla"]:
            key = (robot, part)
            if key not in dataframes:
                continue

            df = dataframes[key]
            if idx >= len(df):
                continue

            payload = {"robot": robot, "part": part, "data": {}}
            row = df.iloc[idx]
            for col, val in row.items():
                val = str(val)
                if "[" in val:
                    arr = extract_floats(val)
                    for i, v in enumerate(arr):
                        new_col = f"{col}_{i}"
                        node = data_nodes.get((robot, part, new_col))
                        if node:
                            await node.write_value(v)
                            payload["data"][new_col] = v
                else:
                    try:
                        float_val = float(val)
                        node = data_nodes.get((robot, part, col))
                        if node:
                            await node.write_value(float_val)
                            payload["data"][col] = float_val
                    except:
                        pass

            producer.send(KAFKA_TOPIC, payload)
        idx += 1
        await asyncio.sleep(0.5)

async def start_background_opcua_server():
    server = await init_opcua_server()
    print("✅ Async OPC UA Server 已啟動:http://localhost:4840")

    for i in range(1, 5):
        asyncio.create_task(play_robot(f"robot_{i}"))

    async with server:
        while True:
            await asyncio.sleep(1)




