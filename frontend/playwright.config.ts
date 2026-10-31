import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from '@playwright/test'

// Puertos sólo de prueba, distintos de los de desarrollo (5710, 8710): nunca se reutiliza un
// servidor que hable con la cuenta real (ADR-10).
const ports = { smartsheet: 8791, gis: 8792, backend: 8793, frontend: 5791 }
const backendDir = fileURLToPath(new URL('../backend/', import.meta.url))
const python = path.join(
  backendDir,
  '.venv',
  process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python',
)

function backendServer(module: string, port: number, readyPath: string, args = '') {
  return {
    command: `"${python}" -m ${module} --port ${port} ${args}`,
    cwd: backendDir,
    url: `http://127.0.0.1:${port}${readyPath}`,
    reuseExistingServer: false,
  }
}

export default defineConfig({
  testDir: './e2e',
  testMatch: '**/*.spec.ts',
  reporter: 'list',
  use: { baseURL: `http://127.0.0.1:${ports.frontend}` },
  webServer: [
    backendServer('tests.fake_smartsheet', ports.smartsheet, '/docs'),
    backendServer('tests.fake_gis', ports.gis, '/_fake/calls'),
    backendServer(
      'tests.e2e_backend',
      ports.backend,
      '/api/health',
      `--smartsheet ${ports.smartsheet} --gis ${ports.gis} --frontend ${ports.frontend}`,
    ),
    {
      command: `npx vite --port ${ports.frontend} --strictPort`,
      url: `http://127.0.0.1:${ports.frontend}`,
      env: { VITE_BACKEND_URL: `http://127.0.0.1:${ports.backend}` },
      reuseExistingServer: false,
    },
  ],
})
