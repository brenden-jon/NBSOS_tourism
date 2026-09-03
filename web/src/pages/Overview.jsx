import { Hero, Section, Callout, Stat } from '../components/ui'
import { ACTIONS, FAMILIES } from '../lib/constants'
import { useData } from '../lib/useData'

const TABS = [
  { href: '#strategy', t: 'Government Strategy',
    d: 'The current national tourism master plan (PMTS 2025–2030), its ten priority destinations mapped, and its commitments on nature, community and sustainability.' },
  { href: '#explorer', t: 'Data Explorer',
    d: 'The underlying data: ecosystems, existing tourism assets and protected areas. Nothing on this tab is modelled.' },
  { href: '#analysis', t: 'Analysis',
    d: 'The national screening grid. Map any indicator, review how recommendation types are distributed, and inspect the measurements behind any cell.' },
  { href: '#opportunities', t: 'Opportunities',
    d: 'Results. Named areas, each with specific sites for visitor infrastructure, specific zones for ecosystem investment, and an indicative employment estimate.' },
  { href: '#methods', t: 'Methods & Limits',
    d: 'Indicator construction, data sources and licences, and the limitations of the analysis.' },
]

const STEPS = [
  { n: '1', t: 'Divide the country', d: 'A national grid of 37 km² hexagons over all land and the coastal water tourism uses.' },
  { n: '2', t: 'Measure each cell', d: 'Ecosystems, terrain, biodiversity records, protection status, existing tourism supply, modelled travel time and population — from open data.' },
  { n: '3', t: 'Score six dimensions', d: 'Six indicator families, each built from sub-indicators that remain inspectable throughout.' },
  { n: '4', t: 'Screen for feasibility', d: 'Places without road access, more than 8 hours from a gateway, or inside the Darién Gap advisory zone cannot receive a development recommendation.' },
  { n: '5', t: 'Classify and cluster', d: 'Each cell receives the recommendation its evidence supports, or none. Contiguous strong cells form named Opportunity Areas.' },
  { n: '6', t: 'Identify sites and zones', d: 'Within each area, locate specific sites for visitor infrastructure and specific zones for ecosystem protection or restoration.' },
]

export default function Overview() {
  const { data: s } = useData('summary.json')

  return (
    <>
      <Hero
        eyebrow="World Bank prototype · Panama pilot"
        title="Tourism–Nature Opportunity Scan"
        lead="A national screening tool that identifies where tourism investment offers the greatest potential, and where protecting or restoring ecosystems would support that tourism and strengthen resilience. Panama is the pilot country."
      >
        <div className="flex flex-wrap gap-3">
          <a href="#opportunities" className="btn-green">Results</a>
          <a href="#methods" className="btn-ghost">Method</a>
        </div>
      </Hero>

      <Section eyebrow="Purpose"
        title="What this pilot does"
        lead="An exploratory prototype testing whether a rapid, open-data screening can produce tourism investment ideas specific enough to act on. The method is designed to transfer to other countries by swapping the national data layers.">
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="prose-wb space-y-4 text-[15px]">
            <p>
              It produces two distinct answers for each place it identifies: where visitor
              infrastructure could be developed, and where ecosystems should be protected or
              restored to support that tourism and improve resilience. These are separate budget
              lines and separate implementing responsibilities, so they are reported separately.
            </p>
            <p>
              The approach adapts the World Bank's Nature-Based Solutions Opportunity Scan, which
              screens for where nature can reduce a specified climate hazard. The discipline is
              the same — open data, rapid upstream screening, and a preference for protecting
              functioning ecosystems over creating new ones.
            </p>
            <p>
              The national tourism master plan is used as an input and reference. The screening
              covers the whole country, so results can be compared against the destinations
              government has already prioritised as well as identifying additional areas.
            </p>
          </div>
          <Callout title="What it is not" tone="amber">
            <ul className="list-disc pl-5 space-y-1.5">
              <li>Not a flood-risk model — resilience indicators are screening proxies and no avoided damages are estimated.</li>
              <li>Not a tourism master plan, feasibility study or ecological assessment.</li>
              <li>Not a recommendation to designate protected areas — candidates need ecological, social, legal and stakeholder assessment.</li>
              <li>Not a jobs forecast — employment figures are order-of-magnitude ranges for a stated hypothetical package.</li>
            </ul>
          </Callout>
        </div>
      </Section>

      <Section tint eyebrow="Method" title="How the screening works">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {STEPS.map(x => (
            <div key={x.n} className="card p-5">
              <div className="flex items-center gap-2.5 mb-2">
                <span className="grid place-items-center w-6 h-6 rounded-full bg-wb-green
                                 text-white text-[11px] font-bold">{x.n}</span>
                <span className="font-bold text-[14.5px] text-wb-slateDk">{x.t}</span>
              </div>
              <p className="prose-wb text-[13.5px]">{x.d}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section eyebrow="Indicators" title="What is measured">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FAMILIES.map(f => (
            <div key={f.key} className="card p-5">
              <div className="flex items-baseline gap-2.5">
                <span className="text-[11px] font-bold tracking-wider text-white bg-wb-slate rounded px-1.5 py-0.5">{f.key}</span>
                <span className="font-bold text-[14.5px] text-wb-slateDk">{f.label}</span>
              </div>
              <p className="prose-wb mt-2 text-[13px]">{f.desc}</p>
            </div>
          ))}
        </div>
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Object.values(ACTIONS).filter(a => a.key !== 'NONE').map(a => (
            <div key={a.key} className="card p-5">
              <div className="flex items-center gap-2.5">
                <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: a.color }} />
                <span className="font-bold text-[14.5px] text-wb-slateDk">{a.label}</span>
              </div>
              <p className="prose-wb mt-2 text-[13px]">{a.blurb}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section tint eyebrow="Data" title="Sources"
        lead="National government data where available, established global datasets elsewhere. All of it can be regenerated from the scripts in the repository.">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[
            ['Panama’s own protected-area register', 'MiAmbiente SINAP 2025 — 91 areas with IUCN category and legal basis. Preferred over global datasets.'],
            ['National boundaries and hydrography', 'Districts, corregimientos, watersheds, bathymetry, ecoregions and life zones, via the STRI GIS Portal.'],
            ['ESA WorldCover 10 m', 'Land cover including mangrove, read remotely so nothing large is stored.'],
            ['Copernicus DEM & WorldPop', 'Terrain, relief and population at 30 m and 100 m.'],
            ['OpenStreetMap', 'Accommodation, attractions, beaches, trails, dive sites, marinas, roads — with its biases documented.'],
            ['GBIF', '10.1 million vertebrate occurrence records, aggregated to species richness.'],
          ].map(([t, d]) => (
            <div key={t} className="card p-5">
              <div className="font-bold text-[14px] text-wb-slateDk">{t}</div>
              <p className="prose-wb text-[13px] mt-2">{d}</p>
            </div>
          ))}
        </div>
        <p className="mt-5 text-[13px] text-wb-slate">
          Full catalogue with licences and redistribution terms under
          <a className="text-wb-blueDk font-semibold hover:underline ml-1" href="#methods">Methods &amp; Limits</a>.
        </p>
      </Section>

      <Section eyebrow="Navigation" title="Sections of this site">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {TABS.map(c => (
            <a key={c.href} href={c.href}
              className="card p-5 hover:border-wb-blue hover:shadow-md transition-all group">
              <div className="font-bold text-[15px] text-wb-slateDk group-hover:text-wb-blueDk">{c.t} →</div>
              <p className="prose-wb mt-2 text-[13.5px]">{c.d}</p>
            </a>
          ))}
        </div>
      </Section>

      {s && (
        <Section tint eyebrow="Scale" title="The Panama pilot">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Stat value={s.cells.toLocaleString()} label="Screening cells" sub="37 km² hexagons" />
            <Stat value={s.opportunity_areas} label="Opportunity areas" sub="Named, ranked and written up" />
            <Stat value={s.tourism_nodes ?? '—'} label="Tourism investment sites"
              sub="Specific locations with road access and a settlement nearby" />
            <Stat value={s.nature_zones ?? '—'} label="Nature action zones"
              sub="Ecosystem-specific protect or restore areas" />
          </div>
        </Section>
      )}
    </>
  )
}
