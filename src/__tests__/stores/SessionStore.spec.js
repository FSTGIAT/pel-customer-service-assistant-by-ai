import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSessionStore } from '@/stores/session'

describe('Session Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('handles session', async () => {
    const store = useSessionStore()
    await store.initializeSession('3694388_07012024')
    expect(store.sessionToken).toBeTruthy()
  })
})