# Limitations

This prototype is designed to be *decision-useful*, not authoritative. The list below is
deliberately blunt: a screening tool that overstates its own confidence is worse than no tool.

## What this is not

- **Not a flood-risk study.** Flood exposure comes from WRI Aqueduct Floods, a *global* model
  at ~1 km. It does not resolve flood defences, urban drainage or Canal Zone water
  infrastructure, so exposure is likely overstated where protection exists and understated in
  small catchments the model omits. The nature-based protection estimate applies published
  attenuation coefficients to mapped ecosystem extent — it is a screening calculation, **not a
  hydrodynamic model, and no avoided damages are estimated**.
- **Wave attenuation is not flood-depth reduction.** Mangrove and reef coefficients describe
  wave energy. Aqueduct's coastal layer is a surge-plus-depth product. The two are related but
  not equivalent, and the result should be read as "the share of wave energy existing
  ecosystems remove from what reaches these people", not as people protected from flooding.
- **Mangrove width is a proxy.** It is mangrove area divided by coastline length in the cell,
  which is wrong wherever mangrove sits in a lagoon or estuary rather than as a shore-parallel
  belt — common in the Gulf of Chiriquí and Bocas del Toro.
- **Riverine NBS benefit is not quantified at all.** Catchment forest moderates runoff, but the
  effect on peak flows at basin scale is contested. Catchments are ranked by exposure against
  forest cover; no percentage reduction in flood peak is claimed or implied.
- **Not a tourism master plan, feasibility study or ecological assessment.**
- **Not a protected-area designation recommendation.** Areas classified *Protect / Restore* —
  including any implied new or extended marine protection — are analytical candidates for
  further ecological, social, legal and stakeholder assessment.
- **Not a jobs forecast.** Employment figures are order-of-magnitude ranges for a stated
  hypothetical investment package, derived from published planning benchmarks. They assume
  finance, tenure, skills and visitor demand that this screening cannot observe. Restoration
  employment is full-time equivalents while a five-year programme runs, not permanent posts.

## Data limitations

**OpenStreetMap measures mapping effort, not tourism.** Accommodation and service counts are
used as a proxy for existing tourism development, but OSM coverage is best where visitors
already go. A low count partly reflects genuinely low development and partly reflects low
mapping effort. Where an Opportunity Area shows zero mapped accommodation, that is a
ground-truthing task, not a finding.

**Threatened-species counts inherit GBIF's biases.** A cell shows threatened species where
someone has recorded them and the species has an IUCN assessment. Unsurveyed ground reads as
zero. The counts are a floor, not a census.

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

**The Darien Gap advisory zone is a judgement, not a dataset.** It is defined here as land
within 40 km of the Colombian border with no road access. Security conditions change, the
boundary is approximate, and it should be replaced by current official advisory geography
before any use beyond screening. It suppresses development recommendations only.

**Feasibility thresholds are round numbers.** 10 km to a road and 8 hours to a gateway are
defensible screening cut-offs, not researched thresholds. A site just outside them is not
meaningfully different from one just inside.

**Tourism nodes depend on OSM naming.** A node exists only where a natural feature has been
named in OpenStreetMap. Real assets that nobody has mapped produce no node, so an area
reporting zero sites may be an OSM gap rather than a genuine absence.

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
