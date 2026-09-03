import { useMemo, useState } from 'react'
import MapCanvas from '../components/MapCanvas'
import { Hero, Loading, ErrorBox } from '../components/ui'
import { ECO_CLASSES, TOURISM_CLASSES, matchExpr } from '../lib/palettes'
import { useData } from '../lib/useData'

const POI_STYLE = {
  accommodation: { c: '#3E7CAB', label: 'Accommodation' },
  food_service:  { c: '#8EA0AF', label: 'Food service' },
  attraction:    { c: '#9B4B54', label: 'Attractions & heritage' },
  beach:         { c: '#E0B417', label: 'Beaches' },
  waterfall:     { c: '#4FB3C9', label: 'Waterfalls' },
  peak:          { c: '#7A6A55', label: 'Peaks & volcanoes' },
  viewpoint:     { c: '#D99A2B', label: 'Viewpoints' },
  dive_surf:     { c: '#0F766E', label: 'Dive & surf' },
  marina_port:   { c: '#2E3944', label: 'Marinas & ferries' },
  airport:       { c: '#5C7A22', label: 'Airports & airstrips' },
  visitor_infra: { c: '#7FA23A', label: 'Visitor information' },
  reef_natural:  { c: '#2E7D5B', label: 'Mapped reefs' },
  hotspring:     { c: '#C2703D', label: 'Hot springs' },
}

const NATURE_POIS = ['beach', 'waterfall', 'peak', 'reef_natural', 'hotspring', 'viewpoint']
const SUPPLY_POIS = ['accommodation', 'food_service', 'attraction', 'visitor_infra',
                     'dive_surf', 'marina_port', 'airport']

const VIEWS = {
  ecosystems: {
    label: 'Ecosystems',
    blurb: 'Every screening cell labelled by the ecosystem that defines it, from ESA WorldCover 10 m land cover and national bathymetry. Rarer, more policy-relevant systems — mangrove, wetland, shallow reef habitat — take precedence over the general land-cover majority, so they stay visible.',
    field: 'eco_class', classes: ECO_CLASSES, defaultPois: NATURE_POIS,
  },
  tourism: {
    label: 'Tourism assets',
    blurb: 'Existing tourism supply from OpenStreetMap, smoothed over each cell and its immediate neighbours because a destination does not stop at a hexagon boundary. Only about one cell in eight carries any mapped supply at all — the concentration is the finding.',
    field: 'tourism_class', classes: TOURISM_CLASSES, defaultPois: SUPPLY_POIS,
  },
  protection: {
    label: 'Protection',
    blurb: "Panama's own protected-area register (SINAP, 2025 edition, 91 areas) with IUCN category and marine/terrestrial realm. A third of the national territory is protected, and most headline visitor experiences happen inside it.",
    field: null, classes: [], defaultPois: [],
  },
}

export default function Explorer() {
  const { data: grid, loading, error } = useData('grid.geojson')
  const { data: pas } = useData('protected_areas.geojson')
  const { data: pois } = useData('osm_pois.geojson')
  const { data: dests } = useData('gov_destinations.geojson')
  const [view, setView] = useState('ecosystems')
  const [basemap, setBasemap] = useState('light')
  const [showPA, setShowPA] = useState(false)
  const [showGov, setShowGov] = useState(false)
  const [themes, setThemes] = useState(new Set(NATURE_POIS))
  const [info, setInfo] = useState(null)

  const V = VIEWS[view]

  function pick(next) {
    setView(next)
    setThemes(new Set(VIEWS[next].defaultPois))
    setShowPA(next === 'protection')
    setInfo(null)
  }

  const togglePoi = (k) => setThemes(s => {
    const n = new Set(s); n.has(k) ? n.delete(k) : n.add(k); return n
  })

  const poiData = useMemo(() => {
    if (!pois) return null
    return { type: 'FeatureCollection',
      features: pois.features.filter(f => themes.has(f.properties.theme)) }
  }, [pois, themes])

  const layers = useMemo(() => {
    const out = []
    if (grid && V.field) {
      out.push({ id: 'grid-cat', data: grid, type: 'fill',
        paint: {
          'fill-color': matchExpr(V.field, V.classes, '#E4E9ED'),
          'fill-opacity': view === 'tourism' ? 0.88 : 0.8,
        } })
      out.push({ id: 'grid-edge', data: grid, type: 'line',
        paint: { 'line-color': '#FFFFFF', 'line-width': 0.3, 'line-opacity': 0.45 } })
    }
    if (pas && (showPA || view === 'protection')) {
      out.push({ id: 'pa-fill', data: pas, type: 'fill',
        paint: {
          'fill-color': ['match', ['get', 'realm'],
            '100% Marine', '#3FA9C4', 'Marine', '#3FA9C4',
            'Land and Marine', '#3E9B7E', '#5C8A2E'],
          'fill-opacity': view === 'protection' ? 0.45 : 0.22 } })
      out.push({ id: 'pa-line', data: pas, type: 'line',
        paint: { 'line-color': '#1F5C4A', 'line-width': view === 'protection' ? 1.1 : 0.7 } })
    }
    if (dests && showGov) {
      out.push({ id: 'gov-line', data: dests, type: 'line',
        paint: { 'line-color': '#F5D108', 'line-width': 2.2 } })
    }
    if (poiData?.features?.length) {
      out.push({ id: 'poi', data: poiData, type: 'circle',
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['zoom'], 6, 2.2, 10, 4.5, 14, 7.5],
          'circle-color': ['match', ['get', 'theme'],
            ...Object.entries(POI_STYLE).flatMap(([k, v]) => [k, v.c]), '#666'],
          'circle-stroke-width': 0.8, 'circle-stroke-color': '#fff', 'circle-opacity': 0.92 } })
    }
    return out
  }, [grid, pas, dests, poiData, V, view, showPA, showGov])

  if (loading) return <Loading what="the source data layers" />
  if (error) return <div className="wrap py-16"><ErrorBox message={error} /></div>

  return (
    <>
      <Hero eyebrow="Inputs" title="Data explorer"
        lead="The evidence base, mapped as it actually is. Protection from Panama's own SINAP register, tourism assets from OpenStreetMap, ecosystems from ESA WorldCover and national bathymetry, terrain from Copernicus. Nothing on this page is modelled." />

      <div className="wrap py-8">
        <div className="flex flex-wrap gap-2 mb-4">
          {Object.entries(VIEWS).map(([k, v]) => (
            <button key={k} onClick={() => pick(k)}
              className={`px-4 py-2 rounded text-[13px] font-bold transition-colors border
                ${view === k ? 'bg-wb-slateDk text-white border-wb-slateDk'
                             : 'bg-white text-wb-slate border-wb-line hover:border-wb-blue'}`}>
              {v.label}
            </button>
          ))}
        </div>
        <p className="prose-wb text-[14px] max-w-3xl mb-5">{V.blurb}</p>

        <div className="grid gap-5 lg:grid-cols-[250px_1fr]">
          <aside className="space-y-4">
            {V.classes.length > 0 && (
              <div className="card p-4">
                <div className="eyebrow mb-2.5">{V.label}</div>
                <div className="space-y-1.5">
                  {V.classes.map(([label, colour]) => (
                    <div key={label} className="flex items-center gap-2 text-[12px] text-wb-slate">
                      <span className="w-3.5 h-3.5 rounded-sm shrink-0 border border-black/5"
                        style={{ backgroundColor: colour }} />
                      {label}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {view === 'protection' && (
              <div className="card p-4">
                <div className="eyebrow mb-2.5">Realm</div>
                <div className="space-y-1.5 text-[12px] text-wb-slate">
                  {[['#5C8A2E', 'Terrestrial'], ['#3E9B7E', 'Land & marine'], ['#3FA9C4', 'Marine']].map(([c, l]) => (
                    <div key={l} className="flex items-center gap-2">
                      <span className="w-3.5 h-3.5 rounded-sm" style={{ backgroundColor: c, opacity: .7 }} />{l}
                    </div>
                  ))}
                </div>
                <p className="mt-3 text-[10.5px] leading-snug text-wb-muted border-t border-wb-line pt-2.5">
                  Click any protected area for its category, IUCN class, size and year of
                  establishment.
                </p>
              </div>
            )}

            <div className="card p-4">
              <div className="eyebrow mb-2.5">Overlays</div>
              {view !== 'protection' && (
                <label className="flex items-center gap-2 text-[12.5px] text-wb-slate cursor-pointer mb-2">
                  <input type="checkbox" checked={showPA} onChange={e => setShowPA(e.target.checked)}
                    className="accent-wb-green" /> Protected areas
                </label>
              )}
              <label className="flex items-center gap-2 text-[12.5px] text-wb-slate cursor-pointer">
                <input type="checkbox" checked={showGov} onChange={e => setShowGov(e.target.checked)}
                  className="accent-wb-green" /> Government destinations
              </label>
            </div>

            <div className="card p-4">
              <div className="eyebrow mb-2.5">Mapped features (OSM)</div>
              <div className="space-y-1.5 max-h-[260px] overflow-y-auto pr-1">
                {Object.entries(POI_STYLE).map(([k, v]) => (
                  <label key={k} className="flex items-center gap-2 text-[12px] text-wb-slate cursor-pointer">
                    <input type="checkbox" checked={themes.has(k)} onChange={() => togglePoi(k)}
                      className="accent-wb-green" />
                    <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: v.c }} />
                    {v.label}
                  </label>
                ))}
              </div>
              <p className="mt-3 text-[10.5px] leading-snug text-wb-muted border-t border-wb-line pt-2.5">
                OpenStreetMap coverage is uneven and biased toward places that already receive
                visitors. Absence of a point is not evidence of absence on the ground.
              </p>
            </div>
          </aside>

          <div className="card overflow-hidden relative">
            <MapCanvas className="h-[680px]" layers={layers} basemap={basemap}
              onBasemapChange={setBasemap} cursorLayers={['poi', 'pa-fill', 'grid-cat']}
              onFeatureClick={p => setInfo(p)}>
              {info && (
                <div className="absolute bottom-3 left-3 z-10 max-w-[320px] bg-white rounded-md
                                border border-wb-line shadow-lg p-4">
                  <button onClick={() => setInfo(null)}
                    className="float-right text-wb-muted hover:text-wb-slateDk leading-none text-lg">×</button>
                  <div className="font-bold text-[13.5px] text-wb-slateDk pr-5">
                    {info.name || info.eco_class || info.kind || 'Feature'}
                  </div>
                  {info.category && (
                    <div className="text-[12px] text-wb-slate mt-1.5">
                      {info.category}{info.iucn && !String(info.iucn).startsWith('N') ? ` · IUCN ${info.iucn}` : ''}
                      {info.realm ? ` · ${info.realm}` : ''}
                    </div>
                  )}
                  {info.hectares != null && (
                    <div className="text-[12px] text-wb-muted mt-1">
                      {Math.round(info.hectares).toLocaleString()} ha
                      {info.established ? ` · established ${info.established}` : ''}
                    </div>
                  )}
                  {info.theme && (
                    <div className="text-[12px] text-wb-muted mt-1">
                      {POI_STYLE[info.theme]?.label || info.theme}{info.kind ? ` · ${info.kind}` : ''}
                    </div>
                  )}
                  {info.h3 && (
                    <div className="mt-2 pt-2 border-t border-wb-line text-[12px] space-y-1">
                      <div className="text-wb-slate">{info.district}, {info.province}</div>
                      <div className="text-wb-muted">
                        Forest {Math.round(100 * (info.lc_tree ?? 0))}% ·
                        Mangrove {(100 * (info.lc_mangrove ?? 0)).toFixed(1)}% ·
                        Shelf {Math.round(100 * (info.shallow_frac ?? 0))}%
                      </div>
                      <div className="text-wb-muted">
                        {info.tourism_class} · {Math.round(info.n_accommodation ?? 0)} accommodation
                      </div>
                    </div>
                  )}
                </div>
              )}
            </MapCanvas>
          </div>
        </div>
      </div>
    </>
  )
}
