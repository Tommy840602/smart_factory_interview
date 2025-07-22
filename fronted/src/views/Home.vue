<template>
    <div class="home-container">
        <div class="section">
            <Power/>
        </div>
        <div class="section">
            <Weather/>
        </div>
        <div class="section">
            <Ups/>
        </div>
        <div class="section three-section mqtt-section">
            <SceneWrapper/>
        </div>
        <div class="section">
            <Classify/>
        </div>
    </div>
</template>

<script setup>
import Power from '@/components/Power.vue'
import Ups from '@/components/Ups.vue';
import Weather from '@/components/Weather.vue';
import Classify from '@/components/Classify.vue';
import SceneWrapper from '@/pages/SceneWrapper.vue';
</script>

<style scoped>
.home-container {
    width: 100%;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    gap: 20px;
    padding: 20px;
    box-sizing: border-box;
}

.section {
    width: 100%;
    min-height: 200px;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
    overflow: hidden;
}

.three-section {
    min-height: 500px;
    position: relative;
}

.mqtt-section {
  border: 2px solid #4CAF50;
}

.opcua-section {
  border: 2px solid #2196F3;
}
</style>