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
