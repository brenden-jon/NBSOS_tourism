import { useCallback, useEffect, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

// Panama, wide enough for Bocas, Guna Yala, Coiba, Las Perlas and Darien.
export const PANAMA_BOUNDS = [[-83.4, 6.9], [-76.9, 9.9]]

const BASEMAPS = {
  light: { label: 'Light', style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json' },
  terrain: { label: 'Terrain', style: 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json' },
  satellite: {
    label: 'Satellite',
    style: {
      version: 8,
      sources: {
        esri: {
          type: 'raster', tileSize: 256, maxzoom: 18,
          tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
          attribution: 'Imagery © Esri, Maxar, Earthstar Geographics',
        },
        labels: {
          type: 'raster', tileSize: 256, maxzoom: 18,
          tiles: ['https://basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}@2x.png'],
          attribution: '© OpenStreetMap contributors © CARTO',
        },
      },
      layers: [
        { id: 'esri', type: 'raster', source: 'esri' },
        { id: 'labels', type: 'raster', source: 'labels' },
      ],
    },
  },
}

const PREFIX = 'tnos-'
const srcId = (id) => `${PREFIX}src-${id}`
const layerId = (id) => `${PREFIX}${id}`

/**
 * Declarative MapLibre wrapper.
 *
 * `layers`: [{ id, data, type, paint, layout, filter, beforeId }] — each entry becomes one
 * GeoJSON source and one layer.
 *
 * Layer state is applied through a single `apply()` reading from a ref rather than from
 * effect closures. Style changes (basemap switches, and MapLibre's own async style load)
 * wipe every user-added source and layer, and `styledata` fires repeatedly while that
 * happens — so the sync must be idempotent and must always see the *current* layer props,
 * not the ones captured when the listener was attached.
 */
export default function MapCanvas({
  layers = [], onFeatureClick, basemap = 'light', onBasemapChange,
  bounds = PANAMA_BOUNDS, className = '', children, cursorLayers = [],
}) {
  const holder = useRef(null)
  const mapRef = useRef(null)
  const appliedRef = useRef(new Map())   // layer id -> last applied {data, paint, filter}
  const retryRef = useRef(null)
  const retriesRef = useRef(0)
  const layersRef = useRef(layers)
  const clickRef = useRef(onFeatureClick)
  const cursorRef = useRef(cursorLayers)
  const [ready, setReady] = useState(false)

  layersRef.current = layers
  clickRef.current = onFeatureClick
  cursorRef.current = cursorLayers

  const apply = useCallback(() => {
    const m = mapRef.current
    if (!m || !m.style) return
    // If the style is mid-load we cannot add layers yet - but we must come back, or a
    // layer set that arrives during that window (async GeoJSON almost always does) is
    // silently dropped and never painted. Re-arm on the next idle instead of returning.
    let styleReady = false
    try { styleReady = m.isStyleLoaded() } catch { styleReady = false }
    if (!styleReady) {
      // A pending 'idle' is not guaranteed to fire again if the map is already quiescent,
      // so poll briefly instead. Bounded so a genuinely broken style cannot spin forever.
      if (retryRef.current === null && retriesRef.current < 40) {
        retriesRef.current += 1
        retryRef.current = setTimeout(() => { retryRef.current = null; apply() }, 250)
      }
      return
    }
    retriesRef.current = 0
    const current = layersRef.current || []
    const wanted = new Set(current.map(l => layerId(l.id)))
    const applied = appliedRef.current

    for (const l of m.getStyle().layers || []) {
      if (l.id.startsWith(PREFIX) && !wanted.has(l.id) && m.getLayer(l.id)) {
        m.removeLayer(l.id)
        applied.delete(l.id)
      }
    }

    for (const cfg of current) {
      if (!cfg?.data) continue
      const sid = srcId(cfg.id)
      const lid = layerId(cfg.id)
      const prev = applied.get(lid)
      const paintKey = JSON.stringify(cfg.paint || {})
      const layoutKey = JSON.stringify(cfg.layout || {})
      const filterKey = JSON.stringify(cfg.filter ?? null)

      const src = m.getSource(sid)
      if (!src) {
        m.addSource(sid, { type: 'geojson', data: cfg.data })
      } else if (!prev || prev.data !== cfg.data) {
        // Only push data when the reference actually changed. Calling setData on every
        // event re-tiles the source, which fires another event, which calls apply again -
        // an idle/setData loop that pegs the renderer and never paints.
        src.setData(cfg.data)
      }

      if (!m.getLayer(lid)) {
        m.addLayer({
          id: lid, type: cfg.type || 'fill', source: sid,
          paint: cfg.paint || {}, layout: cfg.layout || {},
          ...(cfg.filter ? { filter: cfg.filter } : {}),
        }, cfg.beforeId && m.getLayer(cfg.beforeId) ? cfg.beforeId : undefined)
      } else {
        if (!prev || prev.paint !== paintKey) {
          for (const [k, v] of Object.entries(cfg.paint || {})) m.setPaintProperty(lid, k, v)
        }
        if (!prev || prev.layout !== layoutKey) {
          for (const [k, v] of Object.entries(cfg.layout || {})) m.setLayoutProperty(lid, k, v)
        }
        if (!prev || prev.filter !== filterKey) m.setFilter(lid, cfg.filter ?? null)
      }
      applied.set(lid, { data: cfg.data, paint: paintKey, layout: layoutKey, filter: filterKey })
    }
  }, [])

  // ---- create the map once -------------------------------------------------------
  useEffect(() => {
    if (!holder.current) return undefined
    const m = new maplibregl.Map({
      container: holder.current,
      style: BASEMAPS[basemap]?.style ?? BASEMAPS.light.style,
      bounds,
      fitBoundsOptions: { padding: 24 },
      attributionControl: false,
      dragRotate: false,
      pitchWithRotate: false,
    })
    mapRef.current = m
    m.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
    m.addControl(new maplibregl.ScaleControl({ maxWidth: 110, unit: 'metric' }), 'bottom-left')
    m.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right')
    m.touchZoomRotate.disableRotation()

    const onLoad = () => { setReady(true); apply() }
    m.on('load', onLoad)
    m.on('styledata', () => { appliedRef.current.clear(); apply() })
    // 'idle' fires once the style is fully loaded and the map is quiescent. It is the only
    // event that reliably lands AFTER MapLibre has finished swapping in a remote style's
    // layer list - which otherwise silently discards layers added a moment too early, so
    // the grid loads, reports itself present, and never paints.
    m.on('idle', apply)

    const onClick = (e) => {
      const ids = (cursorRef.current || []).map(layerId).filter(i => m.getLayer(i))
      if (!ids.length) return
      const hits = m.queryRenderedFeatures(e.point, { layers: ids })
      clickRef.current?.(hits[0]?.properties ?? null, hits[0], e.lngLat)
    }
    const onMove = (e) => {
      const ids = (cursorRef.current || []).map(layerId).filter(i => m.getLayer(i))
      if (!ids.length) return
      m.getCanvas().style.cursor =
        m.queryRenderedFeatures(e.point, { layers: ids }).length ? 'pointer' : ''
    }
    m.on('click', onClick)
    m.on('mousemove', onMove)

    if (import.meta.env.DEV) window.__map = m

    return () => {
      setReady(false)
      if (retryRef.current) clearTimeout(retryRef.current)
      retryRef.current = null
      mapRef.current = null
      m.remove()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // ---- re-apply whenever the caller's layers change -------------------------------
  useEffect(() => { apply() }, [layers, ready, apply])

  // ---- basemap switching keeps the current view -----------------------------------
  const firstBasemap = useRef(basemap)
  useEffect(() => {
    const m = mapRef.current
    if (!m || !ready || basemap === firstBasemap.current) return
    firstBasemap.current = basemap
    const c = m.getCenter(); const z = m.getZoom()
    appliedRef.current.clear()
    m.setStyle(BASEMAPS[basemap]?.style ?? BASEMAPS.light.style)
    m.once('idle', () => { m.jumpTo({ center: c, zoom: z }); apply() })
  }, [basemap, ready, apply])

  return (
    <div className={`relative ${className}`}>
      <div ref={holder} className="absolute inset-0" />
      {onBasemapChange && (
        <div className="absolute top-3 left-3 z-10 flex rounded overflow-hidden shadow border border-wb-line bg-white">
          {Object.entries(BASEMAPS).map(([k, v]) => (
            <button key={k} onClick={() => onBasemapChange(k)}
              className={`px-2.5 py-1.5 text-[11px] font-bold uppercase tracking-wider transition-colors
                ${basemap === k ? 'bg-wb-slateDk text-white' : 'bg-white text-wb-slate hover:bg-wb-wash'}`}>
              {v.label}
            </button>
          ))}
        </div>
      )}
      {children}
    </div>
  )
}
