import { useMemo, useRef, useState } from 'react'
import { ACTIONS } from '../lib/constants'

/**
 * Lightweight scatter for ~3,400 screening cells.
 *
 * Deliberately NOT one React element per point with its own handlers: 3,417 circles x two
 * charts x two listeners each is ~14,000 event handlers, which blocks the main thread long
 * enough to starve MapLibre's render loop and leave the map on the same page blank. Points
 * are emitted as plain <circle> nodes with no listeners, and hover is resolved by a single
 * mousemove on the SVG doing a nearest-point search.
 */
const MAX_POINTS = 1600

export default function Scatter({ features, x = 'TDL', y = 'NAV', xLabel, yLabel, height = 380 }) {
  const [hover, setHover] = useState(null)
  const svgRef = useRef(null)
  const W = 560, H = height, P = { t: 16, r: 16, b: 44, l: 48 }
  const iw = W - P.l - P.r, ih = H - P.t - P.b

  const pts = useMemo(() => {
    const all = (features || []).filter(f => f && f[x] != null && f[y] != null)
    // Evenly sample rather than draw every cell. At 3,400+ points the cloud is already
    // saturated, and the DOM cost competes with the map on the same page for main-thread
    // time. The shape of the distribution is unchanged.
    const step = Math.max(1, Math.ceil(all.length / MAX_POINTS))
    return all.filter((_, i) => i % step === 0)
    .map(f => ({
      cx: P.l + (Number(f[x]) / 100) * iw,
      cy: P.t + ih - (Number(f[y]) / 100) * ih,
      c: ACTIONS[f.primary || f.action]?.color || '#8EA0AF',
      d: f,
    }))
  }, [features, x, y, iw, ih])

  function onMove(e) {
    const svg = svgRef.current
    if (!svg) return
    const r = svg.getBoundingClientRect()
    const px = ((e.clientX - r.left) / r.width) * W
    const py = ((e.clientY - r.top) / r.height) * H
    let best = null, bestD = 64  // ~8px in viewBox units
    for (const p of pts) {
      const d2 = (p.cx - px) ** 2 + (p.cy - py) ** 2
      if (d2 < bestD) { bestD = d2; best = p }
    }
    setHover(best)
  }

  return (
    <div className="relative">
      <svg ref={svgRef} viewBox={`0 0 ${W} ${H}`} className="w-full h-auto"
        onMouseMove={onMove} onMouseLeave={() => setHover(null)}
        role="img" aria-label={`${yLabel || y} against ${xLabel || x}`}>
        <rect x={P.l} y={P.t} width={iw * 0.45} height={ih * 0.4} fill="#3E7CAB" opacity="0.06" />
        <text x={P.l + 8} y={P.t + 16} fontSize="9.5" fill="#3E7CAB" fontWeight="700"
          letterSpacing="0.08em">HIGH NATURE · LOW SUPPLY</text>

        {[0, 25, 50, 75, 100].map(v => (
          <g key={`g${v}`}>
            <line x1={P.l} x2={P.l + iw} y1={P.t + ih - (v / 100) * ih} y2={P.t + ih - (v / 100) * ih}
              stroke="#E2E8EC" strokeWidth="1" />
            <line y1={P.t} y2={P.t + ih} x1={P.l + (v / 100) * iw} x2={P.l + (v / 100) * iw}
              stroke="#E2E8EC" strokeWidth="1" />
            <text x={P.l - 8} y={P.t + ih - (v / 100) * ih + 3.5} fontSize="9.5" fill="#8EA0AF"
              textAnchor="end">{v}</text>
            <text x={P.l + (v / 100) * iw} y={P.t + ih + 15} fontSize="9.5" fill="#8EA0AF"
              textAnchor="middle">{v}</text>
          </g>
        ))}
        <line x1={P.l} y1={P.t + ih} x2={P.l + iw} y2={P.t} stroke="#8EA0AF"
          strokeWidth="1" strokeDasharray="4 3" opacity="0.55" />

        <g pointerEvents="none">
          {pts.map((p, i) => (
            <circle key={i} cx={p.cx.toFixed(1)} cy={p.cy.toFixed(1)} r="2.4"
              fill={p.c} opacity="0.55" />
          ))}
          {hover && <circle cx={hover.cx} cy={hover.cy} r="5.5" fill={hover.c}
            stroke="#2E3944" strokeWidth="1.2" />}
        </g>

        <text x={P.l + iw / 2} y={H - 6} fontSize="11" fill="#4D5C69" textAnchor="middle"
          fontWeight="600">{xLabel || x}</text>
        <text x={14} y={P.t + ih / 2} fontSize="11" fill="#4D5C69" textAnchor="middle"
          fontWeight="600" transform={`rotate(-90 14 ${P.t + ih / 2})`}>{yLabel || y}</text>
      </svg>
      {hover && (
        <div className="absolute top-2 right-2 bg-white border border-wb-line rounded shadow-lg
                        px-3 py-2 text-[11.5px] pointer-events-none">
          <div className="font-bold text-wb-slateDk">
            {hover.d.name || hover.d.eco_class || 'Screening cell'}
          </div>
          <div className="text-wb-muted capitalize">
            {hover.d.districts?.split('; ')[0] ?? hover.d.zone ?? ''}
            {hover.d.primary ? ` · ${ACTIONS[hover.d.primary]?.label ?? ''}` : ''}
          </div>
          <div className="mt-1 text-wb-slate">
            {yLabel || y} {Number(hover.d[y]).toFixed(0)} · {xLabel || x} {Number(hover.d[x]).toFixed(0)}
          </div>
        </div>
      )}
    </div>
  )
}
