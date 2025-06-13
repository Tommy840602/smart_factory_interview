<template>
  <div class="three-container" ref="threeContainer">
    <div v-if="hoveredObject" 
         class="hover-info"
         :style="{ left: `${infoPosition.x}px`, top: `${infoPosition.y}px` }">
      {{ hoveredObject }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

const threeContainer = ref(null)
const hoveredObject = ref(null)
const infoPosition = ref({ x: 0, y: 0 })

let scene, camera, renderer, controls, directionalLight, raycaster, mouse
// 儲存圓環 mesh 的陣列
const circles = []

const fetchSunData = async () => {
  const res = await fetch('http://localhost:8000/api/suntime')
  return await res.json()
}

const updateLight = (now, sunrise, sunset) => {
  const currentTime = new Date(now)
  const sunriseTime = new Date(sunrise)
  const sunsetTime = new Date(sunset)
  
  // 计算当前时间在日出日落之间的位置（0-1）
  let timeRatio = 0
  if (currentTime < sunriseTime) {
    // 日出前
    timeRatio = 0
  } else if (currentTime > sunsetTime) {
    // 日落后
    timeRatio = 1
  } else {
    // 日出日落之间
    const totalDayLength = sunsetTime - sunriseTime
    const currentDayLength = currentTime - sunriseTime
    timeRatio = currentDayLength / totalDayLength
  }
  
  // 根据时间调整光照强度和颜色
  const intensity = 0.3 + (1 - timeRatio) * 0.7 // 0.3 到 1.0 之间
  const color = new THREE.Color()
  color.setHSL(0.1 + timeRatio * 0.1, 0.8, 0.5) // 从暖色到冷色
  
  if (directionalLight) {
    directionalLight.intensity = intensity
    directionalLight.color = color
    
    // 调整光源位置模拟太阳运动
    const angle = Math.PI * (0.5 + timeRatio)
    const radius = 5
    directionalLight.position.x = Math.cos(angle) * radius
    directionalLight.position.y = Math.sin(angle) * radius
    directionalLight.position.z = 0
  }
}

const initScene = async () => {
  // 基本場景設定
  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000)
  camera.position.set(0, 2, 5)

  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(window.innerWidth, window.innerHeight)
  threeContainer.value.appendChild(renderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.update()

  // 光源
  directionalLight = new THREE.DirectionalLight(0xffffff, 1)
  directionalLight.position.set(5, 5, 5)
  scene.add(directionalLight)
  scene.add(new THREE.AmbientLight(0xffffff, 0.3))

  // Raycaster & Mouse
  raycaster = new THREE.Raycaster()
  mouse = new THREE.Vector2()
  renderer.domElement.addEventListener('mousemove', onMouseMove)

  // 載入 GLTF 模型
  const loader = new GLTFLoader()
  loader.load(
    '/models/scene.glb',            // 改成你的路徑
    gltf => {
      const model = gltf.scene
      scene.add(model)

      // 指定兩個世界座標點（或由 model.getObjectByName 拿到節點位置）
      const positions = [
        new THREE.Vector3(0, 1.5, 0),     // 例：模型上方
        new THREE.Vector3(1, 0.5, 0)      // 例：模型側面
      ]

      positions.forEach((pos, idx) => {
        // 建立虛線圓
        const circleGeo = new THREE.CircleGeometry(0.1, 64)
        const dashedMat = new THREE.LineDashedMaterial({
          color: 0x00ff00,
          dashSize: 0.05,
          gapSize: 0.05,
          scale: 1
        })
        const circle = new THREE.LineLoop(circleGeo, dashedMat)
        circle.computeLineDistances()
        circle.rotation.x = Math.PI / 2
        circle.position.copy(pos)
        circle.name = `MarkerCircle${idx}`

        // 如果想讓圓跟著 model 動，可以加到 model 上：
        // model.add(circle)
        // 或直接放在 scene 中，並在動畫裡更新位置

        scene.add(circle)
        circles.push(circle)
      })
    },
    xhr => console.log(`模型載入中：${(xhr.loaded/xhr.total*100).toFixed(1)}%`),
    err => console.error('載入模型失敗：', err)
  )

  // 取得初次日照資料並設定光照
  const sunData = await fetchSunData()
  updateLight(sunData.now, sunData.sunrise, sunData.sunset)

  // 動畫迴圈
  const animate = () => {
    requestAnimationFrame(animate)
    controls.update()
    checkHover()
    renderer.render(scene, camera)
  }
  animate()
}

const onMouseMove = event => {
  const rect = renderer.domElement.getBoundingClientRect()
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1
}

const checkHover = () => {
  raycaster.setFromCamera(mouse, camera)
  // 把所有圓傳進去做相交測試
  const intersects = raycaster.intersectObjects(circles)
  if (intersects.length > 0) {
    hoveredObject.value = intersects[0].object.name
    // 取第一個相交圓的世界座標，轉成螢幕座標
    const worldPos = intersects[0].object.getWorldPosition(new THREE.Vector3())
    const screenPos = worldPos.clone().project(camera)
    infoPosition.value = {
      x: (screenPos.x + 1) / 2 * window.innerWidth,
      y: -(screenPos.y - 1) / 2 * window.innerHeight
    }
  } else {
    hoveredObject.value = null
  }
}

onMounted(initScene)

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight
  camera.updateProjectionMatrix()
  renderer.setSize(window.innerWidth, window.innerHeight)
})

// 每分鐘更新一次光照
setInterval(async () => {
  const sunData = await fetchSunData()
  updateLight(sunData.now, sunData.sunrise, sunData.sunset)
}, 60 * 1000)

</script>

<style scoped>
.three-container {
    width: 100%;
    height: 100%;
    min-height: 500px;
    position: relative;
    background: #f0f0f0;
}

.three-container canvas {
    width: 100% !important;
    height: 100% !important;
    display: block;
}

.hover-info {
    position: absolute;
    background: rgba(0, 0, 0, 0.7);
    color: white;
    padding: 5px 10px;
    border-radius: 4px;
    font-size: 14px;
    pointer-events: none;
    transform: translate(-50%, -100%);
    margin-top: -10px;
    z-index: 1000;
}
</style>

