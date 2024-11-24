import { beforeAll, afterEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// Setup Pinia
beforeAll(() => {
  setActivePinia(createPinia())
})

// Reset mocks after each test
afterEach(() => {
  vi.clearAllMocks()
})

// Mock timer functions
vi.useFakeTimers()

// Mock console to reduce noise in tests
console.log = vi.fn()
console.error = vi.fn()
console.warn = vi.fn()

// Mock fetch/XMLHttpRequest
global.fetch = vi.fn()
global.XMLHttpRequest = vi.fn()