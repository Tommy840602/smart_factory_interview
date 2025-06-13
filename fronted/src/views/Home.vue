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
        <div class="section three-section">
            <ThreeScene/>
        </div>
        <div class="section">
            <Classify/>
        </div>
    </div>
</template>

<script setup>
import Kmap from '@/components/Kmap.vue';
import Power from '@/components/Power.vue'
import Ups from '@/components/Ups.vue';
import Weather from '@/components/Weather.vue';
import ThreeScene from '@/components/ThreeScene.vue';
import Classify from '@/components/Classify.vue';
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
</style>