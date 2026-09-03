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

// Numeric views use a ramp keyed on a single field; categorical views use a class list.
const RAMPS = {
  flood:      ['#F3F6F8', '#BBD4E4', '#7FAECE', '#4A83AF', '#255C86', '#0E3D5E'],
  floodpop:   ['#F7F4F2', '#E5CDBE', '#D3A183', '#BB7350', '#96482A', '#6B2B12'],
  richness:   ['#F6F3EE', '#DCD6BE', '#B9C48D', '#88A860', '#57853C', '#2E5C22'],
  threatened: ['#FAF3F4', '#EBCBCF', '#D89CA4', '#BE6C79', '#9B4453', '#6E2331'],
  buffer:     ['#F1F7F5', '#C3E1D5', '#8FC7B1', '#5AA88C', '#328468', '#175E47'],
}

const VIEWS = {
  ecosystems: {
    label: 'Ecosystems',
    blurb: 'Each screening cell labelled by its defining ecosystem, from ESA WorldCover 10 m land cover and national bathymetry. Rarer systems — mangrove, wetland, shallow reef habitat — take precedence over the land-cover majority so they remain visible.',
    field: 'eco_class', classes: ECO_CLASSES, defaultPois: NATURE_POIS,
  },
  tourism: {
    label: 'Tourism assets',
    blurb: 'Existing tourism supply from OpenStreetMap, smoothed across each cell and its immediate neighbours since destinations do not stop at cell boundaries. Roughly one cell in eight carries any mapped supply.',
    field: 'tourism_class', classes: TOURISM_CLASSES, defaultPois: SUPPLY_POIS,
  },
  flood: {
    label: 'Flood hazard',
    blurb: 'Modelled 1-in-100-year flood extent from WRI Aqueduct Floods (~1 km), and the population standing in it. Riverine flooding dominates in Panama: about 724,000 people fall inside the modelled river flood zone against roughly 12,000 on the coast. Population is intersected with the hazard at the hazard\u2019s own resolution rather than scaled from cell totals.',
    field: null, classes: [], defaultPois: [],
    numeric: [
      { key: 'flood_frac_rp100', label: 'Flood extent, 1-in-100 yr (share of cell)', ramp: RAMPS.flood, max: 1 },
      { key: 'riv_rp100_frac', label: 'River flood extent, 1-in-100 yr', ramp: RAMPS.flood, max: 1 },
      { key: 'cst_rp100_frac', label: 'Coastal flood extent, 1-in-100 yr', ramp: RAMPS.flood, max: 1 },
      { key: 'flood_pop_rp100', label: 'People in the 1-in-100 yr flood zone', ramp: RAMPS.floodpop, max: 20000 },
      { key: 'att_total', label: 'Wave energy removed by mangrove & reef', ramp: RAMPS.buffer, max: 1 },
      { key: 'mangrove_ha', label: 'Mangrove (hectares per cell)', ramp: RAMPS.buffer, max: 800 },
    ],
  },
  biodiversity: {
    label: 'Biodiversity',
    blurb: 'Species recorded in GBIF, aggregated to the screening grid. Threatened richness counts distinct species assessed by the IUCN Red List as Critically Endangered, Endangered or Vulnerable. These measure where people have recorded wildlife, not where wildlife is \u2014 recording effort concentrates at research stations, roadsides and established birding sites.',
    field: null, classes: [], defaultPois: [],
    numeric: [
      { key: 'gbif_threatened', label: 'Threatened species (IUCN CR/EN/VU)', ramp: RAMPS.threatened, max: 60 },
      { key: 'gbif_species', label: 'Vertebrate species recorded', ramp: RAMPS.richness, max: 700 },
    ],
  },
  protection: {
    label: 'Protection',
    blurb: "Panama's protected-area register (SINAP, 2025 edition, 91 areas) with IUCN category and marine or terrestrial realm. Around a third of national territory is protected, and most headline visitor experiences occur inside it.",
    field: null, classes: [], defaultPois: [],
  },
}

export default function Explorer() {
  const { data: grid, loading, error } = useData('grid.geojson')
  const { data: pas } = useData('protected_areas.geojson')
  const { data: pois } = useData('osm_pois.geojson')
  const { data: dests } = useData('gov_destinations.geojson')
  const { data: detail } = useData('grid_detail.json')
  const [view, setView] = useState('ecosystems')
  const [numField, setNumField] = useState(null)
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
    setNumField(VIEWS[next].numeric ? VIEWS[next].numeric[0] : null)
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
      out.push({ id: 'grid-edge', data: grid, type: 'line', sourceOf: 'grid-cat',
        paint: { 'line-color': '#FFFFFF', 'line-width': 0.3, 'line-opacity': 0.45 } })
    }
    if (pas && (showPA || view === 'protection')) {
      out.push({ id: 'pa-fill', data: pas, type: 'fill',
        paint: {
          'fill-color': ['match', ['get', 'realm'],
            '100% Marine', '#3FA9C4', 'Marine', '#3FA9C4',
            'Land and Marine', '#3E9B7E', '#5C8A2E'],
          'fill-opacity': view === 'protection' ? 0.45 : 0.22 } })
      out.push({ id: 'pa-line', data: pas, type: 'line', sourceOf: 'pa-fill',
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
  }, [grid, pas, dests, poiData, V, view, showPA, showGov, numField])

  if (loading) return <Loading what="the source data layers" />
  if (error) return <div className="wrap py-16"><ErrorBox message={error} /></div>

  return (
    <>
      <Hero eyebrow="Inputs" title="Data explorer"
        lead="The underlying data. Protection from Panama's SINAP register, tourism assets from OpenStreetMap, ecosystems from ESA WorldCover and national bathymetry, terrain from Copernicus. Nothing on this page is modelled." />

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
            {V.numeric && (
              <div className="card p-4">
                <div className="eyebrow mb-2.5">{V.label}</div>
                <div className="space-y-1.5 mb-3">
                  {V.numeric.map(nf => (
                    <label key={nf.key} className="flex items-start gap-2 text-[12px] text-wb-slate cursor-pointer">
                      <input type="radio" name="numfield" className="accent-wb-green mt-0.5"
                        checked={numField?.key === nf.key} onChange={() => setNumField(nf)} />
                      <span>{nf.label}</span>
                    </label>
                  ))}
                </div>
                {numField && (
                  <>
                    <div className="h-3 rounded" style={{ backgroundImage:
                      `linear-gradient(90deg, ${numField.ramp.join(',')})` }} />
                    <div className="flex justify-between text-[10.5px] text-wb-muted mt-1">
                      <span>0</span>
                      <span>{numField.max >= 1000 ? numField.max.toLocaleString() : numField.max}</span>
                    </div>
                  </>
                )}
              </div>
            )}
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
              onBasemapChange={setBasemap} cursorLayers={['poi', 'pa-fill', 'grid-cat', 'grid-num']}
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
                  {info.h3 && (() => {
                    const d = detail?.[info.h3] || {}
                    return (
                      <div className="mt-2 pt-2 border-t border-wb-line text-[12px] space-y-1">
                        <div className="text-wb-slate">{d.district}, {d.province}</div>
                        <div className="text-wb-muted">
                          Forest {Math.round(100 * (d.lc_tree ?? 0))}% ·
                          Mangrove {(100 * (d.lc_mangrove ?? 0)).toFixed(1)}% ·
                          Shelf {Math.round(100 * (d.shallow_frac ?? 0))}%
                        </div>
                        <div className="text-wb-muted">
                          {info.tourism_class} · {Math.round(d.n_accommodation ?? 0)} accommodation
                        </div>
                        <div className="text-wb-muted">
                          {Math.round(info.gbif_threatened ?? 0)} threatened ·
                          {' '}{Math.round(info.gbif_species ?? 0)} species recorded
                        </div>
                        {(info.flood_pop_rp100 ?? 0) > 0 && (
                          <div className="text-wb-muted">
                            {Math.round(info.flood_pop_rp100).toLocaleString()} people in the
                            1-in-100 yr flood zone
                            {(info.att_total ?? 0) > 0.02
                              ? ` · ${Math.round(100 * info.att_total)}% wave energy removed by mangrove/reef`
                              : ''}
                          </div>
                        )}
                      </div>
                    )
                  })()}
                </div>
              )}
            </MapCanvas>
          </div>
        </div>
      </div>
    </>
  )
}
