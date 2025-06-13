<template>
    <div>
        <h3>Knowledge Map</h3>
        <iframe v-if="mapUrl" :src="mapUrl" frameborder="0" scrolling="no" width="750px" height="750px"></iframe>
    </div>
</template>

<script setup>
    import { ref, onMounted, onBeforeUnmount } from 'vue'
  
    const mapUrl=ref('')

    onMounted(async () => {
        const res = await fetch('http://localhost:8000/api/kmap')
        const data = await res.json()
        mapUrl.value = 'http://localhost:8000' + data.map_url
    })

</script>

<style scoped>
    .iframe {
        width: 100%;
        height: 100%;
    }
</style>