import { readFileSync } from 'node:fs'
import { defineConfig } from 'vitest/config'
import { loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

function backendUrl(backendOverride: string | undefined): string {
  if (backendOverride) return backendOverride
  try {
    const port = readFileSync('../backend/.port', 'utf8').trim()
    if (/^\d+$/.test(port)) return `http://127.0.0.1:${port}`
  } catch {
    // El backend puede no estar iniciado todavía.
  }
  return 'http://127.0.0.1:8710'
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '')
  const target = backendUrl(env.VITE_BACKEND_URL)
  return {
    plugins: [react(), tailwindcss()],
    server: {
      host: '127.0.0.1',
      port: 5710,
      strictPort: true,
      proxy: { '/api': { target }, '/docs': { target }, '/openapi.json': { target } },
    },
    test: {
      environment: 'jsdom',
      setupFiles: './src/test/setup.ts',
      css: true,
      exclude: ['e2e/**', 'node_modules/**', 'dist/**'],
    },
  }
})
