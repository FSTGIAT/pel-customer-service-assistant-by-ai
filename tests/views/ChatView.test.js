import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ChatView from '../src/views/ChatView.vue'

// Mock PDF data from your actual response
const mockPdfResponse = {
  status: "success",
  customer_id: "3694388",
  pdf_files: [{
    path: "/root/telecom-customer-service/pdf-test/3694388_07012024.pdf",
    name: "3694388_07012024.pdf",
    url: "/api/pdf/view/3694388_07012024.pdf",
    pages: 3
  }]
}

// Simple mock of chat service
vi.mock('@/services/api', () => ({
  chatService: {
    getPdfList: vi.fn(() => Promise.resolve(mockPdfResponse)),
    sendMessage: vi.fn(() => Promise.resolve({ response: 'Test response' }))
  }
}))

describe('ChatView', () => {
  let wrapper

  beforeEach(() => {
    wrapper = mount(ChatView)
  })

  it('mounts with correct ID', () => {
    expect(wrapper.vm.customerId).toBe('3694388_07012024')
  })
})