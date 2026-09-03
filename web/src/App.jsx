import { useEffect, useState } from 'react'
import Gate from './components/Gate.jsx'
import Overview from './pages/Overview.jsx'
import Strategy from './pages/Strategy.jsx'
import Explorer from './pages/Explorer.jsx'
import Analysis from './pages/Analysis.jsx'
import Opportunities from './pages/Opportunities.jsx'
import Methods from './pages/Methods.jsx'

const PAGES = [
  { id: 'overview',      label: 'Overview',            C: Overview },
  { id: 'strategy',      label: 'Government Strategy', C: Strategy },
  { id: 'explorer',      label: 'Data Explorer',       C: Explorer },
  { id: 'analysis',      label: 'Analysis',            C: Analysis },
  { id: 'opportunities', label: 'Opportunities',       C: Opportunities },
  { id: 'methods',       label: 'Methods & Limits',    C: Methods },
]

function useHashRoute() {
  const parse = () => {
    const raw = (window.location.hash || '#overview').slice(1)
    const [id, param] = raw.split('/')
    return { id: PAGES.some(p => p.id === id) ? id : 'overview', param }
  }
  const [route, setRoute] = useState(parse)
  useEffect(() => {
    const on = () => { setRoute(parse()); window.scrollTo({ top: 0 }) }
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  return route
}

function Header({ current }) {
  const [open, setOpen] = useState(false)
  return (
    <header className="sticky top-0 z-50 bg-white border-b border-wb-line shadow-sm">
      <div className="wrap flex items-center justify-between h-[62px]">
        <a href="#overview" className="flex items-center gap-3 group">
          <span className="grid place-items-center w-8 h-8 rounded bg-wb-green text-white
                           font-bold text-[13px] tracking-tight">TN</span>
          <span className="leading-tight">
            <span className="block text-[13px] font-bold text-wb-slateDk group-hover:text-wb-blueDk">
              Tourism–Nature Opportunity Scan
            </span>
            <span className="block text-[10.5px] uppercase tracking-[0.12em] text-wb-muted">
              Panama pilot · World Bank prototype
            </span>
          </span>
        </a>
        <nav className="hidden lg:flex items-center">
          {PAGES.map(p => (
            <a key={p.id} href={`#${p.id}`}
              className={`navlink ${current === p.id
                ? 'text-wb-blueDk border-b-2 border-wb-green'
                : 'text-wb-slate hover:text-wb-blueDk'}`}>{p.label}</a>
          ))}
        </nav>
        <button onClick={() => setOpen(o => !o)}
          className="lg:hidden text-wb-slate text-sm font-bold uppercase tracking-wider">
          {open ? 'Close' : 'Menu'}
        </button>
      </div>
      {open && (
        <nav className="lg:hidden border-t border-wb-line bg-white">
          {PAGES.map(p => (
            <a key={p.id} href={`#${p.id}`} onClick={() => setOpen(false)}
              className={`block px-6 py-3 text-[13px] font-semibold border-b border-wb-line
                ${current === p.id ? 'text-wb-blueDk bg-wb-wash' : 'text-wb-slate'}`}>
              {p.label}
            </a>
          ))}
        </nav>
      )}
    </header>
  )
}

function Footer() {
  return (
    <footer className="mt-20 bg-wb-slateDk text-white/80">
      <div className="wrap py-12 grid gap-10 md:grid-cols-3">
        <div>
          <div className="text-white font-bold text-[15px] mb-3">Tourism–Nature Opportunity Scan</div>
          <p className="text-[13px] leading-relaxed">
            An exploratory World Bank prototype adapting the Nature-Based Solutions Opportunity
            Scan to tourism investment planning. Panama pilot, 2026.
          </p>
        </div>
        <div>
          <div className="text-white font-bold text-[13px] uppercase tracking-wider mb-3">Sections</div>
          <ul className="space-y-1.5 text-[13px]">
            {PAGES.map(p => (
              <li key={p.id}><a className="hover:text-white" href={`#${p.id}`}>{p.label}</a></li>
            ))}
          </ul>
        </div>
        <div>
          <div className="text-white font-bold text-[13px] uppercase tracking-wider mb-3">Status</div>
          <p className="text-[13px] leading-relaxed">
            Screening-level analysis for discussion. Findings are analytical candidates requiring
            ecological, social, legal and stakeholder assessment before any investment or
            designation decision.
          </p>
        </div>
      </div>
      <div className="border-t border-white/15">
        <div className="wrap py-4 text-[11.5px] text-white/55">
          Built from open data. Sources, licences and limitations are documented under
          <a className="underline hover:text-white ml-1" href="#methods">Methods &amp; Limits</a>.
        </div>
      </div>
    </footer>
  )
}

export default function App() {
  const { id, param } = useHashRoute()
  const Page = PAGES.find(p => p.id === id).C
  return (
    <Gate>
      <div className="min-h-screen flex flex-col">
        <Header current={id} />
        <main className="flex-1"><Page param={param} /></main>
        <Footer />
      </div>
    </Gate>
  )
}
