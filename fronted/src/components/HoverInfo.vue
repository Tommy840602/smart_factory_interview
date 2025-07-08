<template>
  <div
    v-if="hoverData?.name?.includes('Sensor')"
    class="chart-container"
    :style="{
      left: `${hoverData.x}px`, top: `${hoverData.y - 160}px`
    }"
  >
    <!-- 顯示最新名稱＋數值於上方 -->
    <div class="chart-title">
      {{ latestLabel }}
    </div>
    <canvas ref="chartCanvas" width="300" height="150"></canvas>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import Chart from 'chart.js/auto'
import annotationPlugin from 'chartjs-plugin-annotation'
Chart.register(annotationPlugin)

const props = defineProps({ hoverData: Object, chartRecords: Object })

const chartCanvas = ref(null)
let chartInstance = null

// 計算最新標籤文字：名稱＋數值＋單位
const latestLabel = computed(() => {
  const name = props.hoverData?.name
  const raw = props.chartRecords?.get(name) || []
  if (!name || !raw.length) return ''
  const lastVal = parseFloat(raw[raw.length - 1].value)
  
  let type = ''
  const unit = '°C' // Default unit for Sensor_1
  
  if (name === 'Sensor_1') {
    type = 'Temperature'
  } else if (name === 'Sensor_2') {
    type = 'Humidity'
  }
  
  return `${name} (${type}): ${isNaN(lastVal) ? '--' : lastVal.toFixed(1)}${unit}`
})

function drawChart() {
  const name = props.hoverData?.name
  const raw = props.chartRecords?.get(name) || []
  if (!name || !raw.length || !chartCanvas.value) return

  // 處理資料：轉型、過濾、排序
  const dataPoints = raw
    .map(r => ({ time: new Date(r.time), v: parseFloat(r.value) }))
    .filter(dp => !isNaN(dp.v))
    .sort((a, b) => a.time - b.time)
  if (!dataPoints.length) return

  const labels = dataPoints.map(dp => dp.time.toLocaleTimeString())
  const values = dataPoints.map(dp => dp.v)

  // 統計
  const mean = values.reduce((a, b) => a + b, 0) / values.length
  const std = Math.sqrt(values.reduce((a, b) => a + (b - mean) ** 2, 0) / values.length)
  const LCL = mean - 3 * std
  const UCL = mean + 3 * std

  const isTemp = name.includes('Sensor_1')

  // 重繪前清理
  if (chartInstance) {
    chartInstance.destroy()
    chartCanvas.value.getContext('2d')?.clearRect(0, 0, chartCanvas.value.width, chartCanvas.value.height)
  }

  // 建立圖表
  chartInstance = new Chart(chartCanvas.value.getContext('2d'), {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: isTemp ? 'Temperature (°C)' : 'Humidity (%)',
        data: values,
        borderColor: 'blue', borderWidth: 2,
        tension: 0.25,
        pointRadius: values.map(v => (v > UCL || v < LCL ? 4 : 2)),
        pointBackgroundColor: values.map(v => (v > UCL || v < LCL ? 'red' : 'blue'))
      }]
    },
    options: {
      responsive: false,
      animation: false,
      scales: {
        y: {
          min: Math.min(LCL, ...values) - 1,
          max: Math.max(UCL, ...values) + 1,
          grid: { color: '#eee' }
        },
        x: { grid: { color: '#f5f5f5' } }
      },
      plugins: {
        legend: { display: false },
        tooltip: { enabled: true },
        annotation: {
          annotations: {
            meanLine: { type: 'line', yMin: mean, yMax: mean, borderColor: 'green', borderDash: [5,5], borderWidth: 1, label: { enabled: true, content: `Mean: ${mean.toFixed(1)}`, position: 'end' } },
            UCL: { type: 'line', yMin: UCL, yMax: UCL, borderColor: 'red', borderWidth: 1, label: { enabled: true, content: `UCL: ${UCL.toFixed(1)}`, position: 'end' } },
            LCL: { type: 'line', yMin: LCL, yMax: LCL, borderColor: 'red', borderWidth: 1, label: { enabled: true, content: `LCL: ${LCL.toFixed(1)}`, position: 'end' } }
          }
        }
      },
      layout: { padding: { top: 30 } }
    }
  })
}

// 監聽變更並 redraw
watch(() => props.hoverData, drawChart)
watch(() => props.chartRecords, drawChart)
</script>

<style scoped>
.chart-container {
  position: absolute;
  background: rgba(255,255,255,0.95);
  border-radius: 6px;
  padding: 8px;
  box-shadow: 0 0 8px rgba(0,0,0,0.15);
  z-index: 2000;
  transform: translate(-50%, 0);
}
.chart-title {
  font-weight: bold;
  margin-bottom: 4px;
  text-align: center;
}
</style>




  