# 智慧工廠專案 (Smart Factory Digital Twin Platform)

## 📌 專案簡介
本專案旨在建置一個 **數位孿生 (Digital Twin) 智慧工廠平台**，整合多來源設備數據（Robot、Sensor、UPS、Image），透過 **即時資料串流、AI 預測、3D 可視化** 與 **雲端部署**，實現智慧化監控、預測維護與生產優化。

## 🏗 系統架構




---

## 🔗 資料來源與傳輸方式

- **Sensor (感測器資料)**  
  - 模擬方式：Ornstein–Uhlenbeck 隨機過程  
  - 傳輸協議：MQTT  
  - 流向：MQTT ➝ Kafka ➝ MongoDB  

- **UPS (不斷電系統)**  
  - 模擬方式：隨機生成狀態  
  - 傳輸協議：WebSocket  
  - 流向：FastAPI WS ➝ 前端 Dashboard 
 
- **Robot (機械手臂資料)**  
  - 模擬方式：隨機生成動作數據  
  - 傳輸協議：Sparkplug-B over MQTT  
  - 流向：MQTT Broker ➝ Kafka ➝ PostgreSQL (熱資料庫)  

- **Image (影像資料)**  
  - 資料來源：GCP Storage
    (Screw Anomalies Dataset: https://www.kaggle.com/datasets/hkayan/industrial-robotic-arm-anomaly-detection)  
  - 傳輸協議：gRPC  
  - 流向：gRPC Server ➝ Autoencoder + KNN 模型 ➝ Kafka ➝ 前端異常檢測展示結果  

- **Open data (Weather,Power reserve rate)**  
  - 資料來源: Taipower,CWB
  - 傳輸協議：WebSocket  
  - 流向：FastAPI WS ➝ 前端 Dashboard 


---

## ⚙️ 技術棧

- **前端 (Frontend)**  
  - Vue 3 + Three.js + Chart.js
  - Hover/Click 顯示即時數據  
  - UPS 狀態紅/黃/綠燈警示  

- **後端 (Backend)**  
  - FastAPI (RESTful API, WebSocket)  
  - gRPC (影像分類服務)  
  - Sparkplug-B (Robot 協議)  
  - Kafka (資料串流核心)  

- **資料庫 / 儲存**  
  - PostgreSQL (Robot 時序資料)  
  - MongoDB (Sensor 時序資料)  
  - GCP Storage (Image 冷資料, Parquet 歷史)  

- **AI 模型**  
  - ARIMA (Sensor 預測)  
  - Autoencoder + KNN (影像瑕疵檢測)  
  - Ornstein–Uhlenbeck Process (Sensor 模擬)  

---

## 🌟 專案亮點
- **跨協議整合**：MQTT、Sparkplug-B、WebSocket、gRPC  
- **多來源模擬器**：Robot / Sensor / UPS / Image 四類設備完整覆蓋  
- **資料分層架構**：PostgreSQL 熱存取 + GCP Storage 冷存取  
- **即時可視化**：Vue + Three.js 數位孿生工廠  
- **AI 輔助**：結合時間序列預測與異常影像偵測  

---


👉 本專案展現了 **IoT + AI + Cloud + 3D Digital Twin** 的完整實踐，涵蓋 **資料工程、全端開發、雲端部署、工廠自動化**，可作為智慧製造與工業 4.0 的落地解決方案。


Copyright © 2025 Tommy.Huang
This project for interview
