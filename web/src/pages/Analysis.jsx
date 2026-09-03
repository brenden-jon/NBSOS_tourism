import { useMemo, useState } from 'react'
import MapCanvas from '../components/MapCanvas'
import Scatter from '../components/Scatter'
import { Hero, Section, Stat, Callout, Loading, ErrorBox, ScoreBar, ActionChip } from '../components/ui'
import { ACTIONS, FAMILIES } from '../lib/constants'
import { useData } from '../lib/useData'

const RAMP = ['#F2F6F4', '#CFE0D6', '#9DC3AE', '#6BA189', '#3E7F68', '#1F5C4A']

const MODES = [
  { key: 'primary', label: 'Recommendation', kind: 'cat' },
  ...FAMILIES.map(f => ({ key: f.key, label: f.label, kind: 'num', desc: f.desc })),
  { key: 'protection_gap', label: 'Protection gap', kind: 'num',
    desc: 'Nature or resilience value not currently held under strict protection.' },
  { key: 'supply_gap', label: 'Tourism supply gap', kind: 'num',
    desc: 'Natural attraction minus existing tourism development.' },
  { key: 'sensitivity', label: 'Ecological sensitivity', kind: 'num',
    desc: 'Biodiversity value weighted with strict protection — damps development recommendations.' },
]

function colourExpr(mode) {
  if (mode.kind === 'cat') {
    return ['match', ['get', 'primary'],
      'PROTECT', ACTIONS.PROTECT.color, 'INVEST', ACTIONS.INVEST.color,
      'ADAPT', ACTIONS.ADAPT.color, 'MANAGE', ACTIONS.MANAGE.color, '#CBD5DC']
  }
  return ['interpolate', ['linear'], ['coalesce', ['get', mode.key], 0],
    0, RAMP[0], 20, RAMP[1], 40, RAMP[2], 60, RAMP[3], 80, RAMP[4], 100, RAMP[5]]
}

function Inspector({ f, onClose }) {
  if (!f) return null
  return (
    <div className="absolute top-3 right-3 z-10 w-[310px] max-h-[calc(100%-24px)] overflow-y-auto
                    bg-white rounded-md shadow-xl border border-wb-line">
      <div className="p-4 border-b border-wb-line flex items-start justify-between gap-2">
        <div>
          <div className="eyebrow">{f.district}, {f.province}</div>
          <div className="font-bold text-[14px] text-wb-slateDk mt-0.5 capitalize">{f.zone} cell</div>
        </div>
        <button onClick={onClose} className="text-wb-muted hover:text-wb-slateDk text-lg leading-none">×</button>
      </div>
      <div className="p-4 space-y-4">
        <div>
          <ActionChip action={f.primary} />
          {f.secondary && <div className="mt-2 text-[11.5px] text-wb-muted">
            Also scores as: {String(f.secondary).split('; ').map(s => ACTIONS[s]?.label).join(', ')}
          </div>}
        </div>
        <div className="space-y-2.5">
          {FAMILIES.map(fam => (
            <ScoreBar key={fam.key} label={fam.label} value={f[fam.key]}
              color={ACTIONS[f.primary]?.color || '#3E7CAB'} />
          ))}
        </div>
        <div className="pt-3 border-t border-wb-line grid grid-cols-2 gap-x-3 gap-y-2 text-[12px]">
          <Kv k="Forest cover" v={`${(100 * (f.lc_tree ?? 0)).toFixed(0)}%`} />
          <Kv k="Mangrove" v={`${(100 * (f.lc_mangrove ?? 0)).toFixed(1)}%`} />
          <Kv k="Shallow shelf" v={`${(100 * (f.shallow_frac ?? 0)).toFixed(0)}%`} />
          <Kv k="Protected" v={`${(100 * (f.pa_frac ?? 0)).toFixed(0)}%`} />
          <Kv k="Strict IUCN" v={`${(100 * (f.pa_strict_frac ?? 0)).toFixed(0)}%`} />
          <Kv k="Relief" v={`${Math.round(f.relief_m ?? 0)} m`} />
          <Kv k="Species recorded" v={Math.round(f.gbif_species ?? 0)} />
          <Kv k="To gateway" v={`${Number(f.tt_gateway_h ?? 0).toFixed(1)} h`} />
          <Kv k="Population" v={Math.round(f.population ?? 0).toLocaleString()} />
          <Kv k="Accommodation" v={Math.round(f.n_accommodation ?? 0)} />
        </div>
        {f.pa_name && <div className="text-[12px]"><span className="text-wb-muted">Protected area: </span>
          <span className="font-semibold text-wb-slateDk">{f.pa_name}</span></div>}
        {f.ecoregion && <div className="text-[12px]"><span className="text-wb-muted">Ecoregion: </span>{f.ecoregion}</div>}
        <div className="pt-3 border-t border-wb-line text-[12px]">
          <span className="text-wb-muted">Government plan: </span>
          {f.gov_dest ? <span className="font-semibold text-wb-slateDk">{f.gov_dest} ({f.gov_relation})</span>
                      : <span className="text-wb-slate">outside priority destinations</span>}
        </div>
      </div>
    </div>
  )
}

const Kv = ({ k, v }) => (
  <div><div className="text-wb-muted text-[11px]">{k}</div><div className="font-semibold text-wb-slateDk">{v}</div></div>
)

export default function Analysis() {
  const { data: grid, loading, error } = useData('grid.geojson')
  const { data: dests } = useData('gov_destinations.geojson')
  const { data: pas } = useData('protected_areas.geojson')
  const { data: s } = useData('summary.json')
  const [mode, setMode] = useState(MODES[0])
  const [basemap, setBasemap] = useState('light')
  const [sel, setSel] = useState(null)
  const [showGov, setShowGov] = useState(true)
  const [showPA, setShowPA] = useState(false)
  const [zoneFilter, setZoneFilter] = useState('all')

  const filter = useMemo(() => {
    if (zoneFilter === 'land') return ['in', ['get', 'zone'], ['literal', ['inland', 'coastal']]]
    if (zoneFilter === 'sea') return ['in', ['get', 'zone'], ['literal', ['marine', 'nearshore']]]
    return null
  }, [zoneFilter])

  const layers = useMemo(() => {
    const out = []
    if (grid) {
      out.push({ id: 'grid-fill', data: grid, type: 'fill', filter,
        paint: { 'fill-color': colourExpr(mode), 'fill-opacity': 0.82 } })
      out.push({ id: 'grid-line', data: grid, type: 'line', filter,
        paint: { 'line-color': '#ffffff', 'line-width': 0.25, 'line-opacity': 0.5 } })
    }
    if (pas && showPA) {
      out.push({ id: 'pa-line', data: pas, type: 'line',
        paint: { 'line-color': '#1F5C4A', 'line-width': 1, 'line-dasharray': [3, 2] } })
    }
    if (dests && showGov) {
      out.push({ id: 'gov-line', data: dests, type: 'line',
        paint: {
          'line-color': ['match', ['get', 'tier'], 'priority', '#F5D108', '#71AAD7'],
          'line-width': ['match', ['get', 'tier'], 'priority', 2.4, 1.4],
        } })
    }
    if (sel) {
      out.push({ id: 'grid-sel', data: grid, type: 'line',
        filter: ['==', ['get', 'h3'], sel.h3],
        paint: { 'line-color': '#2E3944', 'line-width': 2.6 } })
    }
    return out
  }, [grid, dests, pas, mode, showGov, showPA, sel, filter])

  if (loading) return <Loading what="the national screening grid" />
  if (error) return <div className="wrap py-16"><ErrorBox message={error} /></div>

  return (
    <>
      <Hero eyebrow="National screening" title="The analysis, cell by cell"
        lead="Every 37 km² hexagon across Panama's land area and the coastal water around it — 10 km from every coastline, extended to 30 km over shallow shelf and marine protected areas — scored on six indicator families and classified into a recommendation type. Colour the map by any indicator; click any cell to see the evidence behind it." />

      <div className="wrap py-8">
        <div className="flex flex-wrap items-center gap-2 mb-4">
          {MODES.map(m => (
            <button key={m.key} onClick={() => setMode(m)}
              className={`px-3 py-1.5 rounded text-[12px] font-semibold border transition-colors
                ${mode.key === m.key ? 'bg-wb-slateDk text-white border-wb-slateDk'
                                     : 'bg-white text-wb-slate border-wb-line hover:border-wb-blue'}`}>
              {m.label}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 mb-3 text-[12px] text-wb-slate">
          <label className="inline-flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={showGov} onChange={e => setShowGov(e.target.checked)}
              className="accent-wb-green" /> Government priority destinations
          </label>
          <label className="inline-flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={showPA} onChange={e => setShowPA(e.target.checked)}
              className="accent-wb-green" /> Protected areas (SINAP 2025)
          </label>
          <span className="inline-flex items-center gap-1.5">
            Show:
            {['all', 'land', 'sea'].map(z => (
              <button key={z} onClick={() => setZoneFilter(z)}
                className={`px-2 py-0.5 rounded text-[11px] font-semibold capitalize
                  ${zoneFilter === z ? 'bg-wb-blue text-white' : 'bg-wb-wash text-wb-slate'}`}>{z}</button>
            ))}
          </span>
        </div>

        <div className="card overflow-hidden relative">
          <MapCanvas className="h-[600px]" layers={layers} basemap={basemap}
            onBasemapChange={setBasemap} cursorLayers={['grid-fill']}
            onFeatureClick={p => setSel(p)}>
            <Inspector f={sel} onClose={() => setSel(null)} />
            <div className="absolute bottom-6 left-3 z-10 bg-white/95 backdrop-blur rounded-md
                            border border-wb-line shadow px-3.5 py-3 max-w-[260px]">
              <div className="text-[11px] font-bold uppercase tracking-wider text-wb-slateDk mb-2">
                {mode.label}
              </div>
              {mode.kind === 'cat' ? (
                <div className="space-y-1.5">
                  {Object.values(ACTIONS).map(a => (
                    <div key={a.key} className="flex items-center gap-2 text-[11.5px] text-wb-slate">
                      <span className="w-3.5 h-3.5 rounded-sm" style={{ backgroundColor: a.color }} />
                      {a.label}
                    </div>
                  ))}
                </div>
              ) : (
                <>
                  <div className="flex h-3 rounded overflow-hidden">
                    {RAMP.map(c => <div key={c} className="flex-1" style={{ backgroundColor: c }} />)}
                  </div>
                  <div className="flex justify-between text-[10.5px] text-wb-muted mt-1">
                    <span>0</span><span>50</span><span>100</span>
                  </div>
                  {mode.desc && <p className="text-[10.5px] leading-snug text-wb-muted mt-2">{mode.desc}</p>}
                </>
              )}
            </div>
          </MapCanvas>
        </div>
        <p className="mt-3 text-[11.5px] text-wb-muted">
          Yellow outlines are PMTS 2025–2030 priority destinations; blue outlines are destinations
          with recent ATP action plans. Boundaries are derived from official district units — see
          Government Strategy.
        </p>
      </div>

      {s && (
        <Section tint eyebrow="What the national picture shows" title="Four findings from the screening grid">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8">
            <Stat value={`${s.share_in_gov_dest}%`} label="Inside a priority destination"
              sub={`${s.cells_in_gov_dest.toLocaleString()} of ${s.cells.toLocaleString()} cells. The other ${(100 - s.share_in_gov_dest).toFixed(1)}% is where new opportunities can appear.`} />
            <Stat value={s.corr_nav_tdl} label="Correlation, attraction vs supply"
              sub="Weak correlation means Panama's tourism supply is only loosely aligned with where its natural attraction actually is." />
            <Stat value={s.cells_high_nav_low_tdl.toLocaleString()} label="High-nature, low-supply cells"
              sub="Attraction ≥60 and development ≤40 — the raw pool of latent destination potential." />
            <Stat value={`${s.strict_protected_share}%`} label="Under strict protection"
              sub={`Against ${s.protected_share}% with some protected status — the gap the Protect/Restore class targets.`} />
          </div>
          <div className="grid gap-5 lg:grid-cols-2 mb-5">
            <div className="card p-5">
              <div className="h-sub">Natural attraction against existing tourism supply</div>
              <p className="prose-wb text-[13px] mt-1.5 mb-3">
                Each point is one screening cell, coloured by its recommendation type. The dashed
                line is where development matches natural draw. Panama's mass sits well below it:
                the country has far more natural attraction than it has tourism supply to serve it,
                and the shaded quadrant is where that gap is largest.
              </p>
              <Scatter features={(grid?.features || []).map(f => f.properties)}
                x="TDL" y="NAV" xLabel="Tourism development (TDL)"
                yLabel="Nature attraction (NAV)" height={360} />
            </div>
            <div className="card p-5">
              <div className="h-sub">Biodiversity value against strict protection</div>
              <p className="prose-wb text-[13px] mt-1.5 mb-3">
                The vertical spread on the left is the protection gap: cells carrying high
                biodiversity value with little or no strict IUCN protection. These drive the
                Protect / Restore recommendations.
              </p>
              <Scatter features={(grid?.features || []).map(f => ({
                  ...f.properties,
                  strictpct: 100 * (f.properties.pa_strict_frac ?? 0) }))}
                x="strictpct" y="BCV" xLabel="Area under strict IUCN protection (%)"
                yLabel="Biodiversity value (BCV)" height={360} />
            </div>
          </div>
          <div className="grid gap-5 lg:grid-cols-2">
            <div className="card p-5">
              <div className="h-sub mb-3">Cells by recommendation type</div>
              {Object.values(ACTIONS).map(a => {
                const n = s.by_action[a.key] ?? 0
                const pctv = 100 * n / s.cells
                return (
                  <div key={a.key} className="mb-3 last:mb-0">
                    <div className="flex justify-between text-[12.5px] mb-1">
                      <span className="font-semibold text-wb-slateDk">{a.label}</span>
                      <span className="text-wb-muted tabular-nums">{n.toLocaleString()} · {pctv.toFixed(0)}%</span>
                    </div>
                    <div className="h-2 bg-wb-line rounded-full overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${pctv}%`, backgroundColor: a.color }} />
                    </div>
                  </div>
                )
              })}
            </div>
            <Callout title="How to read the classification" tone="blue">
              <p>
                Each cell gets the recommendation type it fits best, but the fit scores for all four
                are kept. A cell classified <strong>Protect / Restore</strong> that also scores highly
                for <strong>Invest</strong> is precisely the interesting case: conservation and
                tourism investment pointing at the same place.
              </p>
              <p className="mt-2.5">
                The <em>Invest</em> fit score is deliberately damped where biodiversity value and
                strict protection are both very high, so the tool does not recommend building in
                every accessible beautiful place.
              </p>
            </Callout>
          </div>
        </Section>
      )}
    </>
  )
}
