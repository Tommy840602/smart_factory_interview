<!-- src/pages/SceneWrapperMultiWS.vue -->
<template>
  <div class="connection-status">
    <div v-for="id in ROBOT_IDS" :key="id" :class="['status-indicator', connectionStatus[id]]">
      {{ id }}: {{ connectionStatus[id] }}
    </div>
  </div>
  <ThreeScene
    :sensorData="sensorData"
    :chartRecords="chartRecords"
  />
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import ThreeScene from '@/components/ThreeScene.vue'
import mqtt from 'mqtt'

// Constants
const ROBOT_IDS = ['Robot_1', 'Robot_2', 'Robot_3', 'Robot_4']
const SENSOR_IDS = ['Sensor_1', 'Sensor_2']
const MAX_CHART_RECORDS = 30
const WS_RECONNECT_DELAY = 5000 // Base reconnect delay
const MQTT_URL = 'ws://localhost:8083/mqtt'
const WS_BASE_URL = 'ws://localhost:8000/ws/opcua'
const HEARTBEAT_INTERVAL = 30000 // 30 seconds

// Reactive data
const sensorData = ref({
  ...Object.fromEntries(SENSOR_IDS.map(id => [id, null])),
  ...Object.fromEntries(ROBOT_IDS.map(id => [id, null]))
})

const chartRecords = ref({
  ...Object.fromEntries(SENSOR_IDS.map(id => [id, []])),
  ...Object.fromEntries(ROBOT_IDS.map(id => [id, []]))
})

const connectionStatus = ref(Object.fromEntries(ROBOT_IDS.map(id => [id, 'disconnected'])))
const wsClients = ref({})
const mqttClient = ref(null)

/**
 * Add data to chart records with validation
 */
function addChartData(name, value) {
  if (!chartRecords.value[name]) {
    console.warn(`⚠️ Unknown data source: ${name}`)
    return
  }

  const parsedValue = parseFloat(value)
  if (isNaN(parsedValue)) {
    console.warn(`⚠️ Invalid value for ${name}:`, value)
    return
  }

  const records = chartRecords.value[name]
  records.push({ time: Date.now(), value: parsedValue })
  
  if (records.length > MAX_CHART_RECORDS) {
    records.shift()
  }
}

/**
 * Extract value from data object with fallback keys
 */
function extractValue(data, id) {
  const keysToTry = [
    `ns=2;s=${id.toLowerCase()}_left_arm_Timestamp`,
    `ns=2;s=${id.toLowerCase()}_Timestamp`,
    `ns=2;s=${id}_Timestamp`,
    id,
    id.toLowerCase(),
    'value'
  ]
  
  for (const key of keysToTry) {
    if (data[key] !== undefined && data[key] !== null) {
      const val = parseFloat(data[key])
      if (!isNaN(val)) return val
    }
  }
  return null
}

/**
 * Handle WebSocket messages with robust error handling
 */
 function handleWsMessage(id) {
  return (evt) => {
    try {
      // Handle server error messages
      if (typeof evt.data === 'string' && (evt.data.includes('WebSocket 錯誤') || evt.data.includes('Error parsing'))) {
        try {
          const errorData = JSON.parse(evt.data)
          if (errorData.error) {
            console.error(`❌ WS[${id}] server error:`, errorData.error)
            connectionStatus.value[id] = 'error'
            // 添加 toast 提示
            Vue.prototype.$toast.error(`Robot ${id} 連線失敗: ${errorData.error}`, { timeout: 5000 })
            return
          }
        } catch (e) {
          console.error(`⚠️ WS[${id}] error message parse failed:`, evt.data)
          Vue.prototype.$toast.error(`Robot ${id} 訊息解析失敗: ${evt.data}`, { timeout: 5000 })
        }
        return
      }

      let data
      try {
        // Handle both key:value and JSON formats
        if (typeof evt.data === 'string' && evt.data.includes(':')) {
          const [key, value] = evt.data.split(':')
          data = { [key.trim()]: value.trim() }
        } else {
          data = JSON.parse(evt.data)
        }
      } catch (e) {
        console.error(`⚠️ WS[${id}] parse error:`, e)
        Vue.prototype.$toast.error(`Robot ${id} 資料解析錯誤`, { timeout: 5000 })
        return
      }

      if (data.error) {
        console.warn(`⚠️ WS[${id}] error from server:`, data.error)
        connectionStatus.value[id] = 'error'
        Vue.prototype.$toast.error(`Robot ${id} 伺服器錯誤: ${data.error}`, { timeout: 5000 })
        return
      }

      const val = extractValue(data, id)
      
      if (val !== null) {
        sensorData.value[id] = val
        addChartData(id, val)
        connectionStatus.value[id] = 'connected'
      } else {
        console.warn(`⚠️ No valid value found for ${id}:`, data)
      }
    } catch (error) {
      console.error(`⚠️ WS[${id}] unexpected error in message handler:`, error)
      Vue.prototype.$toast.error(`Robot ${id} 訊息處理錯誤`, { timeout: 5000 })
    }
  }
}

/**
 * Initialize WebSocket connection with heartbeat
 */
 function initWebSocket(id) {
  // Skip if already connected/connecting
  if (wsClients.value[id] && [WebSocket.OPEN, WebSocket.CONNECTING].includes(wsClients.value[id].readyState)) {
    return
  }

  connectionStatus.value[id] = 'connecting'
  const ws = new WebSocket(`${WS_BASE_URL}/${id}`)
  wsClients.value[id] = ws

  let heartbeatInterval

  ws.addEventListener('open', () => {
    console.log(`✅ WS[${id}] connected`)
    connectionStatus.value[id] = 'connected'
    Vue.prototype.$toast.success(`Robot ${id} 已連線`, { timeout: 3000 })
    
    // Setup heartbeat
    heartbeatInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'heartbeat' }))
      }
    }, HEARTBEAT_INTERVAL)
  })

  ws.addEventListener('message', handleWsMessage(id))

  ws.addEventListener('error', (e) => {
    console.error(`⚠️ WS[${id}] error:`, e)
    connectionStatus.value[id] = 'error'
    Vue.prototype.$toast.error(`Robot ${id} 連線錯誤`, { timeout: 5000 })
  })

  ws.addEventListener('close', () => {
    console.warn(`🚪 WS[${id}] closed`)
    connectionStatus.value[id] = 'disconnected'
    Vue.prototype.$toast.warning(`Robot ${id} 連線已關閉`, { timeout: 5000 })
    if (heartbeatInterval) clearInterval(heartbeatInterval)
    
    // Longer delay for Robot_3 due to known issues
    const delay = id === 'Robot_3' ? 10000 : WS_RECONNECT_DELAY
    setTimeout(() => initWebSocket(id), delay)
  })
}

/**
 * Initialize MQTT connection
 */
function initMqtt() {
  mqttClient.value = mqtt.connect(MQTT_URL)
  
  mqttClient.value.on('connect', () => {
    console.log('✅ MQTT connected')
    mqttClient.value.subscribe('sensor/temperature')
    mqttClient.value.subscribe('sensor/humidity')
  })

  mqttClient.value.on('message', (topic, message) => {
    const value = parseFloat(message.toString())
    if (isNaN(value)) {
      console.warn(`⚠️ Invalid MQTT value from ${topic}:`, message.toString())
      return
    }

    const sensorId = topic === 'sensor/temperature' ? 'Sensor_1' : 'Sensor_2'
    sensorData.value[sensorId] = value
    addChartData(sensorId, value)
  })

  mqttClient.value.on('error', (e) => {
    console.error('❌ MQTT error:', e)
  })
}

// Component lifecycle
onMounted(() => {
  initMqtt()
  ROBOT_IDS.forEach(initWebSocket)
})

onBeforeUnmount(() => {
  if (mqttClient.value) {
    mqttClient.value.end()
  }
  
  Object.values(wsClients.value).forEach(ws => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.close()
    }
  })
})
</script>

<style scoped>
.connection-status {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(0,0,0,0.7);
  padding: 10px;
  border-radius: 5px;
  color: white;
  z-index: 100;
}

.status-indicator {
  margin: 5px 0;
  padding: 3px 6px;
  border-radius: 3px;
}

.status-indicator.connected {
  background: #4CAF50;
}

.status-indicator.connecting {
  background: #FFC107;
}

.status-indicator.disconnected {
  background: #F44336;
}

.status-indicator.error {
  background: #9C27B0;
}
</style>



  
  
  