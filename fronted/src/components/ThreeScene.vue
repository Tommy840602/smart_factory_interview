<template>
  <div class="scene-wrapper">
    <div ref="threeContainer" class="three-container"></div>
    <div class="info-panel"
         v-if="hoveredObject"
         :style="{ left: infoPosition.x + 'px', top: infoPosition.y + 'px' }">
        <h3>Object Info.</h3>
        <p>Name:{{ hoveredObject }}</p>
    </div>
  </div>
</template>

<script setup>
  import { ref, onMounted } from 'vue'
  import * as THREE from 'three'
  import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

  const threeContainer = ref(null)
  const hoveredObject = ref(null)
  const infoPosition = ref({ x: 0, y: 0 })

  let scene, camera, renderer, controls, directionalLight, cube, raycaster, mouse, circle

  const fetchSunData = async () => {
      const res = await fetch('http://localhost:8000/sunlight?lat=24.56&lng=120.82&tz=Asia/Taipei')
      return await res.json()
  }

  const updateLight = (now, sunrise, sunset) => {
      const current = new Date(now).getTime()
      const sr = new Date(sunrise).getTime()
      const ss = new Date(sunset).getTime()

      let intensity = 0
      let color = new THREE.Color()

      if (current < sr || current > ss) {
          intensity = 0.1
          color.setHSL(0.6, 1, 0.1)
      } else {
          const progress = (current - sr) / (ss - sr)
          intensity = 0.5 + 0.5 * Math.sin(Math.PI * progress)
          color.setHSL(0.1 + 0.1 * (1 - progress), 1, 0.5)
      }

      directionalLight.intensity = intensity
      directionalLight.color = color
  }

  const initScene = async () => {
      scene = new THREE.Scene()
      camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000)
      camera.position.set(0, 2, 5)

      renderer = new THREE.WebGLRenderer({ antialias: true })
      renderer.setSize(window.innerWidth, window.innerHeight)
      threeContainer.value.appendChild(renderer.domElement)

      controls = new OrbitControls(camera, renderer.domElement)
      controls.enableDamping = true
      controls.target.set(0, 0, 0)
      controls.update()

      // 光源
      directionalLight = new THREE.DirectionalLight(0xffffff, 1)
      directionalLight.position.set(5, 5, 5)
      scene.add(directionalLight)

      const ambientLight = new THREE.AmbientLight(0xffffff, 0.3)
      scene.add(ambientLight)

      // 立方體
      const geometry = new THREE.BoxGeometry(3,3,3)
      const material = new THREE.MeshStandardMaterial({ color: 0x999999 })
      cube = new THREE.Mesh(geometry, material)
      cube.name = 'Cube'
      scene.add(cube)

      // 虛線圓形貼在立方體上表面
      const circleGeo = new THREE.CircleGeometry(0.05, 64)
      const dashedMat = new THREE.LineDashedMaterial({ color: 0x00ff00, dashSize: 0.1, gapSize: 0.1 })
      circle = new THREE.LineLoop(circleGeo, dashedMat)
      circle.computeLineDistances()
      circle.rotation.x = Math.PI / 2
      circle.position.y = 1.5 //半高 
      circle.name = 'TopCircle'
      cube.add(circle)

      raycaster = new THREE.Raycaster()
      mouse = new THREE.Vector2()
      renderer.domElement.addEventListener('mousemove', onMouseMove)

      const sunData = await fetchSunData()
      updateLight(sunData.now, sunData.sunrise, sunData.sunset)

      const animate = () => {
          requestAnimationFrame(animate)
          controls.update()
          checkHover()
          renderer.render(scene, camera)
      }
      animate()
  }
  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight
    camera.updateProjectionMatrix()
    renderer.setSize(window.innerWidth, window.innerHeight)
    })

  const onMouseMove = (event) => {
      const rect = renderer.domElement.getBoundingClientRect()
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1
  }

  const checkHover = () => {
      raycaster.setFromCamera(mouse, camera)
      if (!circle) return
      const intersects = raycaster.intersectObjects([circle])
      if (intersects.length > 0) {
          hoveredObject.value = 'TopCircle'
          const screenPos = circle.getWorldPosition(new THREE.Vector3()).clone().project(camera)
          infoPosition.value = {
              x: (screenPos.x + 1) / 2 * window.innerWidth,
              y: -(screenPos.y - 1) / 2 * window.innerHeight
          }
      } else {
          hoveredObject.value = null
      }
  }

  onMounted(initScene)
  
  setInterval(async () => {
  const sunData = await fetchSunData()
  updateLight(sunData.now, sunData.sunrise, sunData.sunset)
    }, 60 * 1000)
    
</script>

<style>
  .three-container {
      width: 100vw;
      height: 100vh;
      overflow: hidden;
  }

  .info-panel {
      position: absolute;
      background: rgba(255, 255, 255, 0.95);
      padding: 10px;
      border: 1px solid #ccc;
      font-family: sans-serif;
      z-index: 10;
      transform: translate(-50%, -100%);
      pointer-events: none;
  }
</style>

