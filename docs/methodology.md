# Methodology

## 1. The question, and why it differs from the NBS Opportunity Scan

The NBSOS screens for investment opportunities by asking **where nature can reduce a specified
climate hazard**, through four steps: understand the problem, map NBS suitability, model NBS
benefits, provide decision support. It applies a hierarchy of intervention — protect existing
ecosystems, then enhance management, then rehabilitate and restore, and only then create new
nature-based assets.

Tourism has no single hazard to reduce. The question here is:

> Where can nature conservation/restoration and tourism investment jointly create sustainable
> economic development, resilience and biodiversity outcomes?

So the hazard–suitability–benefit spine is replaced by a **six-family evidence structure**,
while the intervention hierarchy is retained in the classification: protection and restoration
outrank new construction, and development recommendations are explicitly damped where
ecological sensitivity is high.

## 2. Unit of analysis

H3 resolution-6 hexagons, mean area ~37 km². **3,417 cells** cover:

- all of Panama's land area (74,274 km² as measured from the official province layer, against a
  reference figure of ~75,420 km²), plus
- the coastal water tourism actually uses: **10 km from every coastline**, island coastlines
  included, **extended to 30 km wherever shallow shelf (<20 m) or a marine protected area makes
  the water relevant**.

The band is computed by buffering the dissolved national land polygon and subtracting it, so
Bocas del Toro, Guna Yala, Las Perlas, Coiba, Taboga and the Islas Secas all generate genuine
marine cells rather than being clipped at the shore.

The 30 km buffer is a *search* extent, not an analysis extent. Scoring all of it produced ~1,000
near-empty open-ocean cells that dragged every coastal aggregate down and cluttered the map, so
open water with no shelf and no designation is dropped.

Cells are typed by land fraction: `inland` (≥98% land), `coastal` (2–98%), `nearshore` (water
within 10 km of land), `marine` (retained only over shelf or inside an MPA). Panama's very large offshore MPAs — Banco Volcán
(9.3 M ha) and Cordillera de Coiba (6.8 M ha) — extend well beyond the band and are carried as
context layers rather than scored cells, because tourism relevance there is negligible.

All areas and distances are computed in **EPSG:32617** (UTM 17N); display is WGS 84.

## 3. Measurement

| Step | What it produces |
|---|---|
| `13_rasters.py` | Land-cover fractions from ESA WorldCover 10 m (tree, mangrove, wetland, built, crop, water); elevation mean/min/max and local relief from Copernicus DEM GLO-30; population from WorldPop 100 m |
| `14_gbif.py` | Vertebrate species richness and record counts per H3 resolution-5 parent cell, inherited by its resolution-6 children |
| `15_access.py` | Modelled travel time to tourism gateways and to Panama City |
| `16_vectors.py` | Protection fractions (any / strict IUCN I–IV / marine / Ramsar), dominant protected area, ecoregion, life zone, watershed, shallow-shelf fraction, distance to coast, and counts of OSM tourism and nature assets |

Rasters are read remotely as cloud-optimised GeoTIFFs at decimated resolution using windowed
overview reads. Nothing large is written to disk; only per-hexagon aggregates are kept. This is
what allows a real 10 m land-cover analysis inside a small repository.

### Accessibility model

A 500 m friction surface over Panama, then a multi-source least-cost accumulation
(`skimage.graph.MCP_Geometric`) from seven tourism gateways (Tocumen, Albrook, Panamá Pacífico,
David, Bocas del Toro, Río Hato, Colón) and separately from Panama City.

- Road speeds by OSM `highway` class (motorway 90 → unclassified 25 km/h), halved on unpaved surfaces.
- Off-road land speed 4.5 km/h in open country falling to 1.5 km/h under dense tree cover,
  further reduced by local relief.
- Sea traversable at a uniform 20 km/h, standing in for boat access.

Straight-line distance would badly misrepresent Panama, where the Darién has no roads and the
Caribbean coast east of Portobelo is boat-access only. Validation against known geography:
Boquete 1.2 h, Colón 1.2 h, David 3.0 h, Bocas del Toro 3.4 h, Pedasí 4.5 h, Darién
(Pinogana) 17.4 h from the nearest gateway.

## 4. The six indicator families

Each family is a weighted mean of named sub-indicators. Every sub-indicator is
**percentile-ranked to 0–100** over the cells where it is meaningful.

**Why percentile rank rather than min–max:** almost every count variable is heavily
right-skewed — Panama City has two orders of magnitude more accommodation than anywhere else —
and min–max normalisation would flatten the rest of the country to near zero. True zeros are
pinned to 0 rather than given the mid-rank of the tied zero block, so empty cells are not
inflated.

**Why zone-aware weighting:** a marine cell has no forest; an inland cell has no reef. Scoring
absent features as zero would systematically punish whole zones. Each family declares which
sub-indicators apply in which zone and renormalises its weights over the applicable set.

| Family | What it measures | Principal sub-indicators |
|---|---|---|
| **NAV** Nature attraction | What a visitor would travel for | forest, relief, named natural features, protected-area draw, species richness, mangrove, beaches — or, at sea: shallow shelf, mangrove, reefs, marine operators |
| **TDL** Tourism development | What is already built | accommodation, food service, attractions and visitor infrastructure, trails, marine operators, airports |
| **ACC** Accessibility | Modelled travel time | time to nearest gateway (65%), time to Panama City (35%) |
| **BCV** Biodiversity value | Conservation significance | **threatened (IUCN CR/EN/VU) species richness**, total species richness, forest, ecoregion and life-zone rarity, protection cover, mangrove, Ramsar |
| **RES** Resilience function | Nature's protective role against modelled flood hazard | coastal: modelled wave attenuation by mangrove and reef over the population in the 1-in-100 yr coastal flood zone, plus restoration headroom; inland: catchment forest above flood-exposed population — see section 4c |
| **JOBS** Local opportunity | Capacity to capture value locally | local labour pool, decentralisation distance, comarca context, accessibility |

**RES is not a hazard model.** It is a spatial coincidence measure: protective ecosystems in
front of low-lying people and assets, or catchment tree cover on slopes above them. No
hydrodynamic or probabilistic modelling has been done and no avoided damages are estimated.

## 4b. Development feasibility

Three screens are computed in `17_feasibility.py` and applied as **hard gates** on
development recommendations, not as score penalties:

| Screen | Rule |
|---|---|
| Access | a road, marina, ferry terminal or airstrip within 15 km |
| Remoteness | under 8 hours modelled travel from the nearest tourism gateway |
| Advisory zone | outside the Darien Gap border region |

**On the advisory zone.** The Darien Gap - the roadless forest along the Colombian border -
carries standing "do not travel" advisories and is an active irregular migration corridor. No
open dataset encodes this, so it is defined here explicitly: land within 40 km of the Colombian
border (geoBoundaries COL ADM0) that has no road access. It is a documented analytical
exclusion, not a measurement, and it is labelled as such wherever it appears. It suppresses
tourism-development recommendations only; the conservation value of the Darien is unaffected
and still scored.

2,221 of 3,417 cells (65%) pass all three screens.

**Access counts sea and air, not only roads.** An earlier version measured road distance
alone and excluded 131 high-attraction coastal and island cells - including Bocas del Toro
nearshore, three hours from a gateway - because islands have no roads to them. Panama's
tourism is substantially island-based (Bocas del Toro, Las Perlas, Guna Yala, the Golfo de
Chiriqui archipelagos) and boats and airstrips are how those destinations are reached.

*Why this was needed:* the first version recommended tourism development on cells with a
nature-attraction score of 0, no population, no road and a modelled 17-hour journey from the
nearest gateway, deep inside the Darien Gap.

## 4c. Flood hazard and the nature-based protection it meets

Steps 18 and 19 replace the earlier proxy-based resilience family with modelled hazard.

### Exposure (step 18)

WRI Aqueduct Floods v2, 30 arcsec (~1 km), CC BY 4.0: riverine and coastal inundation depth
for the 1-in-10 and 1-in-100 year return periods.

Population is intersected with the hazard **at the hazard's own resolution**: WorldPop (100 m)
is summed onto the 30 arcsec flood lattice, masked by depth, and only then aggregated to
hexagons. Taking a cell's total population and scaling it by the flooded fraction would smear
people evenly across terrain they do not occupy.

National result: **724,000 people in the 1-in-100-year riverine flood zone** and **12,400 in
the coastal one** — riverine exposure dominates in Panama by roughly sixty to one.

### Nature-based protection (step 19)

**Coastal — quantified.** Mangrove wave attenuation follows McIvor et al. (2012), who report
13–66% wave-height reduction per 100 m of mangrove width; the central case of 50% per 100 m is
applied exponentially, `attenuation = 1 − 0.5^(width/100)`. Width is estimated as mangrove area
divided by coastline length in the cell — conventional, and wrong wherever mangrove sits in a
lagoon rather than as a shore-parallel belt. Coral reef attenuation follows Ferrario et al.
(2014), who find reefs dissipate 97% of wave energy, but is capped at 60% here because the
input is reef-capable shelf extent, not reef condition. The two combine on the residual.

National result: of the 12,400 people in the coastal flood zone, wave energy reaching about
**8,300 of them (67%) is already moderated** by existing mangrove and reef. Widening thin belts
toward 150 m across **2,000 ha** would extend comparable moderation to roughly **1,600 more**.

**What this is not.** Wave attenuation is not the same as reducing still-water flood depth, and
Aqueduct's coastal layer is a surge-plus-depth product. Read the result as the share of wave
energy that existing ecosystems remove — not as avoided flooding, and certainly not as avoided
damages.

**Riverine — deliberately not quantified.** Catchment forest does moderate runoff, but the
effect on peak flows at basin scale is contested and depends on soil, antecedent conditions and
event size. Instead catchments are ranked by flood-exposed population downstream against forest
cover upstream — a prioritisation, not a hydrological claim. The catchments carrying most
exposure are Río Chiriquí (191,000 people, 53% forest), the Caimito–Juan Díaz basins around
Panama City (128,000, 45%) and Río Juan Díaz (87,000, 41%).

### The resilience family

RES is now built from these: for coastal cells, the coastal protection service delivered plus
the service restoration could add plus catchment retention plus exposure; for inland cells,
catchment retention, restoration priority and exposure.

## 5. Classification

Four action types, each scored continuously so that a place can be several things at once.
Each fit is a **weighted geometric mean** of 0–100 factors (weights sum to 1, values floored
at 1):

```
fit_invest  = geo(NAV·0.40, ACC·0.25, supply_headroom·0.20, JOBS·0.15) × damp
fit_protect = geo(BCV·0.40, protection_headroom·0.28, max(NAV,RES)·0.22, JOBS·0.10)
fit_adapt   = geo(TDL·0.40, RES·0.28, BCV·0.20, ACC·0.12)
fit_manage  = geo(BCV·0.38, sensitivity·0.30, ACC·0.22, pressure·0.10)
```

where

```
sensitivity          = 0.6·BCV + 0.4·strict protection
damp                 = 1 − 0.5·clip((sensitivity − 70)/30, 0, 1)
supply_headroom      = clip(100 − TDL, 1, 100)
protection_headroom  = clip(100 − strict protection, 1, 100)
pressure             = 100 · clip((BCV−50)/50, 0, 1) · clip((ACC−35)/65, 0, 1)
```

### Why geometric, not additive

An additive score lets a missing condition be bought back by the others, and in a first pass
that produced nonsense. Because most of Panama has no mapped tourism supply, the term
`(100 − TDL)` sat near 100 almost everywhere and handed every empty cell ~24 free points of
Invest fit — so cells with a nature-attraction score of 25 were being recommended for tourism
development. "Manage / Avoid" landed on roadless Darién forest with an accessibility score of 7,
where there is no visitor pressure to manage. A geometric mean makes each factor **necessary**:
if attraction is low, no amount of accessibility or headroom rescues the score.

`damp` is the deliberate asymmetry that stops the tool recommending construction in every
accessible beautiful place. `pressure` is what stops Manage / Avoid landing on the unreachable.

### Qualification before ranking

A cell must show **absolute** evidence before an action can be considered for it. These floors
cannot be traded off against another indicator:

| Action | Requires |
|---|---|
| Invest / Develop | NAV >= 40, ACC >= 35, **and** passing all three feasibility screens |
| Protect / Restore | BCV >= 40 |
| Adapt / Strengthen | TDL >= 25 - tourism supply that actually exists |
| Manage / Avoid | BCV >= 45 **and** ACC >= 35 - pressure requires reachability |

A cell qualifying for nothing is reported as **No strong basis**, not assigned a recommendation
by default. 38% of cells fall into this class, which is the honest answer for most of a country.

### Comparing the qualifying fits

The four scores do not share a natural scale — protection headroom is high almost everywhere in
Panama, so `fit_protect` sits structurally above `fit_invest`, and a raw argmax labelled 69% of
the country "Protect". Each fit is therefore **ranked against its own national distribution**,
and the primary recommendation is the action for which a cell ranks highest. The question
becomes: *is this cell more exceptional as a protection case than as a development case?*

Any action also ranking in the national top quartile is retained as a **secondary**
recommendation. That matters: the most interesting places in Panama are exactly those where
"protect the reef" and "develop the snorkelling access" are the same recommendation.

### Spatial smoothing

Before ranking, each fit is blended with a discounted share (0.40) of its immediate H3
neighbours. Recommendations are regional — a destination, a reef system or a catchment spans
several 37 km² cells — and ranking raw per-cell fits produced a salt-and-pepper map where
neighbours flipped class on trivial differences.

Two derived diagnostics are also carried:

- `protection_gap = max(NAV, RES) × (1 − strict protection)` — value not currently held by strict protection
- `supply_gap = max(NAV − TDL, 0)` — attraction that existing supply does not yet serve

## 6. Opportunity Areas

Within each action class, cells above the 85th percentile of that class's fit score are
retained, joined into connected components over H3 adjacency, and kept where the component has
≥4 cells (~150 km²). This yields **28 areas**. Each area is named from authoritative geography only: a protected area covering ≥35% of it,
else the government destination containing ≥50% of it, else the dominant district (or the two
dominant districts). Naming from individual OSM points was tried and abandoned — it produced
area names like "Mi jardín es su jardín" (a garden in Boquete) and "Panama Outdoor Adventures"
(a tour operator).

Areas are ranked by `fit × log(1 + cells)`, so a strong small cluster does not outrank a strong
large one.

Each area is tagged against the government plan by the share of its cells falling inside a
priority destination: **reinforces** (≥50% and a development recommendation), **refines** (≥50%
with a conservation, resilience or pressure recommendation), **partial** (>15%), **new** (≤15%).

## 6b. Tourism nodes and nature action zones

An Opportunity Area is still hundreds of square kilometres. `52_zones.py` produces the two
things a task team can act on, as separate outputs:

**Tourism nodes** - candidate sites for visitor infrastructure, anchored on a real named
natural feature (a beach, waterfall, dive site, viewpoint, peak). A site is admitted only if it
has a road within 2.5 km, a settlement within 12 km, and lies outside a strict protection core.
Assets within 4 km are grouped into one node. Built attractions count toward a node's asset mix
but never name it. Nodes are produced only for Invest and Adapt areas.

**Nature action zones** - ecosystem-specific areas labelled with the ecosystem and whether the
action is PROTECT (it is present and functioning) or RESTORE (it belongs here and is degraded
or absent, judged by whether the ecosystem occurs elsewhere in the same area). Covers mangrove,
reef and shallow shelf, forest, wetland and coastal woodland.

## 6c. Indicative employment

`jobs_model.py` translates a stated hypothetical package into a job range. Every coefficient is
a published or conventional planning benchmark, given as a range, and every output is a range.

| Coefficient | Range |
|---|---|
| Jobs per hotel room | 0.4-0.8 direct |
| Food, retail and transport per room | 0.25-0.5 |
| Guiding and activities per developed natural asset | 1.5-4 |
| Ecosystem restoration | 0.15-0.45 person-years per hectare |
| Protected-area management | 0.4-1.2 posts per 1,000 ha |
| Indirect and induced multiplier | 1.7-2.4x direct |

Restoration figures derive from restoration costs of roughly US$2,500-6,000/ha in a Latin
American setting, a ~35% labour share and ~US$5,000 per person-year, expressed as FTE over a
five-year programme. The multiplier is consistent with WTTC's Panama total of about 392,000
travel and tourism jobs in 2024 against a direct share of roughly 40%.

**This is not a forecast.** It assumes finance, tenure, skills and visitor demand the screening
cannot observe, and the package itself is hypothetical.

## 6d. Two independent recommendations

Each Opportunity Area carries two parallel recommendations rather than one combined label,
because a single label conflated two different questions and made them mutually exclusive -
when the most valuable places need both.

**Tourism infrastructure** - one of *Develop new capacity*, *Upgrade and diversify*,
*Low-impact access only*, *No new development* - plus a specific, data-derived list of what to
build or upgrade: accommodation, access (road condition, or pier/landing/airstrip where access
is maritime), visitor facilities, trails and viewpoints, marine facilities, water and
sanitation, solid waste and visitor management.

**Nature** - one of *Protect*, *Restore*, *Protect and restore*, *Maintain* - with the
ecosystem-specific zones and hectares behind it.

The two are computed independently from the same evidence and can take any combination.

## 6e. Coverage of government priority destinations

Where the national threshold leaves one of the ten priority destinations with no Opportunity
Area, its own best-scoring contiguous cluster is added at a threshold relative to that
destination rather than to the country. These are flagged `selected_by = "government priority
coverage"` so a reader can distinguish a nationally-strong area from one included for policy
coverage. Two of the forty areas were added this way.

## 7. Narratives

`55_narratives.py` composes each area's write-up from that area's own measured values. Nothing
is hard-coded per place: sentences fire conditionally on what is actually true — mangrove above
a threshold, relief above a threshold, a protection gap, comarca intersection — and numbers are
substituted from the data. Where a claim depends on an assumption, the sentence says so.

## 8. Weights are judgement

The weights above are reasoned but **not empirically calibrated**: no ground-truth dataset of
"correct" tourism–nature opportunities exists for Panama. Every weight is visible in
`pipeline/30_indicators.py` and `pipeline/40_classify.py` and can be changed and re-run in
minutes. Sensitivity testing of the weights is a phase-2 task.
