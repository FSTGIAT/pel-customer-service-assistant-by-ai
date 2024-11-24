import { beforeEach, describe, expect, it, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSessionStore } from '../../stores/session'

const mockPdfResponse = {
    status: "success",
    customer_id: "3694388",
    pdf_files: [{
      path: "/root/telecom-customer-service/pdf-test/3694388_07012024.pdf",
      name: "3694388_07012024.pdf",
      url: "/api/pdf/view/3694388_07012024.pdf",
      pages: 3,
      date: "2024-01-07",
      customerName: "ורד כהן",
      plan: "תוכנית פלאפון"
    }]
  }

  vi.mock('../../services/api', () => {
    return {
      chatService: {
        getPdfList: () => Promise.resolve(mockPdfResponse)
      }
    }
  })
  
  vi.mock('axios', () => {
    return {
      create: () => ({
        interceptors: {
          request: { use: () => {} },
          response: { use: () => {} }
        },
        post: () => Promise.resolve({ data: mockPdfResponse })
      })
    }
  })

  describe('Session Store', () => {
    beforeEach(() => {
      setActivePinia(createPinia())
      vi.useFakeTimers()
    })

  it('initializes session with correct data', async () => {
    const store = useSessionStore()
    const customerId = '3694388_07012024'
    await store.initializeSession(customerId)
    
    expect(store.sessionToken).toBeTruthy()
    expect(store.customerData.id).toBe(customerId)
    expect(store.sessionError).toBeNull()
  })

  it('handles token refreshing', async () => {
    const store = useSessionStore()
    await store.initializeSession('3694388_07012024')
    const initialToken = await store.getSessionToken()
    
    vi.advanceTimersByTime(1000)
    await store.refreshSession()
    const newToken = await store.getSessionToken()
    
    expect(newToken).not.toBe(initialToken)
  })

  it('manages activity tracking', () => {
    const store = useSessionStore()
    const initialTime = store.lastActivity
    
    vi.advanceTimersByTime(1000)
    store.updateLastActivity()
    
    expect(store.lastActivity).toBeGreaterThan(initialTime)
  })

  it('performs proper cleanup', async () => {
    const store = useSessionStore()
    await store.initializeSession('3694388_07012024')
    store.cleanup()

    expect(store.sessionToken).toBeNull()
    expect(store.customerData).toBeNull()
    expect(store.sessionError).toBeNull()
  })

  it('returns customer information', async () => {
    const store = useSessionStore()
    await store.initializeSession('3694388_07012024')
    
    expect(await store.getCustomerName()).toBeTruthy()
    expect(await store.getCustomerPlan()).toBeTruthy()
  })

  it('handles session errors correctly', async () => {
    const store = useSessionStore()
    
    try {
      await store.refreshSession()
    } catch (error) {
      expect(error.message).toBe('No active session')
      expect(store.sessionError).toBeTruthy()
    }
  })
})