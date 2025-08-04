<template>
  <div class="scene-wrapper">
    <!-- 此處不再直接渲染 ThreeScene，而是交給 Home.vue -->
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import mqtt from 'mqtt'

const emit = defineEmits(['sensor-update', 'chart-update'])

const SENSOR_IDS = ['Sensor_1', 'Sensor_2']
const MQTT_URL = 'ws://localhost:8083/mqtt'
const MAX_CHART_RECORDS = 30

const sensorData = ref(
  Object.fromEntries(SENSOR_IDS.map(id => [id, null]))
)
const chartRecords = ref(
  Object.fromEntries(SENSOR_IDS.map(id => [id, []]))
)

let mqttClient = null

function addChartRecord(id, value) {
  const records = chartRecords.value[id]
  records.push({ time: Date.now(), value })
  if (records.length > MAX_CHART_RECORDS) records.shift()

  // 傳給 Home.vue 做 chartRecords 整合
  emit('chart-update', { name: id, value })
}

function handleMqttMessage(topic, message) {
  const value = parseFloat(message.toString())
  if (isNaN(value)) return

  const id = topic.includes('temperature') ? 'Sensor_1'
           : topic.includes('humidity')    ? 'Sensor_2'
           : null

  if (!id) return
  sensorData.value[id] = value
  addChartRecord(id, value)

  // 即時更新給 Home.vue
  emit('sensor-update', { [id]: value })
}

function initMqtt() {
  mqttClient = mqtt.connect(MQTT_URL)

  mqttClient.on('connect', () => {
    console.log('✅ MQTT connected')
    mqttClient.subscribe('sensor/temperature')
    mqttClient.subscribe('sensor/humidity')
  })

  mqttClient.on('message', handleMqttMessage)
  mqttClient.on('error', (e) => {
    console.error('❌ MQTT error:', e)
  })
}

onMounted(() => {
  initMqtt()
})

onBeforeUnmount(() => {
  if (mqttClient) mqttClient.end()
})
</script>

<style scoped>
.scene-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
}
</style>







  
  
  