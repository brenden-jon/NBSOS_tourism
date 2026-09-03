import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base must match the GitHub Pages sub-path: https://<user>.github.io/NBSOS_tourism/
export default defineConfig({
  plugins: [react()],
  // Data files have stable names (data/grid.geojson etc). Without a build-stamped query a
  // browser will happily serve a previous deploy's data against new code - which silently
  // broke every opportunity dossier during development.
  define: { __BUILD_ID__: JSON.stringify(Date.now().toString(36)) },
  base: process.env.VITE_BASE || '/NBSOS_tourism/',
  build: { outDir: 'dist', assetsInlineLimit: 0, chunkSizeWarningLimit: 1500 },
})
