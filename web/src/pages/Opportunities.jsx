import { useEffect, useMemo, useState } from 'react'
import MapCanvas from '../components/MapCanvas'
import RichText from '../components/RichText'
import { Hero, Callout, Loading, ErrorBox, ScoreBar, ActionChip } from '../components/ui'
import { ACTIONS, FAMILIES } from '../lib/constants'
import { useData } from '../lib/useData'

const TOURISM_BLUE = '#2A5A7E'
const NATURE_GREEN = '#2E7D5B'

function Bullets({ items, colour }) {
  if (!items?.length) return null
  return (
    <ul className="space-y-2.5">
      {items.map((t, i) => (
        <li key={i} className="flex gap-2.5 prose-wb text-[13.5px]">
          <span className="mt-[7px] shrink-0 w-1.5 h-1.5 rounded-full"
            style={{ backgroundColor: colour }} />
          <RichText text={t} />
        </li>
      ))}
    </ul>
  )
}

function JobsPanel({ est, narrative, caveat }) {
  if (!est) return null
  const rows = [
    ['Accommodation', est.accommodation],
    ['Food, retail & transport', est.services],
    ['Guiding & activities', est.guiding],
    ['Ecosystem restoration', est.restoration_fte],
    ['Protected-area management', est.management],
  ].filter(([, v]) => v && (v[0] || v[1]))

  return (
    <div className="card overflow-hidden">
      <div className="px-5 py-4 border-b border-wb-line bg-wb-wash">
        <div className="eyebrow">Indicative employment</div>
        <div className="mt-2 flex flex-wrap items-baseline gap-x-6 gap-y-2">
          <div>
            <div className="text-[26px] font-bold text-wb-slateDk leading-none">
              {est.direct_total[0]}–{est.direct_total[1]}
            </div>
            <div className="text-[11px] uppercase tracking-wider text-wb-muted mt-1">Direct jobs</div>
          </div>
          <div>
            <div className="text-[26px] font-bold text-wb-green leading-none">
              {est.with_indirect[0]}–{est.with_indirect[1]}
            </div>
            <div className="text-[11px] uppercase tracking-wider text-wb-muted mt-1">
              Including indirect &amp; induced
            </div>
          </div>
        </div>
      </div>
      <div className="p-5 space-y-4">
        <p className="prose-wb text-[13.5px]"><RichText text={narrative} /></p>
        {rows.length > 0 && (
          <table className="tbl">
            <thead><tr><th>Channel</th><th className="text-right pr-0">Jobs</th></tr></thead>
            <tbody>
              {rows.map(([k, v]) => (
                <tr key={k}>
                  <td className="text-wb-slate">{k}</td>
                  <td className="text-right pr-0 font-semibold text-wb-slateDk tabular-nums">
                    {v[0]}–{v[1]}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <p className="text-[11.5px] leading-relaxed text-wb-muted border-t border-wb-line pt-3">
          {caveat}
        </p>
      </div>
    </div>
  )
}

function Detail({ area, narr, nodes, zones, onClose }) {
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
              <span className="chip border"
                style={{ borderColor: area.in_gov_plan ? '#7FA23A' : '#8EA0AF',
                         color: area.in_gov_plan ? '#5C7A22' : '#67788A' }}>
                {area.in_gov_plan ? 'In a government priority destination' : 'Outside the government plan'}
              </span>
              {area.is_comarca === 1 && (
                <span className="chip bg-wb-yellow/20 text-[#8a6d00] border border-wb-yellow">Indigenous comarca</span>
              )}
            </div>
            <h3 className="text-[22px] font-bold text-wb-slateDk leading-tight">{area.name}</h3>
            <div className="text-[12.5px] text-wb-muted mt-1">
              {area.districts} · {Math.round(area.area_km2).toLocaleString()} km²
            </div>
          </div>
          <button onClick={onClose} className="text-wb-muted hover:text-wb-slateDk text-xl leading-none shrink-0">×</button>
        </div>
        {n.headline && <p className="mt-4 text-[15px] leading-relaxed text-wb-slateDk font-medium">{n.headline}</p>}
      </div>

      {/* ---- the two answers, side by side ---- */}
      <div className="grid lg:grid-cols-2 border-b border-wb-line">
        <div className="p-6 border-b lg:border-b-0 lg:border-r border-wb-line">
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: TOURISM_BLUE }} />
            <h4 className="text-[15px] font-bold" style={{ color: TOURISM_BLUE }}>
              Where to invest in tourism infrastructure
            </h4>
          </div>
          <p className="text-[11.5px] text-wb-muted mb-4">
            {nodes.length
              ? `${nodes.length} site${nodes.length === 1 ? '' : 's'} with road access and a settlement within reach`
              : 'No site here passes the access test'}
          </p>
          <Bullets items={n.tourism_investment} colour={TOURISM_BLUE} />
        </div>
        <div className="p-6 bg-wb-green/[0.035]">
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: NATURE_GREEN }} />
            <h4 className="text-[15px] font-bold" style={{ color: NATURE_GREEN }}>
              Where to invest in nature
            </h4>
          </div>
          <p className="text-[11.5px] text-wb-muted mb-4">
            {zones.length
              ? `${zones.length} ecosystem zone${zones.length === 1 ? '' : 's'} to protect or restore`
              : 'No ecosystem action zone identified'}
          </p>
          <Bullets items={n.nature_investment} colour={NATURE_GREEN} />
        </div>
      </div>

      <div className="p-6 grid gap-7 lg:grid-cols-[1fr_290px]">
        <div className="space-y-7 order-2 lg:order-1">
          <JobsPanel est={n.jobs_estimate} narrative={n.jobs} caveat={n.jobs_caveat} />

          <div>
            <div className="eyebrow mb-2">Why here</div>
            <Bullets items={n.why_here} colour="#8EA0AF" />
          </div>
          {n.natural_assets && (
            <div>
              <div className="eyebrow mb-2">Natural assets</div>
              <p className="prose-wb text-[13.5px]">{n.natural_assets}</p>
            </div>
          )}
          {n.biodiversity && (
            <div>
              <div className="eyebrow mb-2">Biodiversity and protection</div>
              <p className="prose-wb text-[13.5px]">{n.biodiversity}</p>
            </div>
          )}
          {n.resilience && (
            <div>
              <div className="eyebrow mb-2">Resilience contribution</div>
              <p className="prose-wb text-[13.5px]">{n.resilience}</p>
            </div>
          )}
          <div className="grid gap-6 sm:grid-cols-2">
            <div>
              <div className="eyebrow mb-2">Risks and trade-offs</div>
              <Bullets items={n.risks} colour="#9B4B54" />
            </div>
            <div>
              <div className="eyebrow mb-2">Further analysis needed</div>
              <Bullets items={n.further_analysis} colour="#8EA0AF" />
            </div>
          </div>
          <Callout title="Relationship to the government plan"
            tone={area.in_gov_plan ? 'green' : 'blue'}>
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
                ['Mangrove', `${(area.mangrove_frac * area.area_km2 * 100).toFixed(0)} ha`],
                ['Shallow shelf', `${(100 * area.shallow_frac).toFixed(0)}%`],
                ['Local relief', `${Math.round(area.relief_m)} m`],
                ['Species / cell', Math.round(area.gbif_species)],
                ['To gateway', `${Number(area.tt_gateway_h).toFixed(1)} h`],
                ['Population', Math.round(area.population).toLocaleString()],
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
  const { data: nodeFC } = useData('tourism_nodes.geojson')
  const { data: zoneFC } = useData('nature_zones.geojson')
  const [basemap, setBasemap] = useState('light')
  const [selId, setSelId] = useState(param || null)
  const [fAction, setFAction] = useState('ALL')
  const [showGov, setShowGov] = useState(false)
  const [showNodes, setShowNodes] = useState(true)

  useEffect(() => { if (param) setSelId(param) }, [param])

  const areas = useMemo(() =>
    opps ? opps.features.map(f => f.properties).sort((a, b) => a.rank - b.rank) : [], [opps])
  const shown = useMemo(() =>
    areas.filter(a => fAction === 'ALL' || a.action === fAction), [areas, fAction])

  const selected = areas.find(a => a.cluster_id === selId) || null
  const selNarr = narr?.areas?.find(n => n.cluster_id === selId) || null
  const selNodes = useMemo(() =>
    nodeFC?.features?.filter(f => f.properties.area_id === selId) ?? [], [nodeFC, selId])
  const selZones = useMemo(() =>
    zoneFC?.features?.filter(f => f.properties.area_id === selId) ?? [], [zoneFC, selId])

  const layers = useMemo(() => {
    if (!opps) return []
    const ids = new Set(shown.map(a => a.cluster_id))
    const filtered = { type: 'FeatureCollection',
      features: opps.features.filter(f => ids.has(f.properties.cluster_id)) }
    const out = []

    if (dests && showGov) {
      out.push({ id: 'gov-fill', data: dests, type: 'fill',
        paint: { 'fill-color': '#F5D108', 'fill-opacity': 0.14 } })
      out.push({ id: 'gov-line', data: dests, type: 'line', sourceOf: 'gov-fill',
        paint: { 'line-color': '#C9A800', 'line-width': 1.8 } })
    }

    out.push({ id: 'opp-fill', data: filtered, type: 'fill',
      paint: {
        'fill-color': ['match', ['get', 'action'],
          'PROTECT', ACTIONS.PROTECT.color, 'INVEST', ACTIONS.INVEST.color,
          'ADAPT', ACTIONS.ADAPT.color, 'MANAGE', ACTIONS.MANAGE.color, '#999'],
        'fill-opacity': ['case', ['==', ['get', 'cluster_id'], selId ?? ''], 0.72, 0.40],
      } })
    out.push({ id: 'opp-line', data: filtered, type: 'line', sourceOf: 'opp-fill',
      paint: {
        'line-color': ['match', ['get', 'action'],
          'PROTECT', '#1F5C4A', 'INVEST', '#2A5A7E', 'ADAPT', '#A8741B', 'MANAGE', '#6E343B', '#666'],
        'line-width': ['case', ['==', ['get', 'cluster_id'], selId ?? ''], 3, 1.1],
      } })

    // nature zones for the selected area
    if (zoneFC && selId) {
      const z = { type: 'FeatureCollection',
        features: zoneFC.features.filter(f => f.properties.area_id === selId) }
      if (z.features.length) {
        out.push({ id: 'nz-fill', data: z, type: 'fill',
          paint: {
            'fill-color': ['match', ['get', 'action'], 'protect', NATURE_GREEN, '#8FBF6A'],
            'fill-opacity': 0.5,
          } })
        out.push({ id: 'nz-line', data: z, type: 'line', sourceOf: 'nz-fill',
          paint: { 'line-color': '#14513C', 'line-width': 1.2, 'line-dasharray': [2, 1.5] } })
      }
    }

    if (nodeFC && showNodes) {
      const nd = selId
        ? { type: 'FeatureCollection', features: nodeFC.features.filter(f => f.properties.area_id === selId) }
        : nodeFC
      out.push({ id: 'nodes', data: nd, type: 'circle',
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['zoom'], 6, 3.4, 10, 6.5, 14, 10],
          'circle-color': TOURISM_BLUE,
          'circle-stroke-width': 1.6, 'circle-stroke-color': '#fff',
        } })
    }
    return out
  }, [opps, dests, zoneFC, nodeFC, shown, selId, showGov, showNodes])

  if (loading) return <Loading what="the opportunity areas" />
  if (error) return <div className="wrap py-16"><ErrorBox message={error} /></div>

  return (
    <>
      <Hero eyebrow="Results" title={`${areas.length} investment opportunity areas across Panama`}
        lead="Each area reports two things separately: sites where visitor infrastructure could be developed, and zones where ecosystems should be protected or restored to support that tourism. Select an area to see its sites and zones on the map." />

      <div className="wrap py-8">
        <div className="flex flex-wrap items-center gap-x-6 gap-y-3 mb-4">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] uppercase tracking-wider text-wb-muted mr-1">Type</span>
            {['ALL', 'INVEST', 'PROTECT', 'ADAPT', 'MANAGE'].map(k => (
              <button key={k} onClick={() => setFAction(k)}
                className={`px-2.5 py-1 rounded text-[11.5px] font-semibold border transition-colors
                  ${fAction === k ? 'text-white border-transparent' : 'bg-white text-wb-slate border-wb-line hover:border-wb-blue'}`}
                style={fAction === k ? { backgroundColor: k === 'ALL' ? '#4D5C69' : ACTIONS[k].color } : {}}>
                {k === 'ALL' ? 'All' : ACTIONS[k].label}
              </button>
            ))}
          </div>
          <label className="inline-flex items-center gap-2 text-[12.5px] text-wb-slate cursor-pointer">
            <input type="checkbox" checked={showGov} onChange={e => setShowGov(e.target.checked)}
              className="accent-wb-green" /> Overlay government priority destinations
          </label>
          <label className="inline-flex items-center gap-2 text-[12.5px] text-wb-slate cursor-pointer">
            <input type="checkbox" checked={showNodes} onChange={e => setShowNodes(e.target.checked)}
              className="accent-wb-green" /> Show tourism investment sites
          </label>
          <span className="text-[12px] text-wb-muted">{shown.length} areas shown</span>
        </div>

        <div className="card overflow-hidden mb-6">
          <MapCanvas className="h-[500px]" layers={layers} basemap={basemap}
            onBasemapChange={setBasemap} cursorLayers={['opp-fill', 'nodes']}
            onFeatureClick={p => p && setSelId(p.area_id ?? p.cluster_id ?? null)}>
            <div className="absolute bottom-6 left-3 z-10 bg-white/95 backdrop-blur rounded-md
                            border border-wb-line shadow px-3.5 py-3">
              <div className="space-y-1.5">
                {Object.values(ACTIONS).filter(a => a.key !== 'NONE').map(a => (
                  <div key={a.key} className="flex items-center gap-2 text-[11.5px] text-wb-slate">
                    <span className="w-3.5 h-3.5 rounded-sm" style={{ backgroundColor: a.color }} />{a.label}
                  </div>
                ))}
                <div className="pt-1.5 mt-1.5 border-t border-wb-line space-y-1.5">
                  <div className="flex items-center gap-2 text-[11.5px] text-wb-slate">
                    <span className="w-3 h-3 rounded-full border-2 border-white shadow"
                      style={{ backgroundColor: TOURISM_BLUE }} />Tourism investment site
                  </div>
                  <div className="flex items-center gap-2 text-[11.5px] text-wb-slate">
                    <span className="w-3.5 h-3.5 rounded-sm" style={{ backgroundColor: NATURE_GREEN, opacity: .6 }} />
                    Nature action zone
                  </div>
                  {showGov && (
                    <div className="flex items-center gap-2 text-[11.5px] text-wb-slate">
                      <span className="w-3.5 h-3.5 rounded-sm" style={{ backgroundColor: '#F5D108', opacity: .5 }} />
                      Government destination
                    </div>
                  )}
                </div>
              </div>
            </div>
          </MapCanvas>
        </div>

        {selected && (
          <div className="mb-8">
            <Detail area={selected} narr={selNarr} nodes={selNodes} zones={selZones}
              onClose={() => setSelId(null)} />
          </div>
        )}

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {shown.map(a => {
            const nn = nodeFC?.features?.filter(f => f.properties.area_id === a.cluster_id).length ?? 0
            const nz = zoneFC?.features?.filter(f => f.properties.area_id === a.cluster_id).length ?? 0
            return (
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
                <div className="mt-3 flex flex-wrap gap-1.5 text-[10.5px]">
                  <span className="px-1.5 py-0.5 rounded font-semibold text-white"
                    style={{ backgroundColor: TOURISM_BLUE }}>{nn} tourism site{nn === 1 ? '' : 's'}</span>
                  <span className="px-1.5 py-0.5 rounded font-semibold text-white"
                    style={{ backgroundColor: NATURE_GREEN }}>{nz} nature zone{nz === 1 ? '' : 's'}</span>
                </div>
                <div className="mt-3 pt-2.5 border-t border-wb-line text-[11px] font-semibold"
                  style={{ color: a.in_gov_plan ? '#5C7A22' : '#8EA0AF' }}>
                  {a.in_gov_plan ? 'In a government priority destination' : 'Outside the government plan'}
                </div>
              </button>
            )
          })}
        </div>
      </div>
    </>
  )
}
