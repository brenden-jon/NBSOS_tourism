import { useEffect, useState } from 'react'

// SHA-256 of the shared access key. This is an ACCESS GATE, NOT SECURITY:
// the site is a static build of open data, and anyone with the bundle can read past it.
// It exists to keep an unfinished internal prototype out of casual circulation.
const KEY_HASH = '5c5d0673cb6507b00c71b494dd32d723cf15717284f7690eb662345b12c4c3d6'
const STORE = 'tnos-unlocked'

async function sha256(text) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text))
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join('')
}

export default function Gate({ children }) {
  const [ok, setOk] = useState(false)
  const [value, setValue] = useState('')
  const [error, setError] = useState('')
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    try { if (sessionStorage.getItem(STORE) === KEY_HASH) setOk(true) } catch { /* private mode */ }
    setChecking(false)
  }, [])

  async function submit(e) {
    e.preventDefault()
    const h = await sha256(value.trim())
    if (h === KEY_HASH) {
      try { sessionStorage.setItem(STORE, KEY_HASH) } catch { /* ignore */ }
      setOk(true)
    } else {
      setError('That access key was not recognised.')
      setValue('')
    }
  }

  if (checking) return null
  if (ok) return children

  return (
    <div className="min-h-screen flex items-center justify-center bg-wb-slateDk relative overflow-hidden">
      <div className="absolute inset-0 opacity-20"
        style={{ backgroundImage:
          'radial-gradient(circle at 20% 30%, #7FA23A 0%, transparent 45%), radial-gradient(circle at 78% 68%, #71AAD7 0%, transparent 50%)' }} />
      <form onSubmit={submit}
        className="relative z-10 w-full max-w-[440px] mx-5 bg-white rounded-lg shadow-2xl p-8">
        <div className="eyebrow mb-2">World Bank · Internal prototype</div>
        <h1 className="text-[22px] font-bold leading-snug text-wb-slateDk">
          Panama Tourism–Nature Opportunity Scan
        </h1>
        <p className="prose-wb mt-3 text-wb-muted text-[14px]">
          A prototype screening tool identifying where tourism investment, conservation,
          resilience and local jobs reinforce each other across Panama.
        </p>
        <label className="block mt-6 text-[12px] font-bold uppercase tracking-wider text-wb-slate">
          Access key
        </label>
        <input
          autoFocus type="password" value={value}
          onChange={e => { setValue(e.target.value); setError('') }}
          className="mt-2 w-full rounded border border-wb-line px-3 py-2.5 text-[15px]
                     focus:outline-none focus:border-wb-blue focus:ring-2 focus:ring-wb-blue/25"
          placeholder="Enter access key" />
        {error && <p className="mt-2 text-[13px] text-act-manage font-medium">{error}</p>}
        <button type="submit" className="btn-green w-full justify-center mt-4 py-2.5">Enter</button>
        <p className="mt-5 text-[11px] leading-relaxed text-wb-muted border-t border-wb-line pt-4">
          This gate restricts casual access only. The application is a static site built from
          open data and provides no server-side authentication.
        </p>
      </form>
    </div>
  )
}
