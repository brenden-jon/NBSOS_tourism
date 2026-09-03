import { Hero, Section, Callout } from '../components/ui'
import { ACCESSED, LIMITS, NOT_USED, SOURCES, STEPS } from '../lib/catalogue'
import { FAMILIES } from '../lib/constants'

export default function Methods() {
  return (
    <>
      <Hero eyebrow="Transparency" title="Methods, data and limitations"
        lead="Everything this prototype claims rests on data you can trace and steps you can rerun. This section documents the sources and their licences, the analytical pipeline, and — at least as importantly — what the analysis cannot tell you." />

      <Section eyebrow="Approach" title="From the NBS Opportunity Scan to a tourism question">
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="prose-wb space-y-4">
            <p>
              The World Bank's Nature-Based Solutions Opportunity Scan screens for investment
              opportunities by asking where nature can reduce a specified climate hazard, working
              through four steps: understand the problem, map suitability, model benefits, support
              decisions. It prioritises protecting functioning ecosystems over restoring them, and
              restoring over creating new ones.
            </p>
            <p>
              Tourism poses a different question. There is no single hazard to reduce. The question
              is where conservation and tourism investment jointly produce economic development,
              resilience and biodiversity outcomes. So the hazard-and-benefit spine is replaced with
              a six-family evidence structure, while the intervention hierarchy is kept: the
              classification favours protection and restoration over new construction, and damps
              development recommendations where ecological sensitivity is high.
            </p>
          </div>
          <Callout title="Unit of analysis" tone="blue">
            <p>
              H3 resolution-6 hexagons, about 37 km² each. 4,434 cells cover Panama's land area and
              a 30 km band measured from every coastline — including island coastlines, so Bocas del
              Toro, Guna Yala, Las Perlas, Coiba and Taboga get genuine marine cells rather than
              being clipped at the shore.
            </p>
            <p className="mt-2.5">
              All areas and distances are computed in UTM zone 17N (EPSG:32617); display is WGS 84.
              Panama's very large offshore marine protected areas — Banco Volcán and Cordillera de
              Coiba — extend far beyond the band and are carried as context, not scored, because
              tourism relevance there is negligible.
            </p>
          </Callout>
        </div>
      </Section>

      <Section tint eyebrow="Pipeline" title="Seven stages, all reproducible">
        <div className="grid gap-3">
          {STEPS.map(s => (
            <div key={s.n} className="card p-4 flex gap-4">
              <div className="shrink-0 w-16 text-center">
                <div className="text-[11px] font-bold text-white bg-wb-slate rounded px-1.5 py-1">{s.n}</div>
              </div>
              <div>
                <div className="font-bold text-[14px] text-wb-slateDk">{s.t}</div>
                <p className="prose-wb text-[13.5px] mt-1">{s.d}</p>
              </div>
            </div>
          ))}
        </div>
        <p className="mt-5 text-[13px] text-wb-slate">
          Run end to end with <code className="bg-white border border-wb-line rounded px-1.5 py-0.5 text-[12px]">make all</code>.
          Raw downloads are cached and git-ignored; only compact derived outputs are committed.
        </p>
      </Section>

      <Section eyebrow="Indicators" title="What each family is built from">
        <div className="overflow-x-auto">
          <table className="tbl min-w-[720px]">
            <thead><tr><th className="w-[130px]">Family</th><th>Definition</th></tr></thead>
            <tbody>
              {FAMILIES.map(f => (
                <tr key={f.key}>
                  <td><span className="font-bold text-wb-slateDk">{f.key}</span><br />
                    <span className="text-[12px] text-wb-muted">{f.label}</span></td>
                  <td className="text-wb-slate">{f.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-6 grid gap-5 lg:grid-cols-2">
          <Callout title="Why percentile ranks, not min–max" tone="blue">
            Almost every count variable here is heavily right-skewed — Panama City has two orders of
            magnitude more accommodation than anywhere else. Min–max normalisation would flatten the
            rest of the country to near zero. Percentile ranking preserves discrimination across the
            whole distribution. True zeros are pinned to zero rather than given the mid-rank of the
            tied zero block.
          </Callout>
          <Callout title="Why zone-aware weighting" tone="green">
            A marine cell has no forest and an inland cell has no reef. Scoring absent features as
            zero would systematically punish whole zones. Each family declares which sub-indicators
            apply in which zone and renormalises its weights over the applicable set.
          </Callout>
        </div>
      </Section>

      <Section tint eyebrow="Provenance" title="Data sources and licences"
        lead={`All sources accessed ${ACCESSED}. Where a source could be used but not redistributed, only derived aggregates are published here.`}>
        <div className="space-y-3">
          {SOURCES.map(s => (
            <div key={s.name} className="card p-5">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <div className="font-bold text-[14.5px] text-wb-slateDk">{s.name}</div>
                <span className="chip bg-wb-green/12 text-wb-greenDk">{s.lic}</span>
              </div>
              <div className="text-[12px] text-wb-muted mt-0.5">{s.org}</div>
              <div className="grid gap-x-6 gap-y-2 sm:grid-cols-2 mt-3 text-[13px]">
                <div><span className="text-wb-muted">Used for: </span><span className="text-wb-slate">{s.use}</span></div>
                <div><span className="text-wb-muted">Redistribution: </span><span className="text-wb-slate">{s.redis}</span></div>
              </div>
              {s.note && <p className="prose-wb text-[12.5px] mt-2.5 text-wb-slate">{s.note}</p>}
              {s.url && <a href={s.url} target="_blank" rel="noreferrer"
                className="inline-block mt-2.5 text-[12px] font-semibold text-wb-blueDk hover:underline">
                Source ↗</a>}
            </div>
          ))}
        </div>
      </Section>

      <Section eyebrow="Deliberate omissions" title="Datasets considered and not used"
        lead="Each of these would improve the analysis. Each is excluded for a stated reason, and each is a candidate for phase 2.">
        <div className="grid gap-4 sm:grid-cols-2">
          {NOT_USED.map(s => (
            <div className="card p-5 border-l-4 border-l-act-adapt" key={s.name}>
              <div className="font-bold text-[14px] text-wb-slateDk">{s.name}</div>
              <p className="prose-wb text-[13px] mt-2">{s.why}</p>
              {s.url && <a href={s.url} target="_blank" rel="noreferrer"
                className="inline-block mt-2 text-[12px] font-semibold text-wb-blueDk hover:underline">More ↗</a>}
            </div>
          ))}
        </div>
      </Section>

      <Section tint eyebrow="Honesty" title="Limitations">
        <div className="grid gap-4 lg:grid-cols-2">
          {LIMITS.map(l => (
            <div key={l.t} className="card p-5 border-l-4 border-l-act-manage">
              <div className="font-bold text-[14px] text-wb-slateDk">{l.t}</div>
              <p className="prose-wb text-[13.5px] mt-2">{l.d}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section eyebrow="What comes next" title="Phase 2">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[
            ['World Bank ~90 m flood hazard', 'Add hazard rasters as another zonal-statistics stage and convert the resilience proxy into an exposure-weighted estimate. The grid and pipeline are already structured for this.'],
            ['Reef extent and condition', 'Allen Coral Atlas benthic and geomorphic maps under an appropriate data agreement, plus bleaching and turbidity time series.'],
            ['Key Biodiversity Areas', 'KBA and IBA overlay under a data agreement, replacing the ecoregion-rarity and occurrence-richness proxies with designated biodiversity priorities.'],
            ['Observed visitation', 'ATP visitor statistics, protected-area entry records and mobile-positioning or card-spend proxies to replace OSM density as the tourism-development measure.'],
            ['Employment and enterprise data', 'INEC establishment and employment data by corregimiento to move the jobs lens from qualitative to semi-quantitative.'],
            ['Stakeholder validation', 'Review of candidate areas with ATP, MiAmbiente and the Comités de Gestión de Destinos, and with comarca authorities where relevant.'],
          ].map(([t, d]) => (
            <div key={t} className="card p-5">
              <div className="font-bold text-[14px] text-wb-slateDk">{t}</div>
              <p className="prose-wb text-[13px] mt-2">{d}</p>
            </div>
          ))}
        </div>
      </Section>
    </>
  )
}
