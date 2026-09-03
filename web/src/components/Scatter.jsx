import { useMemo, useState } from 'react'
import { ACTIONS } from '../lib/constants'

/**
 * NAV vs TDL scatter — the central diagnostic.
 * Everything low-right is attraction without supply; everything high-left is supply
 * without much natural draw. The diagonal is "development matched to nature".
 */
export default function Scatter({ features, x = 'TDL', y = 'NAV', xLabel, yLabel, height = 380 }) {
  const [hover, setHover] = useState(null)
  const W = 560, H = height, P = { t: 16, r: 16, b: 44, l: 48 }
  const iw = W - P.l - P.r, ih = H - P.t - P.b

  const pts = useMemo(() => (features || [])
    .filter(f => f[x] != null && f[y] != null)
    .map(f => ({
      cx: P.l + (Number(f[x]) / 100) * iw,
      cy: P.t + ih - (Number(f[y]) / 100) * ih,
      a: f.primary || f.action,
      d: f,
    })), [features, x, y, iw, ih])

  return (
    <div className="relative">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img"
        aria-label={`${yLabel || y} against ${xLabel || x}`}>
        {/* quadrant wash: high attraction, low supply */}
        <rect x={P.l} y={P.t} width={iw * 0.45} height={ih * 0.4}
          fill="#3E7CAB" opacity="0.06" />
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

        {pts.map((p, i) => (
          <circle key={i} cx={p.cx} cy={p.cy} r={hover === i ? 5 : 2.6}
            fill={ACTIONS[p.a]?.color || '#8EA0AF'}
            opacity={hover === null || hover === i ? 0.75 : 0.28}
            onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}
            style={{ cursor: 'pointer' }} />
        ))}

        <text x={P.l + iw / 2} y={H - 6} fontSize="11" fill="#4D5C69" textAnchor="middle"
          fontWeight="600">{xLabel || x}</text>
        <text x={14} y={P.t + ih / 2} fontSize="11" fill="#4D5C69" textAnchor="middle"
          fontWeight="600" transform={`rotate(-90 14 ${P.t + ih / 2})`}>{yLabel || y}</text>
      </svg>
      {hover !== null && pts[hover] && (
        <div className="absolute top-2 right-2 bg-white border border-wb-line rounded shadow-lg px-3 py-2 text-[11.5px] pointer-events-none">
          <div className="font-bold text-wb-slateDk">
            {pts[hover].d.name || `${pts[hover].d.district ?? ''}`}
          </div>
          <div className="text-wb-muted">
            {pts[hover].d.province ?? pts[hover].d.provinces ?? ''}
          </div>
          <div className="mt-1 text-wb-slate">
            {yLabel || y} {Number(pts[hover].d[y]).toFixed(0)} · {xLabel || x} {Number(pts[hover].d[x]).toFixed(0)}
          </div>
        </div>
      )}
    </div>
  )
}
