import os
import time
import grpc
import logging
from pathlib import Path
from google.cloud import storage
import backend.utils.image_pb2_grpc as image_pb2_grpc
from grpc import RpcError

# —— 日志 —— #
logger = logging.getLogger(__name__)

# —— 路径、常量 —— #
PROJECT_ROOT    = Path(__file__).parent.parent.parent.absolute()
GCS_CRED_PATH   = PROJECT_ROOT / "plasma-creek-438010-s0-bbae490f4314.json"
GCS_BUCKET_NAME = "screw_anomalies"
GRPC_TARGET     = "localhost:50051"

# gRPC keepalive 与消息长度配置
GRPC_OPTIONS = [
    ('grpc.keepalive_time_ms',            30_000),
    ('grpc.keepalive_timeout_ms',         10_000),
    ('grpc.keepalive_permit_without_calls', True),
    ('grpc.max_receive_message_length',   100 * 1024 * 1024),
    ('grpc.max_send_message_length',      100 * 1024 * 1024),
]

# 全局 channel/stub 缓存
_channel = None
_stub    = None

def get_gcs_client() -> storage.Client:
    """
    返回一个已配置好凭证的 GCS client
    """
    if not GCS_CRED_PATH.exists():
        raise FileNotFoundError(f"GCS credentials not found: {GCS_CRED_PATH}")
    return storage.Client.from_service_account_json(str(GCS_CRED_PATH))

def _create_channel():
    """
    (内部) 建立并返回一个已就绪的 gRPC channel
    """
    channel = grpc.insecure_channel(GRPC_TARGET, options=GRPC_OPTIONS)
    grpc.channel_ready_future(channel).result(timeout=5)
    logger.info(f"gRPC channel ready: {GRPC_TARGET}")
    return channel

def get_classifier_stub():
    """
    返回一个有效的 ImageClassifierStub；断线时自动重连
    """
    global _channel, _stub
    try:
        if _channel is None:
            _channel = _create_channel()
            _stub    = image_pb2_grpc.ImageClassifierStub(_channel)
        else:
            # 检查 channel 是否还活着
            grpc.channel_ready_future(_channel).result(timeout=1)
    except (RpcError, Exception):
        logger.warning("gRPC connection lost, reconnecting...")
        _channel = _create_channel()
        _stub    = image_pb2_grpc.ImageClassifierStub(_channel)
    return _stub
