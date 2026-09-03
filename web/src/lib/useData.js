import { useEffect, useState } from 'react'
import { dataUrl } from './constants'

const cache = new Map()

export function useData(file) {
  const [state, setState] = useState(() =>
    cache.has(file) ? { data: cache.get(file), loading: false, error: null }
                    : { data: null, loading: true, error: null })

  useEffect(() => {
    if (cache.has(file)) { setState({ data: cache.get(file), loading: false, error: null }); return }
    let alive = true
    setState({ data: null, loading: true, error: null })
    fetch(dataUrl(file))
      .then(r => { if (!r.ok) throw new Error(`${r.status} ${r.statusText}`); return r.json() })
      .then(j => { cache.set(file, j); if (alive) setState({ data: j, loading: false, error: null }) })
      .catch(e => alive && setState({ data: null, loading: false, error: e.message }))
    return () => { alive = false }
  }, [file])

  return state
}


/**
 * One-shot staleness check. Compares the build id compiled into this bundle against the one
 * the server is currently publishing; if they differ, the browser is running a cached bundle
 * from a previous deploy and is reloaded once. Guarded by sessionStorage so a genuine
 * mismatch can never turn into a reload loop.
 */
const RELOAD_FLAG = 'tnos-reloaded-for'

export async function ensureLatestBuild() {
  // eslint-disable-next-line no-undef
  const mine = typeof __BUILD_ID__ !== 'undefined' ? __BUILD_ID__ : null
  if (!mine) return
  try {
    const r = await fetch(`${import.meta.env.BASE_URL}version.json?t=${Date.now()}`,
      { cache: 'no-store' })
    if (!r.ok) return
    const { build } = await r.json()
    if (!build || build === mine) return
    if (sessionStorage.getItem(RELOAD_FLAG) === build) return  // already tried for this build
    sessionStorage.setItem(RELOAD_FLAG, build)
    window.location.reload()
  } catch {
    /* offline or blocked - keep showing what we have */
  }
}
