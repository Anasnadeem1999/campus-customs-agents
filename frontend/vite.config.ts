import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

/**
 * Vite config for the Campus Customs desk.
 *
 * `npm run dev` serves the dashboard, which calls the FastAPI backend
 * directly at http://localhost:8000 (see src/api.ts). There is deliberately
 * no dev proxy: the browser should make a genuine cross-origin request, so
 * the backend's CORS allowance is actually exercised in development rather
 * than discovered to be wrong later.
 *
 * Port 5173, Vite's default and the one the brief names. `strictPort` is off
 * so that a machine already using 5173 gets 5174 instead of a hard failure —
 * Vite prints the port it actually bound, and the backend accepts any
 * localhost origin, so either works without touching CORS.
 *
 * (During development another project in this workspace held 5173 and this
 * dashboard was moved to 5180 to avoid serving that project's page by
 * mistake. A clean clone has 5173 free, so the default is restored.)
 */
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: false,
    open: true,
  },
})
