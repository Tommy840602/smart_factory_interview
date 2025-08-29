<template>
  <!-- 只顯示 Sensor hover，不處理 Robot -->
  <div
    v-if="hoverData?.name && hoverData.name.includes('Sensor')"
    class="chart-container"
    :style="{ left: `${leftPos}px`, top: `${topPos}px` }"
  >
    <div class="chart-title">{{ latestLabel }}</div>
    <canvas ref="chartCanvas" width="280" height="120"></canvas>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import Chart from 'chart.js/auto'
import annotationPlugin from 'chartjs-plugin-annotation'
Chart.register(annotationPlugin)

type RawRecord = { time: number; value: number }

const props = defineProps({
  hoverData: { type: Object, default: null },
  chartRecords: { type: Object, required: true }
})

const chartCanvas = ref<HTMLCanvasElement | null>(null)
let chartInstance: Chart | null = null

// --- 動態位置（避免超出視窗）
const leftPos = computed(() => {
  const x = props.hoverData?.x || 0
  return Math.min(window.innerWidth - 320, x)
})
const topPos = computed(() => {
  const y = props.hoverData?.y || 0
  return Math.max(20, y - 160)
})

// --- 資料存取：兼容 Map / Object
function getRaw(name?: string): RawRecord[] {
  if (!name || !props.chartRecords) return []
  if (props.chartRecords instanceof Map) {
    return props.chartRecords.get(name) || []
  }
  return props.chartRecords[name] || []
}

const latestLabel = computed(() => {
  const name = props.hoverData?.name
  const raw = getRaw(name).slice(-30) // 只取最近 30 筆
  if (!name || !raw.length) return ''
  const lastVal = raw[raw.length - 1].value

  let type = ''
  let unit = ''
  if (name === 'Sensor_1') {
    type = 'Temperature'
    unit = '°C'
  } else if (name === 'Sensor_2') {
    type = 'Humidity'
    unit = '%'
  }

  return `${name}${type ? ` (${type})` : ''}: ${
    isNaN(lastVal) ? '--' : lastVal.toFixed(1)
  }${unit}`
})

function drawChart() {
  const name = props.hoverData?.name
  const raw = getRaw(name).slice(-30)
  if (!name || !raw.length || !chartCanvas.value) return

  const dataPoints = raw
    .map(r => ({ time: new Date(r.time), v: r.value }))
    .filter(dp => !isNaN(dp.v))

  if (!dataPoints.length) return

  const labels = dataPoints.map(dp => dp.time.toLocaleTimeString())
  const values = dataPoints.map(dp => dp.v)

  const mean = values.reduce((a, b) => a + b, 0) / values.length
  const std = Math.sqrt(values.reduce((a, b) => a + (b - mean) ** 2, 0) / values.length)
  const LCL = mean - 3 * std
  const UCL = mean + 3 * std

  if (chartInstance) chartInstance.destroy()

  chartInstance = new Chart(chartCanvas.value.getContext('2d')!, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: name === 'Sensor_1' ? 'Temperature (°C)' : 'Humidity (%)',
          data: values,
          tension: 0.25,
          pointRadius: values.map(v => (v > UCL || v < LCL ? 4 : 2)),
          pointBackgroundColor: values.map(v => (v > UCL || v < LCL ? 'red' : 'blue'))
        }
      ]
    },
    options: {
      responsive: false,
      animation: false,
      scales: {
        y: { min: Math.min(LCL, ...values) - 1, max: Math.max(UCL, ...values) + 1 }
      },
      plugins: {
        legend: { display: false },
        annotation: {
          annotations: {
            meanLine: { type: 'line', yMin: mean, yMax: mean, borderColor: 'green', borderDash: [5, 5] },
            UCL: { type: 'line', yMin: UCL, yMax: UCL, borderColor: 'red' },
            LCL: { type: 'line', yMin: LCL, yMax: LCL, borderColor: 'red' }
          }
        }
      }
    }
  })
}

watch(() => props.hoverData?.name, () => drawChart())
watch(() => getRaw(props.hoverData?.name), () => drawChart(), { deep: true })
</script>

<style scoped>
.chart-container {
  position: absolute;
  background: rgba(0, 0, 0, 0.85);
  color: white;
  border-radius: 6px;
  padding: 6px;
  max-width: 300px;
  max-height: 180px;
  overflow: hidden;
  box-shadow: 0 0 8px rgba(0, 0, 0, 0.3);
  z-index: 2000;
  transform: translate(-50%, 0);
}

.chart-title {
  font-weight: 600;
  margin-bottom: 4px;
  text-align: center;
  font-size: 13px;
}
</style>
















  