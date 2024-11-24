// src/stores/__tests__/session.spec.js
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSessionStore } from '../session'

describe('Session Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initializes session with customer ID', async () => {
    const store = useSessionStore()
    await store.initializeSession('3694388_07012024')
    
    expect(store.sessionToken).toBeTruthy()
    expect(store.sessionError).toBeNull()
  })

  it('handles session expiration', async () => {
    const store = useSessionStore()
    await store.initializeSession('3694388_07012024')
    
    // Simulate timeout
    await new Promise(resolve => setTimeout(resolve, 5000))
    
    const token = await store.getSessionToken()
    expect(token).toBeTruthy()
  })

  it('updates last activity', async () => {
    const store = useSessionStore()
    const initialTime = store.lastActivity
    
    await new Promise(resolve => setTimeout(resolve, 100))
    store.updateLastActivity()
    
    expect(store.lastActivity).toBeGreaterThan(initialTime)
  })

  it('cleans up on unmount', () => {
    const store = useSessionStore()
    store.cleanup()
    
    expect(store.sessionToken).toBeNull()
    expect(store.customerData).toBeNull()
  })
})