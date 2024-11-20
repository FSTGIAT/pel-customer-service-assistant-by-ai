import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useSessionStore } from '@/stores/session'

describe('Session Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initializes session with customer ID', async () => {
    const store = useSessionStore()
    const customerId = '3694388_07012024'
    
    await store.initializeSession(customerId)
    
    expect(store.sessionToken).toBeTruthy()
    expect(store.customerData.id).toBe(customerId)
    expect(store.sessionError).toBeNull()
  })

  it('handles session refresh', async () => {
    const store = useSessionStore()
    const initialTime = store.lastActivity
    
    await store.refreshSession()
    
    expect(store.lastActivity).toBeGreaterThan(initialTime)
  })

  it('cleans up session data', () => {
    const store = useSessionStore()
    store.cleanup()
    
    expect(store.sessionToken).toBeNull()
    expect(store.sessionError).toBeNull()
    expect(store.customerData).toBeNull()
  })
})
