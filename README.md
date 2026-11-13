# Panama Tourism–Nature Opportunity Scan

A working prototype that adapts the World Bank **Nature-Based Solutions Opportunity Scan
(NBSOS)** to tourism investment planning, piloted on Panama.

> **Where in Panama could tourism investment, nature conservation/restoration, climate
> resilience, biodiversity and local job creation reinforce each other?**

The NBSOS asks where nature can reduce a *specified hazard*. Tourism poses a different
question, so this prototype keeps the NBSOS intervention hierarchy — protect functioning
ecosystems before restoring, restore before building new — but replaces the hazard-and-benefit
spine with a six-family evidence structure and a rule-based recommendation typology.

**Status:** exploratory prototype for internal discussion. Findings are analytical candidates
requiring ecological, social, legal and stakeholder assessment. Nothing here is a
protected-area designation recommendation or a jobs forecast.

---

## What it produces

- A national screening grid: **3,417 H3 resolution-6 hexagons** (~37 km²) covering Panama's
  land area plus a 30 km coastal band measured from *every* coastline, so island
  archipelagos get genuine marine cells.
- Six named indicator families per cell — nature attraction, tourism development,
  accessibility, biodiversity value, resilience function, local opportunity — each built from
  named, inspectable sub-indicators. **No single opaque composite index.**
- Four recommendation types per cell, as continuous fit scores: **Protect / Restore**,
  **Invest / Develop**, **Adapt / Strengthen**, **Manage / Avoid**.
- **Named Opportunity Areas**, each reporting two things separately:
  - **tourism investment sites** — specific locations anchored on a named natural feature,
    with road access and a settlement within reach, outside strict protection cores;
  - **nature action zones** — ecosystem-specific areas labelled protect or restore, with
    hectares.
- An **indicative employment range** per area from published planning benchmarks, stated as a
  range for a hypothetical package and explicitly not a forecast.
- **Development feasibility gates**: no recommendation to develop where there is no road access
  within 10 km, where travel exceeds 8 hours from a gateway, or inside the Darien Gap advisory
  zone.
- An explicit statement, for every area, of how it relates to the government's own plan:
  **reinforces**, **refines**, **partly overlaps**, or **outside** the priority destinations.

### The government plan is an input, not a boundary

The analysis runs across all of Panama. The ATP priority destinations are overlaid on the
results afterwards. Only ~19% of the screening grid falls inside a priority destination, so
opportunities can and do surface both inside and outside declared policy geography. That
comparison is a deliverable, not a filter.

---

## Repository layout

```
pipeline/        numbered, reproducible analysis steps (Python)
  common.py              shared helpers, caching, ArcGIS/Overpass clients
  10_fetch_national.py   official MiAmbiente/IGNTG layers via the STRI GIS Portal
  11_fetch_osm.py        tourism, nature and transport features via Overpass
  12_gov_strategy.py     ATP master plan encoded as data + derived destination polygons
  gov_strategy_source.py the structured encoding of the plan itself
  20_grid.py             H3 grid over land + tourism-relevant coastal water
  17_feasibility.py      road access, remoteness and Darien Gap advisory screens
  13_rasters.py          WorldCover / Copernicus DEM / WorldPop zonal statistics
  14_gbif.py             vertebrate species richness and recording effort
  15_access.py           500 m least-cost travel-time surface
  16_vectors.py          protection, ecosystems, bathymetry, tourism-asset joins
  30_indicators.py       six indicator families
  40_classify.py         recommendation typology
  50_opportunities.py    clustering into named Opportunity Areas
  52_zones.py            tourism investment sites + nature protect/restore zones
  jobs_model.py          indicative employment benchmarks
  55_narratives.py       investment narrative generation
  60_export.py           compact web-ready artefacts
data/raw/        download cache (git-ignored, fully reproducible)
data/processed/  intermediates (git-ignored)
data/outputs/    committed analytical results (CSV)
web/             Vite + React + MapLibre GL application
docs/            methodology, data sources, limitations
```

## Reproducing the analysis

Needs Python 3.11 or newer. No system GDAL, GEOS or PROJ install is required — those ship
inside the `geopandas` and `rasterio` wheels.

```bash
make setup          # creates .venv and installs requirements.txt
make all            # fetch + analyse, start to finish
```

Or without `make`:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python pipeline/10_fetch_national.py      # ...and so on, in the order below
```

If you already have an environment you would rather use, point `make` at it:

```bash
make all PY=python3
```

### Order and runtime

Steps are numbered in dependency order. `make fetch` runs the `1x` fetchers; `make analyse`
runs the rest. A cold run takes roughly 1–1.5 hours, almost all of it network-bound in
`11_fetch_osm.py` (Overpass, rate-limited) and `14_gbif.py` (~1,100 GBIF queries, cached per
cell so interruptions resume). `20_grid.py` is the slowest compute step at around 20 minutes.
Everything is cached in `data/raw/`, so re-runs are minutes, not hours.

The pipeline downloads roughly 600 MB into `data/raw/` and writes about 10 MB of derived
outputs. No large raster is written to disk: WorldCover and Copernicus DEM are read remotely as
cloud-optimised GeoTIFFs at decimated resolution, and only per-hexagon aggregates are kept.

### What each step does

| Step | Does |
|---|---|
| `10_fetch_national.py` | MiAmbiente/STRI national layers: protected areas, watersheds, admin, places |
| `11_fetch_osm.py` | OSM tourism, nature and road features via Overpass |
| `12_gov_strategy.py` | ATP master plan destinations → mappable polygons |
| `20_grid.py` | H3 res-6 grid over land + 30 km coastal band |
| `13_rasters.py` | WorldCover land cover, Copernicus DEM, WorldPop → zonal stats |
| `14_gbif.py` | Species and threatened-species richness from GBIF |
| `15_access.py` | Least-cost travel-time surface from tourism gateways |
| `16_vectors.py` | Protected areas, ecoregions, POI density joined to the grid |
| `17_feasibility.py` | Road/sea/air access, remoteness, Darién Gap advisory screens |
| `18_flood.py` | WRI Aqueduct flood hazard + exposed population |
| `19_nbs.py` | Mangrove and reef wave attenuation over exposed population |
| `30_indicators.py` | The six indicator families |
| `40_classify.py` | Qualification gates and action classification |
| `50_opportunities.py` | Clustering into named Opportunity Areas |
| `52_zones.py` | Tourism investment sites and nature protect/restore zones |
| `55_narratives.py` | Investment narratives and employment estimates |
| `60_export.py` | Web-ready outputs into `web/public/data/` |

Supporting modules (not steps): `common.py` (shared I/O and CRS helpers),
`gov_strategy_source.py` (the encoded master plan), `jobs_model.py` (employment benchmarks),
`recommendations.py` (the two recommendation axes).

## Running the application

```bash
cd web
npm install
npm run dev
```

The site is a static build. Deployment to GitHub Pages runs from
`.github/workflows/deploy.yml`; set **Settings → Pages → Source** to **GitHub Actions**.

### Access gate

The application is behind a shared access key. This is an **access gate, not security**: the
site is a static build of open data and anyone with the bundle can read past it. It exists to
keep an unfinished internal prototype out of casual circulation.

---

## Documentation

- [`docs/methodology.md`](docs/methodology.md) — indicator construction, weights, classification rules
- [`docs/data-sources.md`](docs/data-sources.md) — every source, access date, licence, redistribution terms
- [`docs/limitations.md`](docs/limitations.md) — what the analysis cannot tell you

## Designed for phase 2

The grid and pipeline are structured so that the World Bank's ~90 m flood hazard layers can be
added as one further zonal-statistics stage, converting the screening resilience proxy into an
exposure-weighted estimate, without redesigning the product.
