import { describe, it, expect, beforeEach, vi } from 'vitest'
import { chatService } from '@/services/api'
import axios from 'axios'

vi.mock('axios')

describe('Chat Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('gets PDF list with session token', async () => {
    const mockResponse = {
      data: {
        pdf_files: [
          { name: 'test.pdf', url: '/api/pdf/view/test.pdf' }
        ]
      }
    }
    axios.post.mockResolvedValue(mockResponse)

    const result = await chatService.getPdfList('3694388_07012024', 'test_token')
    
    expect(axios.post).toHaveBeenCalledWith(
      '/api/legacy/trigger',
      { customer_id: '3694388_07012024' },
      expect.objectContaining({
        headers: expect.objectContaining({
          'Authorization': 'Bearer test_token'
        })
      })
    )
    expect(result.pdf_files).toHaveLength(1)
  })

  it('sends messages with context', async () => {
    const mockResponse = {
      data: { response: 'Test response' }
    }
    axios.post.mockResolvedValue(mockResponse)

    const result = await chatService.sendMessage(
      'test message',
      '3694388_07012024',
      [],
      'test.pdf',
      'test_token'
    )

    expect(axios.post).toHaveBeenCalledWith(
      '/api/chat',
      expect.objectContaining({
        message: 'test message',
        customerId: '3694388_07012024',
        pdf_path: 'test.pdf'
      }),
      expect.any(Object)
    )
  })
})
