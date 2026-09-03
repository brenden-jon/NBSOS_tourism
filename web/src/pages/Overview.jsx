import { Hero, Section, Stat, Callout, Loading } from '../components/ui'
import { ACTIONS, FAMILIES } from '../lib/constants'
import { useData } from '../lib/useData'

function ActionCard({ a, count }) {
  return (
    <div className="card p-5 h-full flex flex-col">
      <div className="flex items-center gap-2.5">
        <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: a.color }} />
        <span className="font-bold text-[15px] text-wb-slateDk">{a.label}</span>
      </div>
      <p className="prose-wb mt-2.5 text-[13.5px] flex-1">{a.blurb}</p>
      {count != null && (
        <div className="mt-4 pt-3 border-t border-wb-line text-[12px] text-wb-muted">
          <span className="font-bold text-wb-slateDk text-[15px]">{count}</span> opportunity area{count === 1 ? '' : 's'}
        </div>
      )}
    </div>
  )
}

export default function Overview() {
  const { data: s } = useData('summary.json')

  return (
    <>
      <Hero
        eyebrow="World Bank · Nature-Based Solutions Opportunity Scan · Panama pilot"
        title="Where could tourism investment, conservation, resilience and local jobs reinforce each other in Panama?"
        lead="A screening prototype that adapts the Nature-Based Solutions Opportunity Scan to tourism investment planning. It runs a national spatial analysis over open data, then names specific places and explains what to do there — and why."
      >
        <div className="flex flex-wrap gap-3">
          <a href="#opportunities" className="btn-green">See the opportunities →</a>
          <a href="#strategy" className="btn-ghost">Government strategy</a>
          <a href="#methods" className="btn-ghost">How it works</a>
        </div>
      </Hero>

      <Section
        eyebrow="The question"
        title="A tourism master plan tells you where government intends to invest. It does not tell you where nature makes that investment work."
        lead="The NBS Opportunity Scan asks where nature can reduce a specified climate hazard. Tourism poses a different question: where can conservation and tourism investment jointly create economic development, resilience and biodiversity outcomes? This prototype answers that for Panama at national screening scale — independently of, and then compared against, the government's own priorities."
      >
        {s && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Stat value={s.cells.toLocaleString()} label="Screening cells"
              sub={`${s.cell_km2} km² hexagons over ${s.land_km2.toLocaleString()} km² of land plus a ${s.coastal_band_km} km coastal band`} />
            <Stat value={s.opportunity_areas} label="Opportunity areas"
              sub="Contiguous clusters of strongly-scoring cells, named and written up" />
            <Stat value={`${s.share_in_gov_dest}%`} label="Of Panama inside a priority destination"
              sub="The analysis covers the whole country, not only these areas" />
            <Stat value={s.cells_high_nav_low_tdl.toLocaleString()} label="High-nature, low-supply cells"
              sub="Strong natural attraction with little existing tourism development" />
          </div>
        )}
      </Section>

      <Section tint eyebrow="What it produces"
        title="Four kinds of recommendation, following the NBS intervention hierarchy"
        lead="Protect what already functions before restoring it; restore before building new. Each place gets a primary recommendation plus any secondary ones — because in Panama the most interesting answer is often 'protect the reef and build the snorkelling access', not one or the other.">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Object.values(ACTIONS).map(a => (
            <ActionCard key={a.key} a={a} count={s?.opp_by_action?.[a.key]} />
          ))}
        </div>
      </Section>

      <Section eyebrow="How places are compared"
        title="Six named indicator families — not one opaque index"
        lead="Every score on this site decomposes into sub-indicators you can inspect. If a place is recommended, the tool can tell you which measurements produced that recommendation.">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FAMILIES.map(f => (
            <div key={f.key} className="card p-5">
              <div className="flex items-baseline gap-2.5">
                <span className="text-[11px] font-bold tracking-wider text-white bg-wb-slate rounded px-1.5 py-0.5">{f.key}</span>
                <span className="font-bold text-[14.5px] text-wb-slateDk">{f.label}</span>
              </div>
              <p className="prose-wb mt-2 text-[13px]">{f.desc}</p>
              {s && <div className="mt-3 text-[11.5px] text-wb-muted">
                National mean <span className="font-bold text-wb-slateDk">{s.family_means[f.key]}</span>/100
              </div>}
            </div>
          ))}
        </div>
      </Section>

      <Section tint eyebrow="Relationship to government policy"
        title="The Plan Maestro is an input, not a boundary">
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="prose-wb space-y-4 text-[15px]">
            <p>
              The analysis runs across all of Panama. The government's ten priority destinations
              are then overlaid on the results, so every opportunity can be labelled by how it
              relates to declared policy.
            </p>
            <p>
              That distinction is the point. It lets a task team see where the evidence
              <strong> reinforces</strong> a government priority, where it <strong>refines</strong> the
              emphasis within one, and where it surfaces something <strong>outside</strong> the current
              plan entirely.
            </p>
            {s && (
              <div className="grid grid-cols-3 gap-3 pt-2">
                {['reinforces', 'refines', 'new'].map(k => (
                  <div key={k} className="card p-4 text-center">
                    <div className="text-[22px] font-bold text-wb-slateDk">
                      {s.opp_by_gov_relation?.[k] ?? 0}
                    </div>
                    <div className="text-[11px] uppercase tracking-wider text-wb-muted mt-1">{k}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
          <Callout title="What this prototype is not" tone="amber">
            <ul className="list-disc pl-5 space-y-1.5">
              <li>Not a flood-risk model. Resilience indicators are spatial screening proxies; no avoided damages are estimated.</li>
              <li>Not a tourism master plan, feasibility study or ecological assessment.</li>
              <li>Not a protected-area designation recommendation. Candidate protection areas require ecological, social, legal and stakeholder assessment.</li>
              <li>Not a jobs forecast. Employment is treated as a qualitative opportunity lens.</li>
            </ul>
          </Callout>
        </div>
      </Section>

      <Section eyebrow="Next" title="Start with the places">
        <div className="grid gap-4 sm:grid-cols-3">
          {[
            { href: '#opportunities', t: 'Opportunity areas', d: 'Named places with investment narratives, evidence and trade-offs.' },
            { href: '#analysis', t: 'National analysis', d: 'The full screening grid, indicator by indicator, with an inspector.' },
            { href: '#strategy', t: 'Government strategy', d: 'The Plan Maestro 2025–2030, its ten destinations and how they enter the scan.' },
          ].map(c => (
            <a key={c.href} href={c.href}
              className="card p-5 hover:border-wb-blue hover:shadow-md transition-all group">
              <div className="font-bold text-[15px] text-wb-slateDk group-hover:text-wb-blueDk">{c.t} →</div>
              <p className="prose-wb mt-2 text-[13.5px]">{c.d}</p>
            </a>
          ))}
        </div>
      </Section>
    </>
  )
}
