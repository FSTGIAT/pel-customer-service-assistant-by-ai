<template>
  <div class="flex h-screen bg-gray-100">
    <!-- Left Panel - PDF Viewer -->
    <div class="w-1/2 p-4 bg-white border-r border-gray-200">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-semibold">Customer Bill</h2>
        <div class="flex items-center space-x-2">
          <i class="fas fa-search text-gray-500"></i>
          <span class="text-sm text-gray-500">Search Document</span>
        </div>
      </div>
      <div class="bg-gray-100 h-full rounded-lg flex items-center justify-center">
        <i class="fas fa-file-pdf text-4xl text-gray-400"></i>
        <p class="text-gray-500 ml-2">PDF Viewer Area</p>
      </div>
    </div>

    <!-- Right Panel - Chat Interface -->
    <div class="w-1/2 flex flex-col">
      <!-- Customer Info Header -->
      <div class="bg-white p-4 border-b border-gray-200">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-lg font-semibold">Customer #{{ customerId }}</h2>
            <p class="text-sm text-gray-500">{{ customerName }} • {{ customerPlan }}</p>
          </div>
          <div class="flex items-center space-x-2 text-sm text-gray-500">
            <i class="fas fa-clock"></i>
            <span>Session: {{ sessionTime }}</span>
          </div>
        </div>
      </div>

      <!-- Chat Messages -->
      <div class="flex-1 overflow-y-auto p-4 space-y-4" ref="chatContainer">
        <div v-for="(message, index) in messages" :key="index" 
             :class="['flex', message.type === 'user' ? 'justify-end' : 'justify-start']">
          <div :class="['flex items-start space-x-2 max-w-[80%]', 
                       message.type === 'system' ? 'justify-center w-full' : '']">
            <div v-if="message.type === 'bot'" 
                 class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
              <i class="fas fa-robot text-blue-600"></i>
            </div>
            <div :class="['p-3 rounded-lg', 
                         message.type === 'user' ? 'bg-blue-600 text-white' :
                         message.type === 'bot' ? 'bg-gray-100 text-gray-800' :
                         'bg-gray-100 text-gray-500 text-sm w-full text-center']">
              {{ message.content }}
            </div>
            <div v-if="message.type === 'user'" 
                 class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
              <i class="fas fa-user text-gray-600"></i>
            </div>
          </div>
        </div>
      </div>

      <!-- Input Area -->
      <div class="p-4 bg-white border-t border-gray-200">
        <div class="flex items-center space-x-2">
          <input
            v-model="userInput"
            type="text"
            placeholder="Type your message..."
            class="flex-1 p-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            @keyup.enter="sendMessage"
          />
          <button
            @click="sendMessage"
            class="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none"
          >
            <i class="fas fa-paper-plane"></i>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  name: 'CustomerServiceChat',
  
  setup() {
    const messages = ref([])
    const userInput = ref('')
    const customerId = ref('1234')
    const customerName = ref('John Doe')
    const customerPlan = ref('Premium Plan')
    const sessionTime = ref('0:00')
    const chatContainer = ref(null)

    onMounted(() => {
      messages.value.push({
        type: 'system',
        content: 'Connected to billing support AI assistant'
      })
      messages.value.push({
        type: 'bot',
        content: `Hello! I see you're viewing the billing statement for customer #${customerId.value}. How can I help you today?`
      })
      
      startSessionTimer()
    })

    const startSessionTimer = () => {
      let seconds = 0
      setInterval(() => {
        seconds++
        const minutes = Math.floor(seconds / 60)
        const remainingSeconds = seconds % 60
        sessionTime.value = `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
      }, 1000)
    }

    const sendMessage = () => {
      if (!userInput.value.trim()) return

      messages.value.push({
        type: 'user',
        content: userInput.value
      })
      userInput.value = ''

      // Simulate bot response
      setTimeout(() => {
        messages.value.push({
          type: 'bot',
          content: 'I am processing your request...'
        })
      }, 1000)

      // Scroll to bottom after new message
      setTimeout(() => {
        if (chatContainer.value) {
          chatContainer.value.scrollTop = chatContainer.value.scrollHeight
        }
      }, 100)
    }

    return {
      messages,
      userInput,
      customerId,
      customerName,
      customerPlan,
      sessionTime,
      chatContainer,
      sendMessage
    }
  }
}
</script>
