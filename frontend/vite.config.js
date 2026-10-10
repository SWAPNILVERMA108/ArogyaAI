import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  test: {
    environment: 'jsdom',
    // Matches the backend's default CORS_ALLOWED_ORIGINS so integration tests behave like the real app.
    environmentOptions: { jsdom: { url: 'http://localhost:5173' } },
    globals: true,
    setupFiles: './src/test/setup.js',
    exclude: ['node_modules/**', 'src/test/integration/**'],
  },
})
