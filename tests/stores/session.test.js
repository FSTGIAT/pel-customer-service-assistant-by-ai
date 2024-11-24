import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSessionStore } from '../../src/stores/session'


describe('Session Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initializes session with customer ID', async () => {
    const store = useSessionStore()
    await store.initializeSession('3694388_07012024')
    expect(store.sessionToken).toBeTruthy()
  })

  it('handles session refresh', async () => {
    const store = useSessionStore()
    await store.initializeSession('3694388_07012024')
    await store.refreshSession()
    expect(store.sessionToken).toBeTruthy()
  })

  it('cleans up session data', () => {
    const store = useSessionStore()
    store.cleanup()
    expect(store.sessionToken).toBeNull()
  })
})