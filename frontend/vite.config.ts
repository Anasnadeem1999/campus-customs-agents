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
 * Port 5180 rather than Vite's default 5173. Another project in this
 * workspace already holds 5173, and the first run of this dashboard served
 * that project's storefront instead — the browser looked fine and was showing
 * the wrong application entirely. `strictPort` makes a clash fail loudly
 * rather than slide somewhere else quietly. The backend accepts any localhost
 * origin, so the port number itself does not matter to CORS.
 */
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5180,
    strictPort: true,
    open: true,
  },
})
