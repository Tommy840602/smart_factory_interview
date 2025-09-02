<template>
  <div
    v-if="hoverData"
    class="hover-card"
    :style="{ top: pos.y + 'px', left: pos.x + 'px' }"
    @mousedown.stop
  >
    <!-- 標題列 -->
    <div
      class="flex justify-between items-center mb-2 cursor-move select-none"
      @mousedown="startDrag"
    >
    <button
          @click="toggleCollapse"
          class="px-2 py-0.5 text-xs bg-gray-200 hover:bg-gray-300 rounded"
        >
          {{ collapsed ? "＋" : "－" }}
        </button>
      <h3 class="font-semibold text-gray-800 text-sm">
        🤖 {{ hoverData.name }} - {{ activeModule }}
      </h3>
      <div class="flex space-x-1">
      </div>
    </div>

    <!-- 縮小模式只顯示標題 -->
    <div v-if="collapsed" class="text-xs text-gray-500">
      (已縮小，點擊＋展開)
    </div>

    <!-- 內容區 -->
    <div v-else>
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
        <!-- NICLA -->
        <div v-if="activeModule === 'nicla'">
          <h4 class="font-bold text-gray-700 mt-2">加速度計 (m/s²)</h4>
          <table class="w-full text-xs mb-2">
            <tbody>
              <tr><td>AccX</td><td class="font-mono text-right">{{ fmt(values.AccX) }}</td></tr>
              <tr><td>AccY</td><td class="font-mono text-right">{{ fmt(values.AccY) }}</td></tr>
              <tr><td>AccZ</td><td class="font-mono text-right">{{ fmt(values.AccZ) }}</td></tr>
            </tbody>
          </table>
          <h4 class="font-bold text-gray-700 mt-2">陀螺儀 (°/s)</h4>
          <table class="w-full text-xs mb-2">
            <tbody>
              <tr><td>GyroX</td><td class="font-mono text-right">{{ fmt(values.GyroX) }}</td></tr>
              <tr><td>GyroY</td><td class="font-mono text-right">{{ fmt(values.GyroY) }}</td></tr>
              <tr><td>GyroZ</td><td class="font-mono text-right">{{ fmt(values.GyroZ) }}</td></tr>
            </tbody>
          </table>
          <h4 class="font-bold text-gray-700 mt-2">磁力計 (μT)</h4>
          <table class="w-full text-xs mb-2">
            <tbody>
              <tr><td>MagX</td><td class="font-mono text-right">{{ fmt(values.MagX) }}</td></tr>
              <tr><td>MagY</td><td class="font-mono text-right">{{ fmt(values.MagY) }}</td></tr>
              <tr><td>MagZ</td><td class="font-mono text-right">{{ fmt(values.MagZ) }}</td></tr>
            </tbody>
          </table>
        </div>

        <!-- ARM -->
        <div v-else>
          <h4 class="font-bold text-gray-700 mt-2">關節狀態 (Joints)</h4>
          <table class="w-full text-xs border-collapse mb-3">
            <thead>
              <tr class="bg-gray-100">
                <th>Joint</th>
                <th>Pos</th>
                <th>Vel</th>
                <th>Curr</th>
                <th>Temp</th>
                <th>Volt</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="i in 6" :key="i" class="border-t">
                <td>J{{ i }}</td>
                <td class="font-mono text-right">{{ fmt(values['Actual Joint Positions']?.[i-1]) }}</td>
                <td class="font-mono text-right">{{ fmt(values['Actual Joint Velocities']?.[i-1]) }}</td>
                <td class="font-mono text-right">{{ fmt(values['Actual Joint Currents']?.[i-1]) }}</td>
                <td :class="tempHigh(values['Temperature of Each Joint']?.[i-1])">
                  {{ fmt(values['Temperature of Each Joint']?.[i-1]) }}
                </td>
                <td class="font-mono text-right">{{ fmt(values['Joint Voltages']?.[i-1]) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-else class="text-gray-400 text-xs text-center py-4">
        No data available
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from "vue"

const props = defineProps({
  hoverData: { type: Object, default: null },
  robotData: { type: Object, default: () => ({}) }
})

const modules = ["nicla", "left_arm", "right_arm"]
const activeModule = ref("nicla")
const collapsed = ref(false)

// 拖曳座標
const pos = ref({ x: window.innerWidth - 550, y: 80 })
let dragging = false
let offset = { x: 0, y: 0 }

function startDrag(e) {
  dragging = true
  offset.x = e.clientX - pos.value.x
  offset.y = e.clientY - pos.value.y
  window.addEventListener("mousemove", onDrag)
  window.addEventListener("mouseup", stopDrag)
}
function onDrag(e) {
  if (!dragging) return
  pos.value.x = e.clientX - offset.x
  pos.value.y = e.clientY - offset.y
}
function stopDrag() {
  dragging = false
  window.removeEventListener("mousemove", onDrag)
  window.removeEventListener("mouseup", stopDrag)
}

// toggle collapse
function toggleCollapse() {
  collapsed.value = !collapsed.value
}

// Watch module
watch(() => props.hoverData?.module, (m) => {
  if (m && modules.includes(m)) activeModule.value = m
}, { immediate: true })

// values 計算
function normalizeValues(raw) {
  if (!raw) return {}
  const vals = { ...raw }
  const groupFields = [
    "Actual Joint Positions", "Actual Joint Velocities", "Actual Joint Currents",
    "Temperature of Each Joint", "Joint Voltages", "Actual Cartesian Coordinates",
    "Actual Tool Speed", "Generalized Forces", "Elbow Position",
    "Elbow Velocity", "Tool Acceleration"
  ]
  for (const base of groupFields) {
    const arr = []
    for (let i = 1; i <= 12; i++) {
      const key = `${base}_${i}`
      if (key in vals) { arr.push(vals[key]); delete vals[key] }
    }
    if (Array.isArray(vals[base])) arr.push(...vals[base])
    if (typeof vals[base] === "number") arr.push(vals[base])
    if (arr.length) vals[base] = arr
  }
  return vals
}
const values = computed(() => {
  if (!props.hoverData?.name) return null
  const key = `${props.hoverData.name.toLowerCase()}_${activeModule.value}`
  return normalizeValues(props.robotData[key] || props.hoverData.values || null)
})

// 格式化工具
function fmt(v) { return (v === undefined || v === null) ? "--" : (typeof v === "number" ? v.toFixed(3) : v) }
function fmtArray(arr) { return (!arr || !arr.length) ? "--" : arr.map(x => fmt(x)).join(", ") }
function tempHigh(v) { return (typeof v === "number" && v > 70) ? "text-red-500 font-bold" : "" }
</script>

<style scoped>
.hover-card {
  position: absolute;
  z-index: 9999;
  width: 520px;
  max-height: 600px;
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(6px);
  border-radius: 0.75rem;
  box-shadow: 0 4px 16px rgba(0,0,0,0.2);
  border: 1px solid #e5e7eb; /* gray-200 */
  padding: 0.75rem;
}
</style>


