import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSessionStore = defineStore('session', () => {
  // State
  const sessionToken = ref(null)
  const sessionError = ref(null)
  const lastActivity = ref(Date.now())
  const customerData = ref(null)

  // Actions
  const initializeSession = async (customerId) => {
    try {
      sessionToken.value = `session_${customerId}_${Date.now()}`
      customerData.value = {
        id: customerId,
        name: 'ורד כהן', // Default name
        plan: 'Premium Plan'
      }
      lastActivity.value = Date.now()
      sessionError.value = null
    } catch (error) {
      console.error('Session initialization failed:', error)
      sessionError.value = error.message
      throw error
    }
  }

  const refreshSession = async () => {
    try {
      if (sessionToken.value) {
        lastActivity.value = Date.now()
        sessionError.value = null
      } else {
        throw new Error('No active session')
      }
    } catch (error) {
      console.error('Session refresh failed:', error)
      sessionError.value = error.message
      throw error
    }
  }

  const getSessionToken = async () => sessionToken.value
  const getCustomerName = async () => customerData.value?.name || ''
  const getCustomerPlan = async () => customerData.value?.plan || ''
  
  const updateLastActivity = () => {
    lastActivity.value = Date.now()
  }

  const cleanup = () => {
    sessionToken.value = null
    sessionError.value = null
    customerData.value = null
  }

  return {
    // State
    sessionToken,
    sessionError,
    lastActivity,
    customerData,

    // Actions
    initializeSession,
    refreshSession,
    getSessionToken,
    getCustomerName,
    getCustomerPlan,
    updateLastActivity,
    cleanup
  }
})