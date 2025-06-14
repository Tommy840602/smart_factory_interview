<!-- SensorDisplay.vue -->
<template>
    <div class="sensor-display p-4">
      <h1 class="text-2xl font-bold mb-4">In Factory</h1>
      <div class="flex space-x-8">
        <div class="p-4 bg-white rounded shadow">
          <p class="text-sm text-gray-500">Temperature:{{ temperature !== null ? temperature.toFixed(1) + ' °C' : '—' }}</p>
        </div>
        <div class="p-4 bg-white rounded shadow">
          <p class="text-sm text-gray-500">Humidity:{{ humidity !== null ? humidity.toFixed(1) + ' %' : '—' }}</p>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted, onUnmounted } from 'vue'
  import mqtt from 'mqtt'
  
  // 連線設定
  const BROKER_URL = 'ws://localhost:8083/mqtt'  // 請改為你的 MQTT over WebSocket URL
  const TOPIC_TEMP = 'sensors/temperature'
  const TOPIC_HUM  = 'sensors/humidity'
  
  // Vue reactive state
  const temperature = ref(null)
  const humidity    = ref(null)
  
  let client = null
  
  onMounted(() => {
    // 建立 MQTT 連線
    client = mqtt.connect(BROKER_URL, {
      // 若有帳密或其他設定，在這裡加上 username/password 等
      // username: 'user', password: 'pass'
    })
  
    client.on('connect', () => {
      console.log('MQTT connected')
      client.subscribe([TOPIC_TEMP, TOPIC_HUM], err => {
        if (err) console.error('Subscribe error:', err)
      })
    })
  
    client.on('message', (topic, payload) => {
      const msg = payload.toString()
      if (topic === TOPIC_TEMP) {
        temperature.value = parseFloat(msg)
      }
      else if (topic === TOPIC_HUM) {
        humidity.value = parseFloat(msg)
      }
    })
  
    client.on('error', err => {
      console.error('MQTT Error:', err)
    })
  })
  
  onUnmounted(() => {
    if (client) {
      client.end()
    }
  })
  </script>
  
  <style scoped>
  .sensor-display {
    max-width: 400px;
    margin: left;
  }
  </style>
  