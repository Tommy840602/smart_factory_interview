<template>
    <div class="weather-container">
        <div v-if="location">
            <p>🌎{{ latDMS }},{{ lonDMS }}</p>
        </div>
        <div v-if="weatherInfo.weather">
            <p>Weather:{{ weatherInfo.weather.Weather }}</p>
            <p>Temperature:{{ weatherInfo.weather.AirTemperature}}℃</p>
            <p>RelativeHumidity:{{ weatherInfo.weather.RelativeHumidity }}%</p>
            <p>WindSpeed:{{ weatherInfo.weather.WindSpeed }} m/s</p>
        </div>
        <div>
            <p>Date: {{ suntime.Date }}</p>
            <p>Sun Rise Time: {{ suntime.SunRiseTime }}</p>
            <p>Sun Set Time: {{ suntime.SunSetTime }}</p>
        </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted, onBeforeUnmount } from 'vue'
  import axios from 'axios'
  
  // axios 全域設定
  axios.defaults.baseURL = 'http://localhost:8000/api'
  axios.defaults.headers.post['Content-Type'] = 'application/json'
  
  const location    = ref(null)
  const latDMS      = ref('')
  const lonDMS      = ref('')
  // 一開始設成空物件，不是 null
  const weatherInfo = ref({})
  const suntime     = ref({})
  let intervalId    = null
  
  function decimalToDMS(coord, posSym, negSym) {
    const abs     = Math.abs(coord)
    const deg     = Math.floor(abs)
    const minFull = (abs - deg) * 60
    const min     = Math.floor(minFull)
    const sec     = ((minFull - min) * 60).toFixed(1)
    const dir     = coord >= 0 ? posSym : negSym
    return `${dir}${deg}°${min}'${sec}"`
  }
  
  async function getLocation() {
    try {
      return await new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
          return reject(new Error('不支援 GPS'))
        }
        navigator.geolocation.getCurrentPosition(
          pos => resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
          err => reject(err)
        )
      })
    } catch {
      const res  = await fetch('https://ipinfo.io/json?token=dc087daf7de4e0')
      const data = await res.json()
      const [lat, lon] = data.loc.split(',').map(Number)
      return { lat, lon }
    }
  }
  
  async function fetchWeatherAndLocation() {
    try {
      // 1. 取得位置
      const { lat, lon } = await getLocation()
      location.value = { lat, lon }
      latDMS.value    = decimalToDMS(lat, 'N', 'S')
      lonDMS.value    = decimalToDMS(lon, 'E', 'W')
  
      // 2. 上傳 GPS
      await axios.post('/gps_location', { lat, lon })
  
      // 3. 拿氣象資料
      const wxRes = await axios.post('/weather', { lat, lon })
      weatherInfo.value = wxRes.data.weather || {}
  
      // 4. 拿日出日落資料
      const sunRes = await axios.post('/suntime', { lat, lon })
      const sun   = sunRes.data || {}
      suntime.value = {
        Date:        sun.Date || '',
        SunRiseTime: sun.SunRiseTime || '',
        SunSetTime:  sun.SunSetTime || ''
      }
  
    } catch (err) {
      console.error('fetchWeatherAndLocation 出錯：', err)
    }
  }
  
  onMounted(() => {
    fetchWeatherAndLocation()
    intervalId = setInterval(fetchWeatherAndLocation, 30 * 60 * 1000)
  })
  
  onBeforeUnmount(() => {
    clearInterval(intervalId)
  })
  </script>
  
  <style scoped>
  </style>
  