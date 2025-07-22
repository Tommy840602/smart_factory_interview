<!-- src/pages/SceneWrapperMultiWS.vue -->
<template>
  <ThreeScene
    :sensorData="sensorData"
    :chartRecords="chartRecords"
  />
</template>

<script setup>
// 完全純 JavaScript，不用 TS
import { ref, onMounted, onBeforeUnmount } from 'vue'
import ThreeScene from '@/components/ThreeScene.vue'
import mqtt from 'mqtt'

// 1️⃣ 定義要監聽的 Robot IDs
const robotIds = ['Robot_1','Robot_2','Robot_3','Robot_4']

// 2️⃣ reactive 狀態：包含 Sensor（若有）和四台 Robot
const sensorData = ref({
  Sensor_1: null,
  Sensor_2: null,
  Robot_1: null,
  Robot_2: null,
  Robot_3: null,
  Robot_4: null
})

const chartRecords = ref({
  Sensor_1: [],
  Sensor_2: [],
  Robot_1: [],
  Robot_2: [],
  Robot_3: [],
  Robot_4: []
})

// 3️⃣ helper：只保留最近 30 筆
function addChartData(name, value) {
  if (!chartRecords.value[name]) {
    chartRecords.value[name] = []
  }
  const arr = chartRecords.value[name]
  arr.push({ time: Date.now(), value: parseFloat(value) })
  if (arr.length > 30) arr.shift()
}

let mqttClient = null
const wsClients = {}  // 存放各機器人專屬的 WebSocket

onMounted(() => {
  // ----- MQTT for Sensor -----
  mqttClient = mqtt.connect('ws://localhost:8083/mqtt')
  mqttClient.on('connect', () => {
    mqttClient.subscribe('sensor/temperature')
    mqttClient.subscribe('sensor/humidity')
  })
  mqttClient.on('message', (topic, message) => {
    const v = parseFloat(message.toString())
    if (topic === 'sensor/temperature') {
      sensorData.value.Sensor_1 = v
      addChartData('Sensor_1', v)
    }
    else if (topic === 'sensor/humidity') {
      sensorData.value.Sensor_2 = v
      addChartData('Sensor_2', v)
    }
  })

  // ----- 四條 WebSocket for Robot_1 ~ Robot_4 -----
  robotIds.forEach(id => {
    const ws = new WebSocket(`ws://localhost:8000/ws/opcua/${id}`)
    wsClients[id] = ws

    ws.addEventListener('open', () => {
      console.log(`✅ WS[${id}] connected`)
    })
    ws.addEventListener('message', evt => {
      let data
      try { data = JSON.parse(evt.data) }
      catch { return }
      // 後端若只送單一值也可以： data = { value: 12.3 }
      const val = typeof data === 'object' && data[id] != null
        ? data[id]
        : data.value  // 或 data for uniform endpoint
      if (val != null) {
        sensorData.value[id] = val
        addChartData(id, val)
      }
    })
    ws.addEventListener('error', e => {
      console.error(`⚠️ WS[${id}] error`, e)
    })
    ws.addEventListener('close', () => {
      console.warn(`🚪 WS[${id}] closed`)
    })
  })
})

onBeforeUnmount(() => {
  if (mqttClient) mqttClient.end()
  // 關掉所有 WS
  Object.values(wsClients).forEach(ws => ws.close())
})
</script>



  
  
  