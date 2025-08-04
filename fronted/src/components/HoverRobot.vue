<script setup>
import { defineProps, ref, computed } from 'vue'

const props = defineProps({
  hover: Object,
  robotId: String,
  records: Object  // { nicla: [...], left_arm: [...], right_arm: [...] }
})

const modules = ['nicla', 'left_arm', 'right_arm']
const selectedModule = ref('nicla')

const selectModule = (mod) => selectedModule.value = mod

const dataToShow = computed(() => props.records[selectedModule.value] || [])
</script>

  