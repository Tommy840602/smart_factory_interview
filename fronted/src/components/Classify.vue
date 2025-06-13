<template>
    <div class="gallery">
      <!-- 已載入並分類的圖片卡片 -->
      <div
        v-for="item in displayed"
        :key="item.imageId"
        class="card"
      >
        <img :src="getUrl(item.imageId)" alt="Image" />
        <p>
          label: {{ item.label }},
          confidence: {{ (item.confidence * 100).toFixed(1) }}%
        </p>
      </div>
  
      <!-- 載入中提示 -->
      <div v-if="loading" class="loading">
        載入中第 {{ displayed.length + 1 }} 張…
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted, onBeforeUnmount } from 'vue'
  import axios from 'axios'
  
  const IMAGES_API   = 'http://localhost:8000/api/images'
  const CLASSIFY_API = 'http://localhost:8000/api/classify'
  
  // 全部圖檔清單
  const allImages = ref([])
  // 已載入並分類的圖片與結果
  const displayed = ref([])
  // 載入狀態
  const loading   = ref(false)
  
  let currentIndex = 0    // 下一張要處理的索引
  let timerId      = null
  
  const getUrl = path =>
    `https://storage.googleapis.com/screw_anomalies/${path}`
  
  async function loadNext() {
    // 如果已經處理完所有圖，停止定時
    if (currentIndex >= allImages.value.length) {
      clearInterval(timerId)
      loading.value = false
      return
    }
  
    const img = allImages.value[currentIndex]
    loading.value = true
  
    try {
      const { data } = await axios.post(
        `${CLASSIFY_API}/${encodeURIComponent(img)}`
      )
      displayed.value.push({
        imageId:    img,
        label:      data.label,
        confidence: data.confidence
      })
    } catch (e) {
      console.error('分類失敗：', img, e)
    } finally {
      loading.value = false
      currentIndex++
    }
  }
  
  onMounted(async () => {
    try {
      // 1. 取得所有圖片路徑
      const res = await axios.get(IMAGES_API)
      // 2. 兼容兩種返回格式：直接陣列，或 { images: [...] }
      const list = Array.isArray(res.data)
        ? res.data
        : Array.isArray(res.data.images)
          ? res.data.images
          : []
      allImages.value = list.filter(p => /\.(png|jpe?g|gif)$/i.test(p))
  
      // 3. 若有圖片，就先載入並分類第一張，再每隔 10 秒載入下一張
      if (allImages.value.length > 0) {
        await loadNext()
        timerId = setInterval(loadNext, 10000)
      }
    } catch (err) {
      console.error('取得圖片列表失敗：', err)
    }
  })
  
  onBeforeUnmount(() => {
    if (timerId) clearInterval(timerId)
  })
  </script>
  
  <style>
  .gallery {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    justify-content: center;
  }
  .card {
    border: 1px solid #ccc;
    padding: 0.5rem;
    width: 200px;
    text-align: center;
  }
  .card img {
    width: 100%;
    height: auto;
  }
  .loading {
    width: 100%;
    text-align: center;
    margin-top: 1rem;
    color: #666;
  }
  </style>
  