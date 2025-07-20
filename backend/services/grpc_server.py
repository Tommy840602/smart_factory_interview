import os,io,grpc,threading,torch
import numpy as np
from concurrent import futures
from PIL import Image
from torchvision import transforms
from google.cloud import storage
import backend.utils.image_pb2 as pb2
import backend.utils.image_pb2_grpc as pb2_grpc
from backend.model.autoencoder import Autoencoder
from kafka import KafkaProducer
import json
import time  
from dotenv import load_dotenv

load_dotenv()
KAFKA_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC  = os.getenv("KAFKA_GRPC_TOPIC", "image")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

# 1. 初始化模型 & encoder
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
ae = Autoencoder().to(DEVICE)
ae.load_state_dict(torch.load("backend/model/autoencoder.pth", map_location=DEVICE))
ae.eval()
encoder = ae.encoder

# 2. 载入质心 & 类别列表
#    假设 centroids.npy 是用 224×224 输入时算出的，shape=(6, 3136)
CENTROIDS = np.load("backend/model/centroids.npy")
CLASS_NAMES = [
    'good','manipulated_front','scratch_head',
    'scratch_neck','thread_side','thread_top'
]

# 3. GCS client
gcs = storage.Client.from_service_account_json("plasma-creek-438010-s0-bbae490f4314.json")
bucket = gcs.bucket("screw_anomalies")

# 4. 预处理 pipeline —— 改为 224×224，以匹配 centroids.npy 的生成方式
PREPROCESS = transforms.Compose([
    transforms.Resize((224,224)),
    transforms.ToTensor(),
])

class ImageStreamerServicer(pb2_grpc.ImageStreamerServicer):
    def StreamImages(self, request, context):
        for blob in bucket.list_blobs(prefix="image/"):
            data = blob.download_as_bytes()
            yield pb2.ImageRequest(image_id=blob.name, image_data=data)

class ImageClassifierServicer(pb2_grpc.ImageClassifierServicer):
    def Classify(self, request_iterator, context):
        for req in request_iterator:
            img = Image.open(io.BytesIO(req.image_data)).convert("RGB")
            x = PREPROCESS(img).unsqueeze(0).to(DEVICE)
            with torch.no_grad():
                z = encoder(x)
            z_flat = z.view(z.size(0), -1).cpu().numpy()[0]
            dists = np.mean((CENTROIDS - z_flat)**2, axis=1)
            idx = int(np.argmin(dists))
            label = CLASS_NAMES[idx]
            conf = 1 - float(dists[idx] / (dists.sum() + 1e-8))

            # ✅ 推送 Kafka
            kafka_payload = {
                "image_id": req.image_id,
                "label": label,
                "confidence": round(conf, 4),
                "timestamp": time.time()
            }
            try:
                producer.send(KAFKA_TOPIC, kafka_payload)
                print(f"📤 Kafka 推送：{kafka_payload}")
            except Exception as e:
                print(f"❌ Kafka 發送失敗：{e}")

            yield pb2.ClassificationResult(
                image_id   = req.image_id,
                label      = label,
                confidence = conf
            )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
    pb2_grpc.add_ImageStreamerServicer_to_server(ImageStreamerServicer(), server)
    pb2_grpc.add_ImageClassifierServicer_to_server(ImageClassifierServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("gRPC server listening on 50051")
    server.start()
    server.wait_for_termination()


def start_background_grpc_server():
    thread=threading.Thread(target=serve,daemon=True)
    thread.start()
    
