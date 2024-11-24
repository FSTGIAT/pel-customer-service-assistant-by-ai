// src/components/LineChart.vue
<script setup>
import { ref, onMounted, onUnmounted ,watch } from 'vue'
import Chart from 'chart.js/auto'

const props = defineProps({
  chartData: {
    type: Object,
    required: true
  }
})

const chartRef = ref(null)
let chart = null

onMounted(() => {
  if (chartRef.value) {
    const ctx = chartRef.value.getContext('2d')
    chart = new Chart(ctx, {
      type: 'line',
      data: props.chartData,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 750,
          easing: 'easeInOutQuart'
        },
        plugins: {
          legend: {
            position: 'top'
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 1.5
          }
        }
      }
    })
  }
})

watch(() => props.chartData, (newData) => {
  if (chart) {
    chart.data = newData
    chart.update('active')
  }
}, { deep: true })

onUnmounted(() => {
  if (chart) {
    chart.destroy()
  }
})
</script>

<template>
  <div class="relative w-full h-full">
    <canvas ref="chartRef"></canvas>
  </div>
</template>