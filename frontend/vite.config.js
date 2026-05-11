import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  envDir: path.resolve(__dirname, '..'), // read .env from project root, not frontend/
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        timeout: 0,       // no timeout — SSE streams can run for minutes
        proxyTimeout: 0,
      },
    },
  },
})
