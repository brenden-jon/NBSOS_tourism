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

H3 resolution-6 hexagons, mean area ~37 km². **4,434 cells** cover:

- all of Panama's land area (74,274 km² as measured from the official province layer, against a
  reference figure of ~75,420 km²), plus
- a **30 km coastal band measured from every coastline**, island coastlines included.

The band is computed by buffering the dissolved national land polygon and subtracting it, so
Bocas del Toro, Guna Yala, Las Perlas, Coiba, Taboga and the Islas Secas all generate genuine
marine cells rather than being clipped at the shore.

Cells are typed by land fraction: `inland` (≥98% land), `coastal` (2–98%), `nearshore` (marine
but within 5 km of land), `marine`. Panama's very large offshore MPAs — Banco Volcán
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
| **BCV** Biodiversity value | Conservation significance | species richness, forest, ecoregion and life-zone rarity, protection cover, mangrove, Ramsar |
| **RES** Resilience function | Screening-level protective role of nature | coastal: protective ecosystems × low-lying exposure in a two-ring neighbourhood; inland: upper-catchment tree cover × downstream assets in the same watershed |
| **JOBS** Local opportunity | Capacity to capture value locally | local labour pool, decentralisation distance, comarca context, accessibility |

**RES is not a hazard model.** It is a spatial coincidence measure: protective ecosystems in
front of low-lying people and assets, or catchment tree cover on slopes above them. No
hydrodynamic or probabilistic modelling has been done and no avoided damages are estimated.

## 5. Classification

Four action types, each scored continuously so that a place can be several things at once.

```
fit_invest  = (0.34·NAV + 0.22·ACC + 0.24·(100−TDL) + 0.20·JOBS) × damp
fit_protect =  0.42·BCV + 0.26·(100−strict protection) + 0.20·max(NAV,RES) + 0.12·JOBS
fit_adapt   =  0.38·TDL + 0.30·RES + 0.20·BCV + 0.12·ACC
fit_manage  =  0.45·BCV + 0.25·(any protection) + 0.30·pressure
```

where

```
sensitivity = 0.6·BCV + 0.4·strict protection
damp        = 1 − 0.5·clip((sensitivity − 70)/30, 0, 1)
pressure    = clip((BCV−60)/40, 0, 1) × clip((ACC−40)/60, 0, 1)
```

The strongest fit becomes the **primary** recommendation; any other action scoring ≥55 is kept
as a **secondary** recommendation. That matters: the most interesting places in Panama are
exactly those where "protect the reef" and "develop the snorkelling access" are the same
recommendation.

`damp` is the deliberate asymmetry that stops the tool recommending construction in every
accessible beautiful place.

Two derived diagnostics are also carried:

- `protection_gap = max(NAV, RES) × (1 − strict protection)` — value not currently held by strict protection
- `supply_gap = max(NAV − TDL, 0)` — attraction that existing supply does not yet serve

## 6. Opportunity Areas

Within each action class, cells above the 80th percentile of that class's fit score are
retained, joined into connected components over H3 adjacency, and kept where the component has
≥3 cells (~110 km²). Each area is named from the protected area covering it, else the largest
settlement or most prominent named feature inside it, else the dominant district.

Areas are ranked by `fit × log(1 + cells)`, so a strong small cluster does not outrank a strong
large one.

Each area is tagged against the government plan by the share of its cells falling inside a
priority destination: **reinforces** (≥50% and a development recommendation), **refines** (≥50%
with a conservation, resilience or pressure recommendation), **partial** (>15%), **new** (≤15%).

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
