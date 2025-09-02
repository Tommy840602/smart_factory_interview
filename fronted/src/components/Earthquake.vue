<template>
  <div class="p-4">
    <h3 class="text-xl mb-2">Earthquake Message:</h3>
    <div v-if="loading">Loading...</div>
    <div v-else-if="error" class="text-red-600">{{ error }}</div>
    <div
      v-else
      class="border rounded-lg shadow p-3 h-[300px] overflow-y-auto bg-gray-50"
    >
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="mb-4 pb-2 border-b last:border-none"
      >
        <!-- 日期 -->
        <p class="text-gray-500 text-xs">{{ formatDate(msg.date) }}</p>
        <!-- 來源 -->
        <p class="font-semibold text-blue-600 text-xs">
          Source: {{ msg.sender_name }}
        </p>
        <!-- 內文 -->
        <div
          class="h-[300px] overflow-y-auto border rounded-lg shadow p-3 bg-gray-50
                text-[12px] leading-[20px] font-sans whitespace-pre-line break-words"
        >
          {{ msg.text.trim() }}
        </div>
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

function formatQuakeText(text) {
  if (!text) return ''
  return text
    .replace(/\\n/g, '\n')   // 把字面上的 "\n" 轉回真正換行
    .trim()
}

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


  
  