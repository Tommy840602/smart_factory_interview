<template>
  <div class="weather-container">
    <div v-if="location">
      <h3>Weather Info:</h3>
      <p>GPS: {{ latDMS }}, {{ lonDMS }}</p>
    </div>
    <div v-if="weatherInfo">
      <p>Weather: {{ weatherInfo.weather.Weather }}</p>
      <p>Temperature: {{ weatherInfo.weather.AirTemperature }}℃</p>
      <p>Humidity: {{ weatherInfo.weather.RelativeHumidity }}%</p>
      <p>Wind Speed: {{ weatherInfo.weather.WindSpeed }} m/s</p>
    </div>
    <div v-if="suntime">
      <p>Date: {{ suntime.Date }}</p>
      <p>Sun Rise Time: {{ suntime.SunRiseTime }}</p>
      <p>Sun Set Time: {{ suntime.SunSetTime }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'

axios.defaults.baseURL = 'http://localhost:8000/api'
axios.defaults.headers.post['Content-Type'] = 'application/json'

const location    = ref(null)
const latDMS      = ref('')
const lonDMS      = ref('')
const weatherInfo = ref(null)
const suntime     = ref(null)
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
    const { lat, lon } = await getLocation()
    location.value = { lat, lon }
    latDMS.value   = decimalToDMS(lat, 'N', 'S')
    lonDMS.value   = decimalToDMS(lon, 'E', 'W')

    const res = await axios.post('/gps_location', { lat, lon })
    const data = res.data
    weatherInfo.value = data.station || {}
    suntime.value     = data.suntime || {}
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



  