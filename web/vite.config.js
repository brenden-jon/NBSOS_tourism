import { writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const BUILD_ID = Date.now().toString(36)

/**
 * GitHub Pages serves index.html with a short cache lifetime, so a returning visitor keeps
 * loading the previous bundle after a deploy and sees stale results with no indication that
 * anything is wrong. This writes the build id to a file the app can check at runtime.
 */
function emitVersion() {
  return {
    name: 'emit-version',
    closeBundle() {
      writeFileSync(join('dist', 'version.json'),
        JSON.stringify({ build: BUILD_ID }), 'utf8')
    },
  }
}

// base must match the GitHub Pages sub-path: https://<user>.github.io/NBSOS_tourism/
export default defineConfig({
  plugins: [react(), emitVersion()],
  // Data files have stable names (data/grid.geojson etc). Without a build-stamped query a
  // browser will happily serve a previous deploy's data against new code - which silently
  // broke every opportunity dossier during development.
  define: { __BUILD_ID__: JSON.stringify(BUILD_ID) },
  base: process.env.VITE_BASE || '/NBSOS_tourism/',
  build: { outDir: 'dist', assetsInlineLimit: 0, chunkSizeWarningLimit: 1500 },
})
