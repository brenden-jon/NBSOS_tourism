import { useMemo, useState } from 'react'
import MapCanvas from '../components/MapCanvas'
import { Hero, Section, Callout, Loading, ErrorBox } from '../components/ui'
import { useData } from '../lib/useData'

const TIER = {
  priority:    { label: 'PMTS 2025–2030 priority destination', color: '#7FA23A' },
  action_plan: { label: 'Recent ATP destination action plan',  color: '#71AAD7' },
}

export default function Strategy() {
  const { data: gov, loading, error } = useData('gov_strategy.json')
  const { data: dests } = useData('gov_destinations.geojson')
  const [basemap, setBasemap] = useState('light')
  const [selected, setSelected] = useState(null)

  const layers = useMemo(() => {
    if (!dests) return []
    return [
      { id: 'dest-fill', data: dests, type: 'fill',
        paint: {
          'fill-color': ['match', ['get', 'tier'], 'priority', '#7FA23A', '#71AAD7'],
          'fill-opacity': ['case', ['==', ['get', 'id'], selected?.id ?? ''], 0.62, 0.30],
        } },
      { id: 'dest-line', data: dests, type: 'line',
        paint: {
          'line-color': ['match', ['get', 'tier'], 'priority', '#5C7A22', '#3E7CAB'],
          'line-width': ['case', ['==', ['get', 'id'], selected?.id ?? ''], 2.6, 1.1],
        } },
    ]
  }, [dests, selected])

  if (loading) return <Loading what="the government strategy" />
  if (error) return <div className="wrap py-16"><ErrorBox message={error} /></div>

  const plan = gov.plan
  const priority = gov.destinations.filter(d => d.tier === 'priority')
  const action = gov.destinations.filter(d => d.tier === 'action_plan')

  return (
    <>
      <Hero
        eyebrow="Policy input"
        title="Government of Panama tourism strategy"
        lead="The scan treats official tourism policy as a formal analytical input and as a comparator — never as a boundary on the analysis. This section sets out what the current plan says, where its priority destinations are, and how they enter the opportunity scan."
      />

      <Section eyebrow="Source of record" title={plan.title_en}>
        <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
          <div className="prose-wb space-y-4">
            <p className="text-[15px]">
              <strong>{plan.title_es}</strong> — the current national tourism master plan, prepared by
              the {plan.authority} and approved by the {plan.approved_by}, covering {plan.period}.
              It supersedes the {plan.predecessor.short}.
            </p>
            <p>{plan.selection_logic}</p>
            <p>{plan.strategy_note}</p>
            <div className="flex flex-wrap gap-3 pt-1">
              <a href={plan.url} target="_blank" rel="noreferrer" className="btn-green">
                Open the master plan (PDF) ↗
              </a>
              <a href={plan.predecessor.url} target="_blank" rel="noreferrer"
                className="btn border border-wb-line text-wb-slate hover:bg-wb-wash">
                Predecessor 2020–2025 ↗
              </a>
            </div>
            <p className="text-[12px] text-wb-muted pt-1">Accessed {plan.accessed}.</p>
          </div>
          <div className="space-y-4">
            <div className="card p-5">
              <div className="eyebrow mb-3">Strategic objectives</div>
              <ul className="space-y-2.5">
                {plan.objectives.map(o => (
                  <li key={o.code} className="flex gap-3">
                    <span className="shrink-0 w-6 h-6 grid place-items-center rounded bg-wb-green
                                     text-white text-[11px] font-bold">{o.code}</span>
                    <span className="text-[13.5px] leading-snug">{o.text_en}</span>
                  </li>
                ))}
              </ul>
            </div>
            <Callout title="Why the previous plan matters" tone="amber">
              The {plan.predecessor.short} reached {plan.predecessor.completion_rate} of its targets.
              {' '}{plan.predecessor.note}
            </Callout>
          </div>
        </div>
      </Section>

      <Section tint eyebrow="Geography" title="Where the plan concentrates effort"
        lead="The ten priority destinations of the PMTS 2025–2030, plus destinations with recent standalone ATP action plans. Click a destination for its value proposition.">
        <div className="grid gap-5 lg:grid-cols-[1.25fr_1fr]">
          <div className="card overflow-hidden">
            <MapCanvas className="h-[520px]" layers={layers} basemap={basemap}
              onBasemapChange={setBasemap} cursorLayers={['dest-fill']}
              onFeatureClick={p => setSelected(p)} />
          </div>
          <div className="space-y-4">
            <div className="flex flex-wrap gap-3">
              {Object.entries(TIER).map(([k, v]) => (
                <span key={k} className="inline-flex items-center gap-2 text-[12px] text-wb-slate">
                  <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: v.color }} />{v.label}
                </span>
              ))}
            </div>
            {selected ? (
              <div className="card p-5">
                <div className="eyebrow mb-1">{TIER[selected.tier]?.label}</div>
                <h3 className="h-sub">{selected.name}</h3>
                <p className="prose-wb mt-3 text-[13.5px]">{selected.vocation_en}</p>
                <div className="mt-4 pt-3 border-t border-wb-line">
                  <div className="text-[11px] uppercase tracking-wider text-wb-muted mb-1.5">Priority products</div>
                  <div className="flex flex-wrap gap-1.5">
                    {String(selected.products).split('; ').map(p => (
                      <span key={p} className="chip bg-wb-wash text-wb-slate border border-wb-line">{p}</span>
                    ))}
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-[11px] uppercase tracking-wider text-wb-muted mb-1.5">Nature assets named</div>
                  <div className="flex flex-wrap gap-1.5">
                    {String(selected.nature_hooks).split('; ').map(p => (
                      <span key={p} className="chip bg-wb-green/10 text-wb-greenDk">{p}</span>
                    ))}
                  </div>
                </div>
                <div className="mt-3 text-[11.5px] text-wb-muted">
                  Districts used to derive this polygon: {selected.districts}
                </div>
                <button onClick={() => setSelected(null)}
                  className="mt-4 text-[12px] font-semibold text-wb-blueDk hover:underline">Clear selection</button>
              </div>
            ) : (
              <div className="card p-5">
                <div className="h-sub mb-3">Priority destinations ({priority.length})</div>
                <ul className="space-y-1.5">
                  {priority.map(d => (
                    <li key={d.id}>
                      <button onClick={() => setSelected(d)}
                        className="text-left text-[13.5px] text-wb-slate hover:text-wb-blueDk hover:underline">
                        {d.name}
                      </button>
                    </li>
                  ))}
                </ul>
                <div className="h-sub mt-5 mb-3">Recent action plans ({action.length})</div>
                <ul className="space-y-1.5">
                  {action.map(d => (
                    <li key={d.id}>
                      <button onClick={() => setSelected(d)}
                        className="text-left text-[13.5px] text-wb-slate hover:text-wb-blueDk hover:underline">
                        {d.name}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <Callout title="These boundaries are derived, not official" tone="amber">
              The master plan names destinations but publishes no boundaries. Each polygon is the
              smallest set of official <em>distrito</em> units containing the places the plan names.
              They support spatial comparison only.
            </Callout>
          </div>
        </div>
      </Section>

      <Section eyebrow="Nature in the plan"
        title="What the government itself says about nature, community and sustainability"
        lead="These statements are the plan's own. They matter because they define the policy space a nature-tourism investment would occupy.">
        <div className="grid gap-4 sm:grid-cols-2">
          {plan.nature_context.map((t, i) => (
            <div key={i} className="card p-5 border-l-4 border-l-wb-green">
              <p className="prose-wb text-[13.5px]">{t}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section tint eyebrow="Products" title="Thematic and heritage routes named in the plan">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {gov.routes.map(r => (
            <div key={r.name} className="card p-4">
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${r.nature ? 'bg-wb-green' : 'bg-wb-muted'}`} />
                <span className="font-bold text-[13.5px] text-wb-slateDk">{r.name}</span>
              </div>
              <div className="text-[11px] uppercase tracking-wider text-wb-muted mt-1">{r.type}</div>
              <p className="prose-wb mt-2 text-[12.5px]">{r.note}</p>
            </div>
          ))}
        </div>
        <p className="mt-5 text-[12px] text-wb-muted">
          Green markers indicate routes whose core product is nature-based.
        </p>
      </Section>

      <Section eyebrow="How this enters the scan"
        title="Policy is compared against the analysis, never used to filter it">
        <div className="grid gap-4 sm:grid-cols-3">
          {[
            { t: 'Reinforces', c: '#7FA23A', d: 'The analysis independently identifies development potential inside a declared priority destination. Evidence supports the plan.' },
            { t: 'Refines', c: '#D99A2B', d: 'The area is a declared priority, but the analysis says the binding issue is conservation, resilience or pressure management rather than supply expansion.' },
            { t: 'Outside', c: '#3E7CAB', d: 'The area sits outside all ten priority destinations. Surfaced by the spatial evidence alone — a candidate for future planning consideration.' },
          ].map(x => (
            <div key={x.t} className="card p-5 border-t-4" style={{ borderTopColor: x.c }}>
              <div className="font-bold text-[15px] text-wb-slateDk">{x.t}</div>
              <p className="prose-wb mt-2 text-[13.5px]">{x.d}</p>
            </div>
          ))}
        </div>
      </Section>
    </>
  )
}
