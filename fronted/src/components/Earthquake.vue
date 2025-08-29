<template>
  <div class="p-4">
    <h2 class="text-xl font-bold mb-4">Earthquake Message</h2>

    <div v-if="loading">Loading...</div>
    <div v-else-if="error" class="text-red-600">{{ error }}</div>

    <div v-else>
      <div v-for="msg in messages" :key="msg.id" class="border rounded-lg p-3 mb-3 shadow">
        <!-- 用 formatDate 轉換 -->
        <p class="text-gray-500 text-sm">{{ formatDate(msg.date) }}</p>
        <p class="font-semibold text-blue-600">Source: {{ msg.sender_name }}</p>
        <pre class="whitespace-pre-wrap">{{ msg.text }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue"

const messages = ref([])
const loading = ref(true)
const error = ref(null)
let timer = null

async function loadMessages() {
  try {
    const res = await fetch("http://localhost:8000/api/earthquake", { method: "GET" })
    const data = await res.json()

    if (data.error) {
      error.value = data.error
    } else if (data.data) {
      // 保證 data.data 是陣列，才能 v-for
      messages.value = Array.isArray(data.data) ? data.data : [data.data]
    } else {
      messages.value = []
    }
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadMessages()                      // 頁面載入時先呼叫一次
  timer = setInterval(loadMessages, 300000)  // 每 5 分鐘重新呼叫
})

onUnmounted(() => {
  if (timer) clearInterval(timer)     // 離開頁面時清掉 timer
})

function formatDate(isoStr) {
  if (!isoStr) return "無效時間"
  const d = new Date(isoStr)
  return isNaN(d.getTime()) ? isoStr : d.toLocaleString("zh-TW", { timeZone: "Asia/Taipei" })
}
</script>


  
  