import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api/run': {
        target: 'http://localhost:8001', // Agent Service
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/run/, '/run')
      },
      '/api/mcp': {
        target: 'http://localhost:8000', // MCP Service
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/mcp/, '/mcp')
      },
      '/api/logs': {
        // Assuming logs are exposed on 8000 or via file reader?
        // If user says GET /logs exists on 8000, we proxy to it.
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/logs/, '/logs')
      }
    }
  }
})
