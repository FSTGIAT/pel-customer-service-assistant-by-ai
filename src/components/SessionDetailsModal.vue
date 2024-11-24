// src/components/SessionDetailsModal.vue
<script setup>
import { computed } from 'vue'

const props = defineProps({
  session: {
    type: Object,
    required: true
  },
  isOpen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])

const statusColor = computed(() => {
  return props.session.status === 'Active' ? 'text-green-600' : 'text-gray-600'
})
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
    <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
      <div class="flex flex-col">
        <!-- Header -->
        <div class="flex justify-between items-center pb-3 border-b">
          <h3 class="text-xl font-semibold text-gray-900">Session Details</h3>
          <button @click="$emit('close')" class="text-gray-400 hover:text-gray-500">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <!-- Content -->
        <div class="space-y-4 mt-4">
          <div>
            <p class="text-sm text-gray-500">Customer ID</p>
            <p class="text-lg font-medium">{{ session.customerId }}</p>
          </div>
          
          <div>
            <p class="text-sm text-gray-500">Duration</p>
            <p class="text-lg font-medium">{{ session.duration }}</p>
          </div>
          
          <div>
            <p class="text-sm text-gray-500">Status</p>
            <p class="text-lg font-medium" :class="statusColor">
              ● {{ session.status }}
            </p>
          </div>

          <div>
            <p class="text-sm text-gray-500">Activity</p>
            <ul class="mt-2 space-y-2">
              <li v-for="(activity, index) in session.activities" 
                  :key="index"
                  class="text-sm bg-gray-50 p-2 rounded">
                {{ activity }}
              </li>
            </ul>
          </div>
        </div>

        <!-- Footer -->
        <div class="mt-6 flex justify-end space-x-3">
          <button 
            @click="$emit('close')"
            class="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>