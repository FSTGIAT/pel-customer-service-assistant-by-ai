import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ChatView from '../../views/ChatView.vue'
import { createPinia } from 'pinia'

// Simple mock for chat service
vi.mock('../../services/api', () => ({
  chatService: {
    getPdfList: vi.fn(() => Promise.resolve({
      status: "success",
      pdf_files: [{
        name: "3694388_07012024.pdf",
        url: "/api/pdf/view/3694388_07012024.pdf",
        pages: 3
      }]
    })),
    sendMessage: vi.fn(() => Promise.resolve({ response: 'Test response' }))
  }
}))

describe('ChatView', () => {
  let wrapper

  beforeEach(() => {
    wrapper = mount(ChatView, {
      global: {
        plugins: [createPinia()],
        stubs: ['VuePdfEmbed']
      }
    })
  })

  it('initializes with correct ID', () => {
    expect(wrapper.vm.customerId).toBe('3694388_07012024')
  })
})  