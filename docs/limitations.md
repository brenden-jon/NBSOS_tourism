# Limitations

This prototype is designed to be *decision-useful*, not authoritative. The list below is
deliberately blunt: a screening tool that overstates its own confidence is worse than no tool.

## What this is not

- **Not a flood-risk model.** The resilience family (RES) is a spatial coincidence measure —
  protective ecosystems in front of low-lying people and assets, or catchment tree cover on
  slopes above them. No hydrodynamic or probabilistic modelling has been undertaken and **no
  avoided damages are estimated**. RES flags where such analysis would be worth doing.
- **Not a tourism master plan, feasibility study or ecological assessment.**
- **Not a protected-area designation recommendation.** Areas classified *Protect / Restore* —
  including any implied new or extended marine protection — are analytical candidates for
  further ecological, social, legal and stakeholder assessment.
- **Not a jobs forecast.** No employment numbers are estimated anywhere.

## Data limitations

**OpenStreetMap measures mapping effort, not tourism.** Accommodation and service counts are
used as a proxy for existing tourism development, but OSM coverage is best where visitors
already go. A low count partly reflects genuinely low development and partly reflects low
mapping effort. Where an Opportunity Area shows zero mapped accommodation, that is a
ground-truthing task, not a finding.

**GBIF measures recording, not biodiversity.** Occurrence density is heavily biased toward
research stations (Barro Colorado above all), roadsides and established birding sites. Richness
is used only as a weak positive signal; record density is used separately as a proxy for
existing wildlife-watching interest. Neither is a survey. Richness is additionally capped at
1,000 species per vertebrate class per resolution-5 cell by the GBIF faceting API.

**Reef habitat is proxied, not mapped.** Without a redistributable reef dataset, reef-capable
habitat is inferred from bathymetric shelf depth under 20 m, OSM-mapped reefs and marine
protected-area designation. **Reef condition is entirely unobserved** — no bleaching, turbidity
or cover data enters the analysis.

**Travel time is modelled, not observed.** The friction surface ignores traffic, ferry
timetables and frequencies, seasonal road closures and border formalities. Sea travel is a
uniform 20 km/h standing in for boat access, which makes **island accessibility optimistic**:
in reality it depends on scheduled services from specific ports.

**Population is an estimate.** WorldPop constrained totals run ~6% below census figures here.

**Elevation is a surface model.** Copernicus GLO-30 includes canopy and structures.

## Method limitations

**Screening scale is 37 km².** A single hexagon can contain a resort strip and intact forest.
Every conclusion is about an *area*, not a site. Nothing here substitutes for site-level
assessment.

**Weights are analytical judgement.** The weights combining sub-indicators into families, and
families into fit scores, are reasoned but not empirically calibrated — no ground-truth dataset
of "correct" tourism–nature opportunities exists for Panama. They are visible in
`pipeline/30_indicators.py` and `pipeline/40_classify.py`. Sensitivity testing is a phase-2 task.

**Percentile ranking is relative.** All scores are positions within Panama. A cell scoring 90
for nature attraction is in the top decile *for Panama*, not on an absolute international scale.

**Government destination boundaries are derived.** The master plan names destinations but
publishes no boundaries. Polygons here are the smallest sets of official district units
containing the named places, and are coarser than the destinations as ATP understands them. The
share of an area falling "inside" a destination is therefore approximate.

**Cluster boundaries follow hexagons.** Opportunity Area outlines are unions of 37 km² cells,
not ecological or administrative boundaries. They indicate where to look, not where to draw a line.

## Interpretation guidance

Distinguish carefully between the four kinds of statement this prototype makes:

| Kind | Example | Confidence |
|---|---|---|
| **Observed data** | "91 protected areas covering X% of this area" | High — from the national register |
| **Derived indicator** | "Nature attraction 72/100" | Moderate — depends on weights and proxies |
| **Government policy** | "Inside the priority destination Bocas del Toro" | High — from the published plan |
| **Analytical judgement** | "Protect / Restore, with a protection gap of 61" | Indicative — a hypothesis to test |
| **Recommendation** | "Assess the case for extended marine protection" | A proposal for further work, never a decision |

The application labels these distinctions throughout. Please preserve them when quoting results.
