<template>
  <div class="scene-wrapper2">
    <!-- 不渲染模型與圖，只作為資料傳輸模組 -->
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const emit = defineEmits(['robot-update', 'chart-update', 'robot-hover'])

const ROBOT_IDS = ['robot_1', 'robot_2', 'robot_3', 'robot_4']
const TYPES = ['nicla', 'left_arm', 'right_arm']
const MAX_RECORDS = 30
const WS_BASE = 'ws://localhost:8000/ws/robot'

const robotData = ref({})
const robotCharts = ref({})
const wsClients = ref({})

// --- 新增即時圖表記錄 ---
function addChart(key, val) {
  if (!robotCharts.value[key]) robotCharts.value[key] = []
  const records = robotCharts.value[key]
  records.push({ time: Date.now(), value: val })
  if (records.length > MAX_RECORDS) records.shift()
  emit('chart-update', { name: key, value: val })
}

// --- 建立 WebSocket ---
function initWS(robotId, typ) {
  const key = `${robotId}_${typ}`
  if (wsClients.value[key]) return

  console.log(`🔗 Connecting WS: ${WS_BASE}/${robotId}/${typ}`)
  const ws = new WebSocket(`${WS_BASE}/${robotId}/${typ}`)
  wsClients.value[key] = ws

  ws.onopen = () => {
    console.log(`✅ WS opened: ${robotId}/${typ}`)
  }

  ws.onmessage = (e) => {
    let packet
    try {
      packet = JSON.parse(e.data)
    } catch (err) {
      console.error(`❌ Parse error [${key}]:`, err)
      return
    }
    console.log(`📦 [${key}]`, packet)

    const values = packet?.data
    if (!values) return

    // ✅ 儲存完整 data
    robotData.value[key] = values

    // 🚀 emit 出完整一筆 { robotId, module, values }
    emit('robot-update', { [key]: values })

    // 🎯 Chart 預設用 AccX (若存在)
    const val = values.AccX ?? Object.values(values).find(v => typeof v === 'number')
    if (!isNaN(val)) {
      addChart(key, val)
    }
  }

  ws.onclose = () => {
    console.warn(`🔌 WS closed: ${key}, retrying in 5s`)
    setTimeout(() => initWS(robotId, typ), 5000)
  }

  ws.onerror = (err) => {
    console.error(`❌ WS error [${key}]:`, err)
  }
}

// --- 接收 ThreeScene 發來的 hover ---
function handleRobotHover(payload) {
  const { id, module, x, y } = payload
  const key = `${id}_${module || 'nicla'}` // 預設 nicla
  const values = robotData.value[key]

  if (!id || !values) {
    emit('robot-hover', null)
    return
  }

  // ✅ 一定帶 values 出去
  console.log("handleRobotHover emit:", { id, module, values })
  emit('robot-hover', {
    name: id,
    module: module || 'nicla',
    values,
    x,
    y
  })
}

onMounted(() => {
  for (const id of ROBOT_IDS) {
    for (const typ of TYPES) {
      initWS(id, typ)
    }
  }
})

onBeforeUnmount(() => {
  Object.keys(wsClients.value).forEach(k => {
    wsClients.value[k]?.close()
    delete wsClients.value[k]
  })
})
</script>

<style scoped>
.scene-wrapper2 {
  width: 100%;
  height: 100%;
  position: relative;
}
</style>













  
  







  
  





  
  