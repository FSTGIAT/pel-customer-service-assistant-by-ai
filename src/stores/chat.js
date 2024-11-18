// src/stores/chat.js
import { defineStore } from 'pinia'
import { chatService } from '@/services/api'

export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: [],
    customerInfo: null,
    isLoading: false,
    currentPdfUrl: null,
    error: null
  }),

  actions: {
    async loadCustomerInfo(customerId) {
      try {
        this.isLoading = true
        this.customerInfo = await chatService.getCustomerInfo(customerId)
        return this.customerInfo
      } catch (error) {
        this.error = 'Error loading customer information'
        throw error
      } finally {
        this.isLoading = false
      }
    },

    async sendMessage(message, customerId) {
      try {
        this.isLoading = true
        const response = await chatService.sendMessage(
          message,
          customerId,
          this.messages.slice(-5)
        )
        
        this.messages.push({
          type: 'bot',
          content: response.response
        })
        
        return response
      } catch (error) {
        this.error = 'Error sending message'
        throw error
      } finally {
        this.isLoading = false
      }
    },

    addMessage(message) {
      this.messages.push(message)
    },

    clearMessages() {
      this.messages = []
    },

    setCurrentPdfUrl(url) {
      this.currentPdfUrl = url
    }
  }
})
