<template>
         <div>
            <h3>UPS Info</h3>
            <p>Battery Charge:{{ ups.battery_charge }}%</p>
            <p>Battery Runtime:{{ ups.battery_runtime}}s</p>
            <p>UPS status:{{ ups.ups_status }}</p>
            <p>Light:<span :style="{ color: getColor(ups.light)}">●</span></p>
            <p>UPS Load:{{ ups.ups_load }}%</p>
            <p>Input Voltage:{{ ups.input_voltage}}V</p>
            <p>Output Voltage:{{ ups.output_voltage }}V</p>
        </div>   
</template>

<script setup>
    import { ref, onMounted, onBeforeUnmount } from 'vue'
    import axios from 'axios'

    const ups = ref({
        battery_charge: 0,
        ups_status: '',
        light: 'green',
        battery_runtime: 0,
        ups_load: 0,
        input_voltage: 0,
        OUTput_voltage:0,
    })

    function getColor(light) {
        return {
            red: 'red',
            yellow: 'orange',
            green: 'green'
        }[light] || 'gray'
    }

    async function fetchUPS() {
        try {
            const res = await fetch('http://localhost:8000/api/ups')
            const data = await res.json()
            ups.value = data
        } catch (error) {
            console.error('UPS 查詢失敗：', error)
        }
    }

    let intervalId2 = null

    onMounted(() => {
        fetchUPS()                              
        intervalId2 = setInterval(fetchUPS,10*1000) 
    })

    onBeforeUnmount(() => {
        clearInterval(intervalId2)
    })
</script>


<style scoped>
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