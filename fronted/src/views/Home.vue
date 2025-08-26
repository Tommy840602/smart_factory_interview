<template>
  <div class="home-container">
    <div class="section"><Power /></div>
    <div class="section"><Weather /></div>
    <div class="section"><Earthquake /></div>
    <div class="section"><Ups /></div>
    <div class="section three-section opuca-section">
      <!-- Three.js 主視覺 -->
      <ThreeScene
        :sensorData="sensorData"
        :robotData="robotData"
        :chartRecords="chartRecords"
        @sensor-hover="onSensorHover"
        @robot-hover="onRobotHover"
      />

      <!-- ✅ MQTT 感測圈 hover 顯示即時圖表 -->
      <HoverInfo
        v-if="sensorHover"
        :hoverData="sensorHover"
        :chartRecords="chartRecords"
      />

      <!-- ✅ WebSocket Robot hover 顯示 3 模組表格 -->
      <HoverRobot
        v-if="robotHover"
        :hover="robotHover"
        :robotId="selectedRobotId"
        :records="chartRecordsByType"
      />

      <!-- ✅ MQTT Sensor stream -->
      <SceneWrapper
        @sensor-update="handleSensorUpdate"
        @chart-update="handleChartUpdate"
      />

      <!-- ✅ WebSocket Robot stream -->
      <SceneWrapper2
        @robot-update="handleRobotUpdate"
        @chart-update="handleChartUpdate"
      />
    </div>

    <div class="section"><Classify /></div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

import Power from '@/components/Power.vue'
import Ups from '@/components/Ups.vue'
import Weather from '@/components/Weather.vue'
import Classify from '@/components/Classify.vue'
import Earthquake from '@/components/Earthquake.vue'
import ThreeScene from '@/components/ThreeScene.vue'
import HoverInfo from '@/components/HoverInfo.vue'
import HoverRobot from '@/components/HoverRobot.vue'

import SceneWrapper from '@/pages/SceneWrapper.vue'
import SceneWrapper2 from '@/pages/SceneWrapper2.vue'

// 🧠 狀態容器
const sensorData = ref({})
const robotData = ref({})
const chartRecords = ref({})

const sensorHover = ref(null)
const robotHover = ref(null)
const selectedRobot = ref(null)

// ✅ robot_1_nicla → robot_1
const selectedRobotId = computed(() => {
  return selectedRobot.value ? selectedRobot.value.split('_').slice(0, 2).join('_') : null
})

// ✅ 提取所有 robot 模組的資料，分為 left_arm / right_arm / nicla
const chartRecordsByType = computed(() => {
  if (!selectedRobot.value) return {}
  const result = {
    left_arm: [],
    right_arm: [],
    nicla: [],
  }
  const robotId = selectedRobot.value.split('_').slice(0, 2).join('_')
  for (const key in chartRecords.value) {
    if (key.startsWith(robotId)) {
      const typ = key.split('_')[2]
      if (result[typ]) result[typ] = chartRecords.value[key]
    }
  }
  return result
})

// 🔁 Hover 事件
function onSensorHover(hover) {
  sensorHover.value = hover
}

function onRobotHover(hover) {
  if (!hover || !hover.name?.startsWith('robot_')) {
    robotHover.value = null
    selectedRobot.value = null
  } else {
    robotHover.value = hover
    selectedRobot.value = hover.name
  }
}

// 📡 MQTT ➝ sensor data
function handleSensorUpdate(payload) {
  sensorData.value = { ...sensorData.value, ...payload }
}

// 🌐 WebSocket ➝ robot data
function handleRobotUpdate(payload) {
  robotData.value = { ...robotData.value, ...payload }
}

// 📈 Chart 更新（統一處理 MQTT + WebSocket）
function handleChartUpdate({ name, value }) {
  const records = chartRecords.value[name] || []
  records.push({ time: Date.now(), value })
  if (records.length > 30) records.shift()
  chartRecords.value[name] = records
}
</script>

<style scoped>
.home-container {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
  box-sizing: border-box;
}
.section {
  width: 100%;
  min-height: 200px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}
.three-section {
  min-height: 500px;
  position: relative;
}
.opcua-section {
  border: 2px solid #2196F3;
}
</style>






  
  
  

  
  

  