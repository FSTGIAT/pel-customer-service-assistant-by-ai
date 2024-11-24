// src/views/__tests__/ChatView.spec.js
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ChatView from '../ChatView.vue'


// Mock PDF data based on your actual JSON
const mockPdfResponse = {
  status: "success",
  customer_id: "3694388",
  pdf_files: [
    {
      path: "/root/telecom-customer-service/pdf-test/3694388_07012024.pdf",
      name: "3694388_07012024.pdf",
      url: "/api/pdf/view/3694388_07012024.pdf",
      pages: 3,
      date: "2024-01-07T00:00:00"
    }
  ]
}

// Mock bill data
const mockBillData = {
  total_amount: 174.48,
  phone_numbers: ["050-5148080", "050-3060366"],
  services: [
    {
      name: "Top פלאפון תיקונים שירות",
      price: 39.90
    }
  ],
  bill_period: "08/09/2024 - 07/10/2024"
}

// Mock chat service
vi.mock('@/services/api', () => ({
  chatService: {
    getPdfList: vi.fn().mockResolvedValue(mockPdfResponse),
    sendMessage: vi.fn().mockImplementation((message) => {
      // Simulate responses based on message content
      if (message.includes('total')) {
        return Promise.resolve({ 
          response: `החשבון הכולל הוא ${mockBillData.total_amount} ₪` 
        })
      }
      if (message.includes('phone')) {
        return Promise.resolve({ 
          response: `מספרי הטלפון בחשבונית: ${mockBillData.phone_numbers.join(', ')}` 
        })
      }
      return Promise.resolve({ response: 'איך אוכל לעזור?' })
    }),
  }
}))

describe('ChatView', () => {
  let wrapper

  beforeEach(() => {
    wrapper = mount(ChatView)
  })

  it('initializes with correct customer ID', () => {
    expect(wrapper.vm.customerId).toBe('3694388_07012024')
  })

  it('loads PDFs correctly', async () => {
    await wrapper.vm.initializeChat()
    expect(wrapper.vm.pdfFiles).toHaveLength(1)
    expect(wrapper.vm.totalPages).toBe(3)
  })

  it('handles PDF navigation', async () => {
    await wrapper.vm.initializeChat()
    
    // Test next/previous page
    await wrapper.vm.nextPage()
    expect(wrapper.vm.currentPage).toBe(2)
    
    await wrapper.vm.previousPage()
    expect(wrapper.vm.currentPage).toBe(1)
  })

  it('handles zoom controls', async () => {
    const initialScale = wrapper.vm.scale
    
    await wrapper.vm.zoomIn()
    expect(wrapper.vm.scale).toBeGreaterThan(initialScale)
    
    await wrapper.vm.zoomOut()
    expect(wrapper.vm.scale).toBe(initialScale)
  })

  it('sends messages and receives responses', async () => {
    wrapper.vm.input = 'מה סכום החשבון הכולל?'
    await wrapper.vm.sendMessage()
    
    const messages = wrapper.vm.messages
    expect(messages[messages.length - 1].content).toContain('174.48')
  })

  it('displays loading states correctly', async () => {
    wrapper.vm.isLoading = true
    await wrapper.vm.$nextTick()
    
    expect(wrapper.find('.animate-pulse').exists()).toBe(true)
    
    wrapper.vm.isLoading = false
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.animate-pulse').exists()).toBe(false)
  })

  it('handles Hebrew text correctly', async () => {
    const hebrewMessage = 'מה מספרי הטלפון בחשבון?'
    wrapper.vm.input = hebrewMessage
    await wrapper.vm.sendMessage()
    
    const messages = wrapper.vm.messages
    expect(messages[messages.length - 2].content).toBe(hebrewMessage)
    expect(messages[messages.length - 1].content).toContain('050-')
  })

  it('validates PDF data structure', async () => {
    await wrapper.vm.initializeChat()
    const firstPdf = wrapper.vm.pdfFiles[0]
    
    expect(firstPdf).toHaveProperty('path')
    expect(firstPdf).toHaveProperty('name')
    expect(firstPdf).toHaveProperty('url')
    expect(firstPdf).toHaveProperty('pages')
    expect(firstPdf.name).toMatch(/^\d{7}_\d{8}\.pdf$/)
  })
})