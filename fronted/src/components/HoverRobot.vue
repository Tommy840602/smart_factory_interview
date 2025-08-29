<template>
  <div v-if="hoverData"
       class="absolute top-6 right-6 bg-white/95 backdrop-blur-md
              rounded-xl shadow-xl p-4 w-[520px] z-50 border border-gray-200 overflow-auto max-h-[600px]">

    <!-- 標題 -->
    <div class="flex justify-between items-center mb-3">
      <h3 class="font-semibold text-gray-800">
        🤖 {{ hoverData.name }} - {{ activeModule }}
      </h3>
      <span class="text-[10px] text-gray-400">
        {{ formatTime(values?.timestamp) }}
      </span>
    </div>

    <!-- 模組切換 -->
    <div class="flex border-b mb-3">
      <button
        v-for="m in modules"
        :key="m"
        @click="activeModule = m"
        class="flex-1 text-center py-1 text-xs font-semibold transition-colors"
        :class="activeModule === m 
          ? 'border-b-2 border-blue-600 text-blue-600' 
          : 'text-gray-500 hover:text-gray-700'"
      >
        {{ m }}
      </button>
    </div>

    <!-- === 顯示區 === -->
    <div v-if="values">

      <!-- ========== NICLA ========== -->
      <div v-if="activeModule === 'nicla'">
        <h4 class="font-bold text-gray-700 mt-2">加速度計 (m/s²)</h4>
        <table class="w-full text-xs mb-2">
          <tbody>
            <tr><td>AccX</td><td>{{ fmt(values.AccX) }}</td></tr>
            <tr><td>AccY</td><td>{{ fmt(values.AccY) }}</td></tr>
            <tr><td>AccZ</td><td>{{ fmt(values.AccZ) }}</td></tr>
          </tbody>
        </table>

        <h4 class="font-bold text-gray-700 mt-2">陀螺儀 (°/s)</h4>
        <table class="w-full text-xs mb-2">
          <tbody>
            <tr><td>GyroX</td><td>{{ fmt(values.GyroX) }}</td></tr>
            <tr><td>GyroY</td><td>{{ fmt(values.GyroY) }}</td></tr>
            <tr><td>GyroZ</td><td>{{ fmt(values.GyroZ) }}</td></tr>
          </tbody>
        </table>

        <h4 class="font-bold text-gray-700 mt-2">磁力計 (μT)</h4>
        <table class="w-full text-xs mb-2">
          <tbody>
            <tr><td>MagX</td><td>{{ fmt(values.MagX) }}</td></tr>
            <tr><td>MagY</td><td>{{ fmt(values.MagY) }}</td></tr>
            <tr><td>MagZ</td><td>{{ fmt(values.MagZ) }}</td></tr>
          </tbody>
        </table>
      </div>

      <!-- ========== LEFT/RIGHT ARM ========== -->
      <div v-else>
        <!-- 一、關節狀態 -->
        <h4 class="font-bold text-gray-700 mt-2">關節狀態 (Joints)</h4>
        <table class="w-full text-xs border-collapse mb-3">
          <thead>
            <tr class="bg-gray-100">
              <th>Joint</th>
              <th>Position (rad)</th>
              <th>Velocity (rad/s)</th>
              <th>Current (A)</th>
              <th>Temp (°C)</th>
              <th>Voltage (V)</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="values['Actual Joint Positions']?.length">
              <tr v-for="i in 6" :key="i" class="border-t">
                <td>J{{ i }}</td>
                <td>{{ fmt(values['Actual Joint Positions']?.[i-1]) }}</td>
                <td>{{ fmt(values['Actual Joint Velocities']?.[i-1]) }}</td>
                <td>{{ fmt(values['Actual Joint Currents']?.[i-1]) }}</td>
                <td :class="tempHigh(values['Temperature of Each Joint']?.[i-1])">
                  {{ fmt(values['Temperature of Each Joint']?.[i-1]) }}
                </td>
                <td>{{ fmt(values['Joint Voltages']?.[i-1]) }}</td>
              </tr>
            </template>
            <tr v-else>
              <td colspan="6" class="text-gray-400 italic text-center">
                No joint data provided
              </td>
            </tr>
          </tbody>
        </table>

        <!-- 二、工具端狀態 -->
        <h4 class="font-bold text-gray-700 mt-2">工具端狀態 (Tool & TCP)</h4>
        <table class="w-full text-xs mb-3">
          <tbody>
            <tr v-if="values['Actual Tool Speed']?.length">
              <td>Tool Speed</td><td class="font-mono">[{{ fmtArray(values['Actual Tool Speed']) }}]</td>
            </tr>
            <tr v-else>
              <td colspan="2" class="text-gray-400 italic text-center">No tool speed data</td>
            </tr>

            <tr><td>Tool Current</td><td>{{ fmt(values['Tool Current']) }} A</td></tr>
            <tr><td>Tool Temperature</td><td :class="tempHigh(values['Tool Temperature'])">{{ fmt(values['Tool Temperature']) }} °C</td></tr>
            <tr><td>TCP Force</td><td>{{ fmt(values['TCP Force']) }} N</td></tr>
          </tbody>
        </table>

        <!-- 三、笛卡爾運動學 -->
        <h4 class="font-bold text-gray-700 mt-2">笛卡爾運動學 (Cartesian / Kinematics)</h4>
        <table class="w-full text-xs mb-3">
          <tbody>
            <template v-if="values['Actual Cartesian Coordinates']?.length">
              <tr><td>Cartesian Coordinates</td><td class="font-mono">[{{ fmtArray(values['Actual Cartesian Coordinates']) }}]</td></tr>
              <tr><td>Elbow Position</td><td>[{{ fmtArray(values['Elbow Position']) }}]</td></tr>
              <tr><td>Elbow Velocity</td><td>[{{ fmtArray(values['Elbow Velocity']) }}]</td></tr>
              <tr><td>Tool Acceleration</td><td>[{{ fmtArray(values['Tool Acceleration']) }}]</td></tr>
            </template>
            <tr v-else>
              <td colspan="2" class="text-gray-400 italic text-center">
                No Cartesian / Kinematics data provided
              </td>
            </tr>
          </tbody>
        </table>

        <!-- 四、狀態監控 -->
        <h4 class="font-bold text-gray-700 mt-2">狀態監控 (Status)</h4>
        <table class="w-full text-xs mb-3">
          <tbody>
            <tr v-if="values['Generalized Forces']?.length">
              <td>Generalized Forces</td><td>[{{ fmtArray(values['Generalized Forces']) }}]</td>
            </tr>
            <tr v-else>
              <td colspan="2" class="text-gray-400 italic text-center">No force data</td>
            </tr>

            <tr><td>Norm Cartesian Momentum</td><td>{{ fmt(values['Norm of Cartesian Linear Momentum']) }}</td></tr>
            <tr><td>Robot Current</td><td>{{ fmt(values['Robot Current']) }} A</td></tr>
            <tr><td>Safety Status</td><td>{{ values['Safety Status'] }}</td></tr>
            <tr><td>Anomaly State</td><td :class="anomalyHigh(values['Anomaly State'])">{{ values['Anomaly State'] }}</td></tr>
            <tr><td>Execution Time</td><td>{{ fmt(values['Execution Time']) }} s</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 沒資料 -->
    <div v-else class="text-gray-400 text-xs text-center py-4">
      No data available
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  hoverData: { type: Object, default: null },
  robotData: { type: Object, default: () => ({}) }
})

const modules = ['nicla','left_arm','right_arm']
const activeModule = ref('nicla')

// 自動跟隨 hoverData.module
watch(() => props.hoverData?.module, (m) => {
  if (m && modules.includes(m)) activeModule.value = m
}, { immediate: true })

// === normalize (_1,_2 → array) ===
function normalizeValues(raw) {
  if (!raw) return {}
  const vals = { ...raw }
  const groupFields = [
    "Actual Joint Positions",
    "Actual Joint Velocities",
    "Actual Joint Currents",
    "Temperature of Each Joint",
    "Joint Voltages",
    "Actual Cartesian Coordinates",
    "Actual Tool Speed",
    "Generalized Forces",
    "Elbow Position",
    "Elbow Velocity",
    "Tool Acceleration"
  ]
  for (const base of groupFields) {
    const arr = []
    let found = false
    for (let i = 1; i <= 12; i++) {
      const key = `${base}_${i}`
      if (key in vals) {
        arr.push(vals[key])
        delete vals[key]
        found = true
      }
    }
    if (Array.isArray(vals[base])) {
      arr.push(...vals[base]); found = true
    }
    if (typeof vals[base] === "number") {
      arr.push(vals[base]); found = true
    }
    if (found) vals[base] = arr
  }
  return vals
}

const values = computed(() => {
  if (!props.hoverData?.name) return null
  const key = `${props.hoverData.name.toLowerCase()}_${activeModule.value}`
  return normalizeValues(props.robotData[key] || props.hoverData.values || null)
})

function fmt(v) {
  if (v === undefined || v === null) return '--'
  return typeof v === 'number' ? v.toFixed(3) : v
}
function fmtArray(arr) {
  if (!arr || arr.length === 0) return '--'
  return arr.map(x => fmt(x)).join(', ')
}
function tempHigh(v) {
  return (typeof v === 'number' && v > 70) ? 'text-red-500 font-bold' : ''
}
function anomalyHigh(v) {
  return v === 1 ? 'text-red-600 font-bold' : ''
}
function formatTime(ts) {
  if (!ts) return ''
  try { return new Date(ts).toLocaleTimeString() }
  catch { return ts }
}
</script>













































  
  