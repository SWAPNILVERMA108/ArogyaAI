import { defineConfig } from 'vitest/config'

// Runs against a live backend (see docs/testing.md). Not part of `npm test`.
export default defineConfig({
  test: {
    environment: 'jsdom',
    environmentOptions: { jsdom: { url: 'http://localhost:5173' } },
    globals: true,
    include: ['src/test/integration/**/*.test.js'],
    testTimeout: 60000,
  },
})
