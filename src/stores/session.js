import { defineStore } from 'pinia'
import { ref } from 'vue'
import { chatService } from '../services/api'

export const useSessionStore = defineStore('session', () => {
  // State
  const sessionToken = ref(null)
  const sessionError = ref(null)
  const lastActivity = ref(Date.now())
  const customerData = ref({
    name: 'Customer Name',
    plan: 'Standard Plan',
    // other properties...
  })

  // Helper function
  const generateToken = (customerId) => {
    return `session_${customerId}_${Date.now()}_${Math.random().toString(36).substr(2)}`
  }

  // Actions
  const initializeSession = async (customerId) => {
    try {
      // Get PDF data first
      const pdfResponse = await chatService.getPdfList(customerId)
      if (!pdfResponse?.pdf_files?.length) {
        throw new Error('No customer data found')
      }

      // Generate session token
      sessionToken.value = generateToken(customerId)
      
      // Set customer data from PDF
      const pdfData = pdfResponse.pdf_files[0]
      customerData.value = {
        id: customerId,
        name: customerData?.name || 'Loading...',
        plan: customerData?.plan || 'Standard Plan',
        pdfInfo: {
          fileName: pdfData.name,
          date: pdfData.date,
          pages: pdfData.pages
        }
      }

      lastActivity.value = Date.now()
      sessionError.value = null
      return customerData.value
    } catch (error) {
      sessionError.value = error.message
      throw error
    }
  }

  const refreshSession = async () => {
    try {
      if (sessionToken.value) {
        // Generate completely new token
        sessionToken.value = generateToken(customerData.value.id)
        lastActivity.value = Date.now()
        sessionError.value = null
        return sessionToken.value
      } else {
        throw new Error('No active session')
      }
    } catch (error) {
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
    cleanup,
    // New getters
    getPdfInfo: () => customerData.value?.pdfInfo || null,
    getCustomerId: () => customerData.value?.id || '',
    // Helper methods
    isSessionActive: () => !!sessionToken.value,
    getLastActivity: () => lastActivity.value,
    getSessionError: () => sessionError.value
  }
})