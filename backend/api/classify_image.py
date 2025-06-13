import logging
import io
import grpc
from fastapi import APIRouter, HTTPException
from PIL import Image

from backend.core.grpc_channel import get_classifier_stub, get_gcs_client
from backend.utils.image_pb2 import ImageRequest

logger = logging.getLogger(__name__)
grpc_router = APIRouter(tags=["gPRC"])

@grpc_router.get("/images")
def list_images():
    try:
        client = get_gcs_client()
        bucket = client.bucket("screw_anomalies")
        blobs = bucket.list_blobs(prefix="image/")
    except Exception as e:
        logger.exception("[list_images] GCS 读取失败")
        raise HTTPException(status_code=500, detail="无法获取图片列表")

    images = [
        b.name
        for b in blobs
        if b.name.lower().endswith((".png", ".jpg", ".jpeg"))
    ]
    return images

@grpc_router.post("/classify/{image_id:path}")
def classify(image_id: str):
    # 1. 从 GCS 下载
    try:
        client = get_gcs_client()
        bucket = client.bucket("screw_anomalies")
        blob = bucket.blob(image_id)
        if not blob.exists():
            raise HTTPException(404, "Image not found")
        data = blob.download_as_bytes()
    except HTTPException:
        raise
    except Exception:
        logger.exception("[classify] GCS 下载失败")
        raise HTTPException(status_code=500, detail="无法读取图片")

    # 2. 验证图像
    try:
        Image.open(io.BytesIO(data))
    except Exception:
        logger.exception("[classify] 图像解析失败")
        raise HTTPException(status_code=400, detail="无效的图片文件")

    # 3. 调用 gRPC
    try:
        stub = get_classifier_stub()
        reqs = iter([ImageRequest(image_id=image_id, image_data=data)])
        resp = next(stub.Classify(reqs))
    except grpc.RpcError as e:
        logger.exception(f"[classify] gRPC 调用失败: {e}")
        if e.code() == grpc.StatusCode.UNAVAILABLE:
            raise HTTPException(503, "分类服务不可用")
        raise HTTPException(500, detail=e.details())
    except Exception:
        logger.exception("[classify] 未知错误")
        raise HTTPException(500, detail="服务器内部错误")

    return {
        "image_id":   resp.image_id,
        "label":      resp.label,
        "confidence": resp.confidence,
    }
