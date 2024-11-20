import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import ChatView from '@/views/ChatView.vue'
import { chatService } from '@/services/api'

// Mock PDF service
vi.mock('@/services/api', () => ({
  chatService: {
    getPdfList: vi.fn(),
    sendMessage: vi.fn()
  }
}))

describe('ChatView', () => {
  let wrapper

  beforeEach(() => {
    const pinia = createPinia()
    
    // Mock successful PDF response
    chatService.getPdfList.mockResolvedValue({
      pdf_files: [{
        path: '/path/to/pdf',
        name: 'test.pdf',
        url: '/api/pdf/view/test.pdf',
        pages: 1
      }]
    })

    wrapper = mount(ChatView, {
      global: {
        plugins: [pinia]
      }
    })
  })

  it('initializes with correct customer ID', () => {
    expect(wrapper.vm.customerId).toBe('3694388_07012024')
  })

  it('loads PDFs on mount', async () => {
    await wrapper.vm.$nextTick()
    expect(chatService.getPdfList).toHaveBeenCalled()
    expect(wrapper.vm.pdfFiles.length).toBe(1)
  })

  it('handles message sending', async () => {
    const testMessage = 'Test message'
    chatService.sendMessage.mockResolvedValue({ response: 'Bot response' })

    wrapper.vm.input = testMessage
    await wrapper.vm.sendMessage()

    expect(wrapper.vm.messages).toContainEqual({
      type: 'user',
      content: testMessage
    })
    expect(wrapper.vm.messages).toContainEqual({
      type: 'bot',
      content: 'Bot response'
    })
  })

  it('handles session expiration', async () => {
    await wrapper.vm.handleSessionExpiration()
    expect(wrapper.vm.sessionError).toBeTruthy()
  })
})
