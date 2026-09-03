import { useEffect, useMemo, useState } from 'react'
import MapCanvas from '../components/MapCanvas'
import { Hero, Section, Callout, Loading, ErrorBox, ScoreBar, ActionChip, GovChip } from '../components/ui'
import { ACTIONS, FAMILIES, GOV_RELATION } from '../lib/constants'
import { useData } from '../lib/useData'

function Bullets({ title, items, icon }) {
  if (!items?.length) return null
  return (
    <div>
      <div className="eyebrow mb-2">{icon} {title}</div>
      <ul className="space-y-2">
        {items.map((t, i) => (
          <li key={i} className="flex gap-2.5 prose-wb text-[13.5px]">
            <span className="mt-[7px] shrink-0 w-1.5 h-1.5 rounded-full bg-wb-green" />
            <span>{t}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function Para({ title, text, icon }) {
  if (!text) return null
  return (
    <div>
      <div className="eyebrow mb-2">{icon} {title}</div>
      <p className="prose-wb text-[13.5px]">{text}</p>
    </div>
  )
}

function Detail({ area, narr, onClose }) {
  if (!area) return null
  const n = narr || {}
  const colour = ACTIONS[area.action]?.color || '#3E7CAB'
  return (
    <div className="card overflow-hidden">
      <div className="p-6 border-b border-wb-line" style={{ borderTop: `4px solid ${colour}` }}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="chip bg-wb-wash text-wb-slate border border-wb-line">#{area.rank}</span>
              <ActionChip action={area.action} />
              <GovChip relation={area.gov_relation} />
              {area.is_comarca === 1 && (
                <span className="chip bg-wb-yellow/20 text-[#8a6d00] border border-wb-yellow">Indigenous comarca</span>
              )}
            </div>
            <h3 className="text-[22px] font-bold text-wb-slateDk leading-tight">{area.name}</h3>
            <div className="text-[12.5px] text-wb-muted mt-1">
              {area.districts} · {area.provinces} · {Math.round(area.area_km2).toLocaleString()} km² ({area.n_cells} cells)
            </div>
          </div>
          <button onClick={onClose} className="text-wb-muted hover:text-wb-slateDk text-xl leading-none shrink-0">×</button>
        </div>
        {n.headline && <p className="mt-4 text-[15px] leading-relaxed text-wb-slateDk font-medium">{n.headline}</p>}
      </div>

      <div className="p-6 grid gap-7 lg:grid-cols-[1fr_260px]">
        <div className="space-y-7 order-2 lg:order-1">
          <Bullets title="Why here" items={n.why_here} />
          <Para title="Natural assets" text={n.natural_assets} />
          <Para title="Tourism context and access" text={n.tourism_context} />
          <Para title="Biodiversity and protection" text={n.biodiversity} />
          <Para title="Resilience contribution" text={n.resilience} />
          <div className="grid gap-6 sm:grid-cols-2">
            <Bullets title="Recommended conservation action" items={n.conservation_action} />
            <Bullets title="Recommended tourism investment" items={n.tourism_investment} />
          </div>
          <Para title="Local jobs and enterprise" text={n.jobs} />
          <div className="grid gap-6 sm:grid-cols-2">
            <Bullets title="Risks and trade-offs" items={n.risks} />
            <Bullets title="Further analysis needed" items={n.further_analysis} />
          </div>
          <Callout title="Relationship to the government plan"
            tone={area.gov_relation === 'new' ? 'blue' : area.gov_relation === 'refines' ? 'amber' : 'green'}>
            {n.gov_alignment}
          </Callout>
        </div>

        <aside className="space-y-5 order-1 lg:order-2">
          <div className="card p-4 bg-wb-wash">
            <div className="eyebrow mb-3">Indicator profile</div>
            <div className="space-y-2.5">
              {FAMILIES.map(f => <ScoreBar key={f.key} label={f.label} value={area[f.key]} color={colour} />)}
            </div>
          </div>
          <div className="card p-4">
            <div className="eyebrow mb-3">Key measures</div>
            <dl className="space-y-2 text-[12px]">
              {[
                ['Protected', `${(100 * area.pa_frac).toFixed(0)}%`],
                ['Strict IUCN', `${(100 * area.pa_strict_frac).toFixed(0)}%`],
                ['Forest cover', `${(100 * area.tree_frac).toFixed(0)}%`],
                ['Mangrove', `${(area.mangrove_frac * area.area_km2).toFixed(0)} km²`],
                ['Shallow shelf', `${(100 * area.shallow_frac).toFixed(0)}%`],
                ['Local relief', `${Math.round(area.relief_m)} m`],
                ['Species / cell', Math.round(area.gbif_species)],
                ['To gateway', `${Number(area.tt_gateway_h).toFixed(1)} h`],
                ['Population', Math.round(area.population).toLocaleString()],
                ['Accommodation', Math.round(area.n_accommodation)],
                ['Food service', Math.round(area.n_food_service)],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between gap-3 border-b border-wb-line pb-1.5 last:border-0">
                  <dt className="text-wb-muted">{k}</dt>
                  <dd className="font-semibold text-wb-slateDk tabular-nums">{v}</dd>
                </div>
              ))}
            </dl>
          </div>
          {area.pa_names && (
            <div className="card p-4">
              <div className="eyebrow mb-2">Protected areas here</div>
              <div className="text-[12.5px] text-wb-slate leading-relaxed">{area.pa_names.replace(/; /g, ' · ')}</div>
            </div>
          )}
        </aside>
      </div>
    </div>
  )
}

export default function Opportunities({ param }) {
  const { data: opps, loading, error } = useData('opportunity_areas.geojson')
  const { data: narr } = useData('narratives.json')
  const { data: dests } = useData('gov_destinations.geojson')
  const [basemap, setBasemap] = useState('light')
  const [selId, setSelId] = useState(param || null)
  const [fAction, setFAction] = useState('ALL')
  const [fGov, setFGov] = useState('ALL')

  useEffect(() => { if (param) setSelId(param) }, [param])

  const areas = useMemo(() => {
    if (!opps) return []
    return opps.features.map(f => f.properties).sort((a, b) => a.rank - b.rank)
  }, [opps])

  const shown = useMemo(() => areas.filter(a =>
    (fAction === 'ALL' || a.action === fAction) &&
    (fGov === 'ALL' || a.gov_relation === fGov)), [areas, fAction, fGov])

  const selected = areas.find(a => a.cluster_id === selId) || null
  const selNarr = narr?.areas?.find(n => n.cluster_id === selId) || null

  const layers = useMemo(() => {
    if (!opps) return []
    const ids = new Set(shown.map(a => a.cluster_id))
    const filtered = { type: 'FeatureCollection',
      features: opps.features.filter(f => ids.has(f.properties.cluster_id)) }
    const out = []
    if (dests) out.push({ id: 'gov-line', data: dests, type: 'line',
      paint: { 'line-color': '#8EA0AF', 'line-width': 1, 'line-dasharray': [4, 3] } })
    out.push({ id: 'opp-fill', data: filtered, type: 'fill',
      paint: {
        'fill-color': ['match', ['get', 'action'],
          'PROTECT', ACTIONS.PROTECT.color, 'INVEST', ACTIONS.INVEST.color,
          'ADAPT', ACTIONS.ADAPT.color, 'MANAGE', ACTIONS.MANAGE.color, '#999'],
        'fill-opacity': ['case', ['==', ['get', 'cluster_id'], selId ?? ''], 0.75, 0.42],
      } })
    out.push({ id: 'opp-line', data: filtered, type: 'line',
      paint: {
        'line-color': ['match', ['get', 'action'],
          'PROTECT', '#1F5C4A', 'INVEST', '#2A5A7E', 'ADAPT', '#A8741B', 'MANAGE', '#6E343B', '#666'],
        'line-width': ['case', ['==', ['get', 'cluster_id'], selId ?? ''], 3, 1.2],
      } })
    return out
  }, [opps, dests, shown, selId])

  if (loading) return <Loading what="the opportunity areas" />
  if (error) return <div className="wrap py-16"><ErrorBox message={error} /></div>

  return (
    <>
      <Hero eyebrow="Results" title={`${areas.length} investment opportunity areas across Panama`}
        lead="Contiguous clusters of strongly-scoring cells, named from the geography they sit in, ranked by strength and scale. Each carries an investment narrative built from its own measured evidence — and a statement of how it relates to the government's declared priorities." />

      <div className="wrap py-8">
        <div className="flex flex-wrap items-center gap-x-6 gap-y-3 mb-4">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] uppercase tracking-wider text-wb-muted mr-1">Type</span>
            {['ALL', ...Object.keys(ACTIONS)].map(k => (
              <button key={k} onClick={() => setFAction(k)}
                className={`px-2.5 py-1 rounded text-[11.5px] font-semibold border transition-colors
                  ${fAction === k ? 'text-white border-transparent' : 'bg-white text-wb-slate border-wb-line hover:border-wb-blue'}`}
                style={fAction === k ? { backgroundColor: k === 'ALL' ? '#4D5C69' : ACTIONS[k].color } : {}}>
                {k === 'ALL' ? 'All' : ACTIONS[k].label}
              </button>
            ))}
          </div>
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] uppercase tracking-wider text-wb-muted mr-1">Vs. plan</span>
            {['ALL', 'reinforces', 'refines', 'partial', 'new'].map(k => (
              <button key={k} onClick={() => setFGov(k)}
                className={`px-2.5 py-1 rounded text-[11.5px] font-semibold border capitalize transition-colors
                  ${fGov === k ? 'bg-wb-slateDk text-white border-wb-slateDk'
                               : 'bg-white text-wb-slate border-wb-line hover:border-wb-blue'}`}>
                {k === 'ALL' ? 'All' : k}
              </button>
            ))}
          </div>
          <span className="text-[12px] text-wb-muted">{shown.length} shown</span>
        </div>

        <div className="card overflow-hidden mb-6">
          <MapCanvas className="h-[480px]" layers={layers} basemap={basemap}
            onBasemapChange={setBasemap} cursorLayers={['opp-fill']}
            onFeatureClick={p => p && setSelId(p.cluster_id)}>
            <div className="absolute bottom-6 left-3 z-10 bg-white/95 backdrop-blur rounded-md
                            border border-wb-line shadow px-3.5 py-3">
              <div className="space-y-1.5">
                {Object.values(ACTIONS).map(a => (
                  <div key={a.key} className="flex items-center gap-2 text-[11.5px] text-wb-slate">
                    <span className="w-3.5 h-3.5 rounded-sm" style={{ backgroundColor: a.color }} />{a.label}
                  </div>
                ))}
                <div className="flex items-center gap-2 text-[11.5px] text-wb-muted pt-1 border-t border-wb-line mt-1">
                  <span className="w-3.5 border-t border-dashed border-wb-muted" />Government destinations
                </div>
              </div>
            </div>
          </MapCanvas>
        </div>

        {selected && (
          <div className="mb-8">
            <Detail area={selected} narr={selNarr} onClose={() => setSelId(null)} />
          </div>
        )}

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {shown.map(a => (
            <button key={a.cluster_id} onClick={() => setSelId(a.cluster_id)}
              className={`card p-5 text-left hover:shadow-md transition-all
                ${selId === a.cluster_id ? 'ring-2 ring-wb-blue' : 'hover:border-wb-blue'}`}
              style={{ borderTop: `3px solid ${ACTIONS[a.action]?.color}` }}>
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="text-[11px] font-bold text-wb-muted">#{a.rank}</span>
                <span className="chip text-white text-[10px]" style={{ backgroundColor: ACTIONS[a.action]?.color }}>
                  {ACTIONS[a.action]?.label}
                </span>
              </div>
              <div className="font-bold text-[15px] text-wb-slateDk leading-snug">{a.name}</div>
              <div className="text-[11.5px] text-wb-muted mt-1">
                {a.districts?.split('; ')[0]} · {Math.round(a.area_km2).toLocaleString()} km²
              </div>
              <div className="mt-3 flex flex-wrap gap-1">
                {FAMILIES.slice(0, 6).map(f => (
                  <span key={f.key} className="text-[10px] px-1.5 py-0.5 rounded bg-wb-wash text-wb-slate tabular-nums"
                    title={f.label}>{f.key} {Math.round(a[f.key])}</span>
                ))}
              </div>
              <div className="mt-3 pt-2.5 border-t border-wb-line">
                <span className="text-[11px] font-semibold"
                  style={{ color: GOV_RELATION[a.gov_relation]?.color }}>
                  {GOV_RELATION[a.gov_relation]?.label}
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </>
  )
}
