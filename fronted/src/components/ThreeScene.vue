<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { CSS2DRenderer, CSS2DObject } from 'three/examples/jsm/renderers/CSS2DRenderer.js'
import HoverInfo from '@/components/HoverInfo.vue'

const glContainer   = ref(null)
const hoveredObject = ref(null)
const infoPosition  = ref({ x: 0, y: 0 })

// ✅ 雙 emit
const emit = defineEmits(['sensor-hover', 'robot-hover'])

const axes = new THREE.AxesHelper(1.5)
let scene, camera, renderer, labelRenderer,
    controls, directionalLight, raycaster, mouse,
    frameId

const circles = []
const circleDataMap = new Map()
const props = defineProps({
  sensorData: Object,
  chartRecords: Object
})

function onWindowResize() {
  const w = window.innerWidth
  const h = window.innerHeight
  camera.aspect = w / h
  camera.updateProjectionMatrix()
  renderer.setSize(w, h)
  labelRenderer.setSize(w, h)
}

function onMouseMove(evt) {
  const rect = renderer.domElement.getBoundingClientRect()
  mouse.x = ((evt.clientX - rect.left) / rect.width) * 2 - 1
  mouse.y = -((evt.clientY - rect.top) / rect.height) * 2 + 1
}

function checkHover() {
  raycaster.setFromCamera(mouse, camera)
  const hits = raycaster.intersectObjects(circles)

  if (hits.length) {
    const obj = hits[0].object
    const name = obj.name
    const meta = obj.userData?.meta || ''
    const world = obj.getWorldPosition(new THREE.Vector3())
    const proj  = world.clone().project(camera)

    infoPosition.value = {
      x: (proj.x + 1) / 2 * window.innerWidth,
      y: (1 - proj.y) / 2 * window.innerHeight
    }

    const entry = circleDataMap.get(name)
    if (entry && props.sensorData?.[name] !== undefined) {
      entry.circle.userData.meta = `Value: ${props.sensorData[name]}`
    }

    // ✅ 統一 hoverObject 結構
    hoveredObject.value = {
      name,
      module: null,   // ✅ Robot 預設 null，交給 SceneWrapper2 補
      html: `<strong>${name}</strong><br>${meta}`,
      x: infoPosition.value.x,
      y: infoPosition.value.y
    }

    // ✅ 判斷資料來源
    if (name.startsWith('Sensor_')) {
      emit('sensor-hover', {
        id: name.toLowerCase(),
        x: infoPosition.value.x,
        y: infoPosition.value.y
      })
    } else if (name.startsWith('Robot_')) {
      const robotId = name.toLowerCase()
      emit('robot-hover', {
        id: robotId,       // robot_3
        name,              // "Robot_3"
        module: 'nicla',      // 後續由 SceneWrapper2 再補
        x: infoPosition.value.x,
        y: infoPosition.value.y
      })
    }

  } else {
    hoveredObject.value = null
  }
}

function drawNamedCircle(position, name) {
  const circleGeo = new THREE.CircleGeometry(0.1, 64).toNonIndexed()
  const dashedMat = new THREE.LineDashedMaterial({
    color: 0x00ff00,
    dashSize: 0.05,
    gapSize: 0.05
  })

  const circle = new THREE.LineLoop(circleGeo, dashedMat)
  circle.computeLineDistances()
  circle.rotation.x = Math.PI / 2
  circle.position.copy(position)
  circle.name = name
  scene.add(circle)
  circles.push(circle)
  circleDataMap.set(name, { circle })

  const div = document.createElement('div')
  div.className = 'label'
  div.textContent = name
  const label = new CSS2DObject(div)
  label.position.set(0, 0.15, 0)
  circle.add(label)
}

async function initScene() {
  await nextTick()
  const container = glContainer.value
  if (!container) throw new Error('glContainer not found')

  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 2000)
  camera.position.set(0, 2, 5)

  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(window.innerWidth, window.innerHeight)
  container.appendChild(renderer.domElement)

  labelRenderer = new CSS2DRenderer()
  labelRenderer.setSize(window.innerWidth, window.innerHeight)
  labelRenderer.domElement.style.position = 'absolute'
  labelRenderer.domElement.style.top = '0px'
  labelRenderer.domElement.style.pointerEvents = 'none'
  container.appendChild(labelRenderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true

  // ✅ 固定光源
  directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
  directionalLight.position.set(5, 5, 5)
  scene.add(directionalLight)
  scene.add(new THREE.AmbientLight(0xffffff, 0.3))

  raycaster = new THREE.Raycaster()
  mouse = new THREE.Vector2()
  renderer.domElement.addEventListener('mousemove', onMouseMove)

  new GLTFLoader().load(
    'models/scene.glb',
    gltf => {
      const model = gltf.scene
      model.rotation.x = Math.PI / 3
      model.rotation.y = -Math.PI / 2
      scene.add(model)
      scene.add(axes)

      const points = [
        { name: 'Robot_1', position: new THREE.Vector3(1.1878, 0.0423, 2.4691) },
        { name: 'Robot_2', position: new THREE.Vector3(3.2301, 0.5295, 2.5110) },
        { name: 'Robot_3', position: new THREE.Vector3(5.1673, 1.8085, 2.3473) },
        { name: 'Robot_4', position: new THREE.Vector3(5.2666, 0.7334, 2.0687) },
        { name: 'Sensor_1', position: new THREE.Vector3(0.3332, -0.0053, 2.5154) },
        { name: 'Sensor_2', position: new THREE.Vector3(0.0189, 0.1707, 2.0220) }
      ]
      points.forEach(p => drawNamedCircle(p.position, p.name))

      const box = new THREE.Box3().setFromObject(model)
      const center = new THREE.Vector3()
      const size = new THREE.Vector3()
      box.getCenter(center)
      box.getSize(size)

      const maxDim = Math.max(size.x, size.y, size.z)
      camera.far = maxDim * 10
      camera.updateProjectionMatrix()

      camera.position.set(center.x, center.y + size.y * 2, 0)
      camera.lookAt(center)
      controls.target.copy(center)
      controls.update()
    },
    xhr => console.log(`Loading ${(xhr.loaded / xhr.total * 100) | 0}%`),
    err => console.error(err)
  )

  window.addEventListener('resize', onWindowResize)

  ;(function animate() {
    frameId = requestAnimationFrame(animate)
    controls.update()
    checkHover()
    renderer.render(scene, camera)
    labelRenderer.render(scene, camera)
  })()
}

onMounted(initScene)

onBeforeUnmount(() => {
  window.removeEventListener('resize', onWindowResize)
  renderer.domElement.removeEventListener('mousemove', onMouseMove)
  cancelAnimationFrame(frameId)
  renderer.dispose()
  controls.dispose()
  labelRenderer?.domElement.remove()
  labelRenderer = null
})
</script>

<template>
  <div ref="glContainer" class="three-container">
    <HoverInfo :hoverData="hoveredObject" :chartRecords="props.chartRecords" />
  </div>
</template>

<style scoped>
.three-container {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 500px;
  background: #f0f0f0;
  overflow: hidden;
}
.three-container canvas {
  display: block;
  width: 100% !important;
  height: 100% !important;
}
:deep(.label) {
  background: rgba(0, 0, 0, 0.6);
  color: white;   /* ✅ 白色字更清楚 */
  padding: 2px 4px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  white-space: nowrap;
}
</style>





















