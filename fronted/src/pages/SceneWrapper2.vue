<template>
  <div class="scene-wrapper2">
    <!-- 不渲染模型與圖，只作為資料傳輸模組 -->
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

// 傳送給父層事件：資料更新、圖表更新、hover
const emit = defineEmits(['robot-update', 'chart-update', 'robot-hover'])

// 機器人 ID 與子模組類型
const ROBOT_IDS = ['robot_1', 'robot_2', 'robot_3', 'robot_4']
const TYPES = ['nicla', 'left_arm', 'right_arm']
const MAX_RECORDS = 30
const WS_BASE = 'ws://localhost:8000/ws/opcua'

const robotData = ref({})      // ex: robot_1_left_arm
const robotCharts = ref({})    // ex: robot_2_nicla
const wsClients = ref({})      // 儲存各 WebSocket 實例

// 新增即時圖表記錄
function addChart(key, val) {
  if (!robotCharts.value[key]) robotCharts.value[key] = []
  const records = robotCharts.value[key]
  records.push({ time: Date.now(), value: val })
  if (records.length > MAX_RECORDS) records.shift()
  emit('chart-update', { name: key, value: val })
}

// 建立 WebSocket 連線（分流：robot_id + type）
function initWS(robotId, typ) {
  const key = `${robotId}_${typ}`
  if (wsClients.value[key]) return

  const ws = new WebSocket(`${WS_BASE}/${robotId}/${typ}`)
  wsClients.value[key] = ws

  ws.onmessage = (e) => {
    let data
    try {
      data = JSON.parse(e.data)
    } catch (err) {
      console.error(`❌ Parse error [${key}]:`, err)
      return
    }

    const val = data?.value ?? Object.values(data)[0]
    if (!isNaN(val)) {
      robotData.value[key] = val
      emit('robot-update', { [key]: val })
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

// 接收 hover payload（未啟用：可保留）
function handleRobotHover(payload) {
  const { id, x, y } = payload
  if (!id || !robotData.value[id]) {
    emit('robot-hover', null)
    return
  }

  emit('robot-hover', {
    name: id,
    label: `Robot ${id}`,
    value: robotData.value[id],
    x,
    y
  })
}

// 建立所有 WebSocket 連線
onMounted(() => {
  for (const id of ROBOT_IDS) {
    for (const typ of TYPES) {
      initWS(id, typ)
    }
  }
})

// 卸載時斷開所有連線
onBeforeUnmount(() => {
  Object.values(wsClients.value).forEach(ws => ws?.close())
})
</script>

<style scoped>
.scene-wrapper2 {
  width: 100%;
  height: 100%;
  position: relative;
}
</style>




  
  







  
  





  
  