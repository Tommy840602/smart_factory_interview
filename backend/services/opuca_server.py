# backend/services/opcua_server.py
from asyncua import Server, ua
import pandas as pd
import asyncio, os, re, json, traceback
from pathlib import Path
from kafka import KafkaProducer
from dotenv import load_dotenv
import numpy as np
import logging

# 設置 asyncua 日誌
logging.getLogger("asyncua").setLevel(logging.INFO)

load_dotenv()
KAFKA_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_OPCUA_TOPIC", "robot")
URI = os.getenv("OPCUA_NS_URI", "http://example.com/robots")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

data_nodes = {}
dataframes = {}
DATA_DIR = Path(__file__).resolve().parent / "data"

FLOAT_RE = re.compile(r'-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?')

def extract_floats(val: str):
    try:
        return [float(x) for x in FLOAT_RE.findall(val)]
    except Exception as e:
        print(f"⚠️ 無法解析: {val} → {e}")
        return []

async def init_opcua_server():
    server = Server()

    try:
        await server.init()
        server.set_endpoint("opc.tcp://0.0.0.0:4840/opcua/server/")
        server.set_server_name("Async OPC UA Server")
        print(f"✅ Server initialized with endpoint: opc.tcp://0.0.0.0:4840/opcua/server/")

        idx = await server.register_namespace(URI)
        print(f"✅ Registered namespace: {URI} at index {idx}")

        objects = server.nodes.objects
        robot_group = await objects.add_object(ua.NodeId("RobotGroup", idx), "RobotGroup")
        print(f"✅ Created RobotGroup (ns={idx})")

        for rid in range(1, 5):
            robot_name = f"robot_{rid}"
            robot_obj = await robot_group.add_object(ua.NodeId(robot_name, idx), robot_name)
            print(f"✅ Created robot node: {robot_name} (ns={idx})")

            for part in ["left_arm", "right_arm", "nicla"]:
                part_obj = await robot_obj.add_object(ua.NodeId(f"{robot_name}_{part}", idx), part)
                csv_file = DATA_DIR / f"{robot_name}_{part}.csv"
                if not csv_file.exists():
                    print(f"⚠️ CSV file not found: {csv_file}")
                    continue

                df = pd.read_csv(csv_file)
                dataframes[(robot_name, part)] = df
                print(f"✅ Processing CSV: {csv_file}, Columns: {df.columns.tolist()}")

                for col in df.columns:
                    first_val = str(df[col].iloc[0])
                    if "[" in first_val:
                        arr = extract_floats(first_val)
                        for j in range(len(arr)):
                            new_col = f"{col}_{j}"
                            node = await part_obj.add_variable(ua.NodeId(f"{robot_name}_{part}_{new_col}", idx), new_col, 0.0)
                            await node.set_writable()
                            data_nodes[(robot_name, part, new_col)] = node
                            print(f"✅ Added variable: {new_col} (ns={idx})")
                    else:
                        node = await part_obj.add_variable(ua.NodeId(f"{robot_name}_{part}_{col}", idx), col, 0.0)
                        await node.set_writable()
                        data_nodes[(robot_name, part, col)] = node
                        print(f"✅ Added variable: {col} (ns={idx})")

        return server, idx

    except Exception as e:
        print(f"❌ Failed to initialize OPC UA server: {e}")
        traceback.print_exc()
        raise

async def play_robot(robot):
    idx_row = 0
    while True:
        for part in ["left_arm", "right_arm", "nicla"]:
            key = (robot, part)
            if key not in dataframes:
                continue

            df = dataframes[key]
            if idx_row >= len(df):
                continue

            payload = {"robot": robot, "part": part, "data": {}}
            row = df.iloc[idx_row]

            for col, val in row.items():
                if pd.isna(val):
                    continue

                sval = str(val)
                if "[" in sval:
                    arr = extract_floats(sval)
                    for j, v in enumerate(arr):
                        new_col = f"{col}_{j}"
                        node = data_nodes.get((part, new_col))
                        if node:
                            await node.write_value(v)
                            payload["data"][new_col] = v
                else:
                    try:
                        v = float(sval)
                        node = data_nodes.get((robot, part, col))
                        if node:
                            await node.write_value(v)
                            payload["data"][col] = v
                    except ValueError:
                        pass

            producer.send(KAFKA_TOPIC, payload)

        idx_row += 1
        await asyncio.sleep(0.5)

async def sanity_check(server, idx):
    try:
        # 使用 read_browse_name 替代 get_browse_name
        robot_group = await server.get_node(ua.NodeId("RobotGroup", idx)).read_browse_name()
        print(f"✅ Sanity check: RobotGroup found with browse name {robot_group} (ns={idx})")
        robot_1 = await server.get_node(ua.NodeId("robot_1", idx)).read_browse_name()
        print(f"✅ Sanity check: robot_1 found with browse name {robot_1} (ns={idx})")
        left_arm = await server.get_node(ua.NodeId("robot_1_left_arm", idx)).read_browse_name()
        print(f"✅ Sanity check: robot_1/left_arm found with browse name {left_arm} (ns={idx})")
    except ua.UaError as e:
        print(f"❌ Sanity check failed: {e}")
        # 列印節點樹以除錯
        async def browse_nodes(node, indent=0):
            try:
                children = await node.get_children()
                for child in children:
                    name = await child.read_browse_name()
                    print("  " * indent + f"Node: {name} (NodeId: {child.nodeid})")
                    await browse_nodes(child, indent + 1)
            except Exception as ex:
                print("  " * indent + f"Error browsing node {node.nodeid}: {ex}")
        print("🔍 Browsing node tree from Objects:")
        await browse_nodes(server.nodes.objects)
        # 繼續運行，不拋出異常
        print("⚠️ Continuing server operation despite sanity check failure")

async def start_background_opcua_server():
    try:
        server, ns_idx = await init_opcua_server()
        print("✅ Async OPC UA Server 已啟動: opc.tcp://0.0.0.0:4840/opcua/server/")

        # 啟動四個播放 task
        for rid in range(1, 5):
            asyncio.create_task(play_robot(f"robot_{rid}"))
            print(f"✅ Started play_robot task for robot_{rid}")

        # 執行 sanity check
        await sanity_check(server, ns_idx)

        async with server:
            while True:
                await asyncio.sleep(1)

    except Exception as e:
        print(f"❌ OPC UA Server failed to start: {e}")
        traceback.print_exc()
        raise







