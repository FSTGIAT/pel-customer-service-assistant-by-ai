// components/MonitoringDashboard.vue
<script setup>
import { ref, onMounted } from 'vue'
import { useSessionStore } from '@/stores/sessionStore'
import { storeToRefs } from 'pinia'
import LineChart from './LineChart.vue'  // Add this import

const stats = ref([
  { 
    label: 'Active Sessions', 
    value: '234', 
    icon: 'fas fa-users', 
    iconClass: 'text-blue-500' 
  },
  { 
    label: 'Error Rate', 
    value: '0.5%', 
    icon: 'fas fa-triangle-exclamation', 
    iconClass: 'text-red-500' 
  },
  { 
    label: 'Avg Response Time', 
    value: '1.2s', 
    icon: 'fas fa-clock', 
    iconClass: 'text-green-500' 
  },
  { 
    label: 'Active Alerts', 
    value: '2', 
    icon: 'fas fa-bell', 
    iconClass: 'text-yellow-500' 
  }
])

const activeTab = ref('realtime')

const tabs = [
  { id: 'realtime', label: 'Realtime' },
  { id: 'historical', label: 'Historical' },
  { id: 'alerts', label: 'Alerts' }
]

const tableHeaders = ['Customer ID', 'Duration', 'Status', 'Actions']

const activeSessions = ref([
  {
    id: 1,
    customerId: '3694388',
    duration: '00:15:23',
    status: 'Active'
  }
])

const chartData = ref({
  labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
  datasets: [
    {
      label: 'Sessions',
      data: [100, 150, 800, 950, 750, 450],
      borderColor: '#3B82F6'
    },
    {
      label: 'Errors',
      data: [2, 3, 4, 7, 5, 3],
      borderColor: '#EF4444'
    }
  ]
})

const getStatusClass = (status) => {
  return status === 'Active' 
    ? 'bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full'
    : 'bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded-full'
}

const viewSessionDetails = (sessionId) => {
  console.log('View session:', sessionId)
}

onMounted(() => {
  // Initialize real-time updates
})
</script>

<template>
  <div class="flex flex-col h-screen bg-gray-50">
    <!-- Header -->
    <div class="bg-white border-b border-gray-200 p-4">
      <h1 class="text-2xl font-bold text-gray-800">System Monitoring</h1>
    </div>

    <!-- Main Content -->
    <div class="flex-1 p-6 overflow-auto">
      <!-- Quick Stats -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div v-for="(stat, index) in stats" 
             :key="index" 
             class="bg-white p-4 rounded-lg shadow">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">{{ stat.label }}</p>
              <p class="text-2xl font-bold">{{ stat.value }}</p>
            </div>
            <i :class="['fas', stat.icon, stat.iconClass]"></i>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="bg-white rounded-lg shadow mb-6">
        <div class="border-b border-gray-200">
          <nav class="flex space-x-4 px-4">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id"
              :class="[
                'px-3 py-2 text-sm font-medium',
                activeTab === tab.id
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              ]"
            >
              {{ tab.label }}
            </button>
          </nav>
        </div>

        <!-- Chart Area -->
        <div class="p-4">
          <div class="h-64">
            <line-chart :chart-data="chartData" />
          </div>
        </div>
      </div>

      <!-- Session List -->
      <div class="bg-white rounded-lg shadow">
        <div class="px-4 py-3 border-b border-gray-200">
          <h3 class="text-lg font-medium">Active Sessions</h3>
        </div>
        <div class="p-4">
          <table class="min-w-full">
            <thead>
              <tr>
                <th v-for="header in tableHeaders" 
                    :key="header"
                    class="text-left text-sm font-medium text-gray-500 pb-3">
                  {{ header }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="session in activeSessions" 
                  :key="session.id" 
                  class="border-t border-gray-100">
                <td class="py-2">{{ session.customerId }}</td>
                <td>{{ session.duration }}</td>
                <td>
                  <span :class="getStatusClass(session.status)">
                    {{ session.status }}
                  </span>
                </td>
                <td>
                  <button @click="viewSessionDetails(session.id)" 
                          class="text-blue-600 hover:text-blue-800 text-sm">
                    View Details
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid {
  display: grid;
  gap: 1rem;
}
</style>