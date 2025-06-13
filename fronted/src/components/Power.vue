<template>
    <div class="status-box">
        <h3>Real-time Reserve Margin: {{ data.reserve_percent }}%</h3>
        <h3>Remaining Reserve: {{ (data.reserve_w * 0.01).toFixed(2) }} GW</h3>
        <div :class="['indicator', data.indicator]"></div>
    </div>
</template>

<script setup>
    import { ref, onMounted, onBeforeUnmount } from 'vue'
    import axios from 'axios'
    const data = ref({
        reserve_percent: 0,
        reserve_w: 0,
        indicator: 'green'
    })
    const fetchReserve = async () => {
        const res = await axios.get('http://localhost:8000/api/power_supply')
        data.value = res.data
    }
    onMounted(() => {
        fetchReserve()
        setInterval(fetchReserve, 600*1000)  // 每小時更新一次
    })    
</script>

<style scoped>
    .status-box {
        text-align: center;
    }

    .indicator {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        margin: 20px auto;
    }
    .green {
        background-color: #4CAF50;
    }

    .yellow {
        background-color: #FFEB3B;
    }

    .orange {
        background-color: #FF9800;
    }

    .red {
        background-color: #F44336;
    }

    .black {
        background-color: #000;
    }      
</style>