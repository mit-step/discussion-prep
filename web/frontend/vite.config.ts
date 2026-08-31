import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/discussion-prep/',
  server: {
    proxy: {
      '/discussion-prep/api': 'http://localhost:8000',
      '/discussion-prep/readings-pdf': 'http://localhost:8000',
    },
  },
})
