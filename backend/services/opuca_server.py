import asyncio
import os
import json
import logging
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI
from kafka import KafkaProducer
from google.cloud import storage
from asyncua import Server, Client
from backend.core.config import get_local_producer, get_cloud_producer

# === Logger ===
logger = logging.getLogger("opcua")
logging.basicConfig(level=logging.INFO)


# === 基本設定 ===
load_dotenv()
KAFKA_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_OPCUA_TOPIC", "robot")
GCP_CREDENTIALS = "plasma-creek-438010-s0-bbae490f4314.json"
BUCKET_NAME = "robot_arm_data"
OPCUA_URL = "opc.tcp://localhost:4840/opcua/server/"

gcs = storage.Client.from_service_account_json(GCP_CREDENTIALS)

# === Kafka 發送函式 ===
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

# === 建立節點（遞迴） ===
async def add_nodes_recursively(server, parent_node, idx, structure_dict):
    for name, value in structure_dict.items():
        try:
            if isinstance(value, dict):
                child = await parent_node.add_object(idx, name)
                await add_nodes_recursively(server, child, idx, value)
            else:
                var = await parent_node.add_variable(idx, name, value)
                await var.set_writable()
        except Exception as e:
            logger.warning(f"[OPCUA] 無法新增節點 {name}: {e}")

# === robot 結構（必須有 MultiFileMetadata） ===
robot = {
    "MultiFileMetadata": ""
}

# === 背景啟動 asyncua Server ===
async def start_background_opcua_server():
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/opcua/server/")
    uri = "http://example.com/robotdata"
    idx = await server.register_namespace(uri)
    objects = server.nodes.objects
    root = await objects.add_folder(idx, "RobotData")
    await add_nodes_recursively(server, root, idx, robot)
    logger.info("✅ OPC UA Server ready.")
    async with server:
        while True:
            await asyncio.sleep(1)

# === GCP Storage 取 metadata ===
def get_bucket_csv_metadata(bucket_name):
    bucket = gcs.bucket(bucket_name)
    blobs = list(bucket.list_blobs())
    metadatas = []
    for blob in blobs:
        if blob.name.endswith('.csv'):
            try:
                with blob.open("r") as f:
                    df = pd.read_csv(f, nrows=10)
                columns_info = [
                    {"name": col, "dtype": str(df[col].dtype)} for col in df.columns
                ]
                stats = {
                    col: {
                        "min": float(df[col].min()) if df[col].dtype != "object" else None,
                        "max": float(df[col].max()) if df[col].dtype != "object" else None,
                        "mean": float(df[col].mean()) if df[col].dtype != "object" else None,
                    }
                    for col in df.columns if df[col].dtype != "object"
                }
                metadata = {
                    "file_name": blob.name.split('/')[-1],
                    "gcs_path": f"gs://{bucket_name}/{blob.name}",
                    "file_url": f"https://storage.googleapis.com/{bucket_name}/{blob.name}",
                    "last_update": blob.updated.isoformat(),
                    "size": blob.size,
                    "columns": columns_info,
                    "stats": stats,
                    "sample": df.head(1).to_dict(orient="records")
                }
                metadatas.append(metadata)
            except Exception as e:
                print(f"Failed to read file: {blob.name} -- {e}")
    return metadatas

# === 寫 metadata 到 OPC UA, 同步推送 Kafka ===
async def write_metadata_to_opcua(metadatas):
    async with Client(OPCUA_URL) as client:
        idx = await client.get_namespace_index("http://example.com/robotdata")
        robot_folder = await client.nodes.objects.get_child(f"{idx}:RobotData")
        node = await robot_folder.get_child(f"{idx}:MultiFileMetadata")
        await node.write_value(json.dumps(metadatas))
        print("[OPC UA] Metadata written!")

async def sync_storage_to_opcua_kafka():
    metadatas = get_bucket_csv_metadata(BUCKET_NAME)
    await write_metadata_to_opcua(metadatas)
    for meta in metadatas:
        send_kafka(KAFKA_TOPIC, meta)














