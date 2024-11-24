import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./tests/setup.js'],
    mockReset: true,
    clearMocks: true,
    restoreMocks: true,
    deps: {
      inline: ['vue', 'pinia']
    }
  }
})