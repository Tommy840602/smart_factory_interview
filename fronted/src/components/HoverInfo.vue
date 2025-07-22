<template>
  <div
    v-if="hoverData?.name && (hoverData.name.includes('Sensor') || hoverData.name.includes('Robot'))"
    class="chart-container"
    :style="{ left: `${hoverData.x}px`, top: `${hoverData.y - 100}px` }"
  >
    <div class="chart-title">{{ latestLabel }}</div>
    <canvas ref="chartCanvas" width="300" height="150"></canvas>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import Chart from 'chart.js/auto'
import annotationPlugin from 'chartjs-plugin-annotation'
Chart.register(annotationPlugin)

type RawRecord = { time: number; value: number }

//const props = defineProps<{ hoverData: { name?: string; x: number; y: number }; chartRecords: Record<string, RawRecord[]> | Map<string, RawRecord[]> }>()
const props = defineProps({
hoverData: {
  type: Object,
  default: null
},
chartRecords: {
  type: Object,
  required: true
}
})

const chartCanvas = ref<HTMLCanvasElement | null>(null)
let chartInstance: Chart | null = null

// 讀資料時先兼容 Map 和 Object
function getRaw(name?: string): RawRecord[] {
  if (!name || !props.chartRecords) return []
  if (props.chartRecords instanceof Map) {
    return props.chartRecords.get(name) || []
  }
  return props.chartRecords[name] || []
}

const latestLabel = computed(() => {
  const name = props.hoverData?.name
  const raw = getRaw(name)
  if (!name || !raw.length) return ''
  const lastVal = raw[raw.length - 1].value

  let type = ''
  let unit = ''
  if (name.startsWith('Sensor_')) {
    type = name === 'Sensor_1' ? 'Temperature' : 'Humidity'
    unit = name === 'Sensor_2' ? '%' : '°C'
  } else if (name.startsWith('Robot_')) {
    type = 'Robot Data'
    unit = ''
  }

  return `${name}${type ? ` (${type})` : ''}: ${
    isNaN(lastVal) ? '--' : lastVal.toFixed(1)
  }${unit}`
})

function drawChart() {
  const name = props.hoverData?.name
  const raw = getRaw(name)
  if (!name || !raw.length || !chartCanvas.value) return

  const dataPoints = raw
    .map(r => ({ time: new Date(r.time), v: r.value }))
    .filter(dp => !isNaN(dp.v))
    .sort((a, b) => a.time.getTime() - b.time.getTime())
  if (!dataPoints.length) return

  const labels = dataPoints.map(dp => dp.time.toLocaleTimeString())
  const values = dataPoints.map(dp => dp.v)
  const mean = values.reduce((a, b) => a + b, 0) / values.length
  const std = Math.sqrt(values.reduce((a, b) => a + (b - mean) ** 2, 0) / values.length)
  const LCL = mean - 3 * std
  const UCL = mean + 3 * std

  if (chartInstance) {
    chartInstance.destroy()
    chartCanvas.value.getContext('2d')?.clearRect(0, 0, chartCanvas.value.width, chartCanvas.value.height)
  }

  chartInstance = new Chart(chartCanvas.value.getContext('2d')!, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: name.startsWith('Sensor_')
            ? name === 'Sensor_1'
              ? 'Temperature (°C)'
              : 'Humidity (%)'
            : name,
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
        y: { min: Math.min(LCL, ...values) - 1, max: Math.max(UCL, ...values) + 1 },
        x: {}
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

watch(
  () => props.hoverData?.name,
  () => drawChart()
)

watch(
  () => getRaw(props.hoverData?.name),
  () => drawChart(),
  { deep: true }
)
</script>

<style scoped>
.chart-container {
  position: absolute;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 6px;
  padding: 8px;
  max-width: 320px;
  max-height: 200px;
  overflow: hidden;
  box-shadow: 0 0 12px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(0, 0, 0, 0.05);
  z-index: 2000;
  transform: translate(-50%, 0);
}

.chart-title {
  font-weight: bold;
  margin-bottom: 4px;
  text-align: center;
  font-size: 14px;
}
</style>






  