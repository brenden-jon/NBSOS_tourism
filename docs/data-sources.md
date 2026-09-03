# Data sources, licences and redistribution

All sources accessed **2026-09-02**.

Principle applied: prefer authoritative Panamanian government data where usable, then
respected global datasets, then open and reproducible sources — and prefer lightweight data
that can be regenerated over large files committed to the repository.

## Used

| Source | Organisation | Used for | Licence | Redistribution here |
|---|---|---|---|---|
| **Panama Protected Areas (SINAP) 2025** | MiAmbiente, via STRI GIS Portal | Protection status, IUCN category, marine/terrestrial realm, establishment year, Gaceta legal basis, Ramsar sites | Open data portal | Simplified geometry published with attribution |
| **Administrative boundaries 2024** | IGNTG / INEC, via STRI GIS Portal | Provinces (incl. 4 comarcas), 82 districts, 699 corregimientos; destination polygons; comarca identification | Open data portal | Derived polygons only |
| **Panama watersheds 2022 & bathymetry** | MiAmbiente / IGNTG, via STRI GIS Portal | 52 watershed units for the inland resilience proxy; shallow-shelf extent (contours at 10/20/50/100/200/400 m) | Open data portal | Aggregates only |
| **Panama ecoregions & Holdridge life zones** | STRI GIS Portal | Ecoregion and life-zone rarity | Open data portal | Aggregates only |
| **OpenStreetMap** (Overpass API) | OSM contributors | 6,666 tourism/nature POIs, 718 named trails, 24,067 road ways | **ODbL 1.0** | Published with ODbL attribution |
| **ESA WorldCover 2021 v200** | European Space Agency | Land-cover fractions at 10 m incl. mangrove class 95 | **CC BY 4.0** | Per-hexagon aggregates only |
| **Copernicus DEM GLO-30** | ESA / Airbus | Elevation, relief, low-elevation coastal zone | Free and open, attribution | Per-hexagon aggregates only |
| **WorldPop 2020 constrained (UN-adjusted)** | WorldPop, U. Southampton | Population, labour pool, coastal exposure | **CC BY 4.0** | Per-hexagon aggregates only |
| **GBIF occurrences** | GBIF | Vertebrate species richness and recording effort | Mixed by publisher (CC0 / CC BY / CC BY-NC) | **Aggregate counts only** — no records republished |
| **PMTS 2025–2030** | Autoridad de Turismo de Panamá | Priority destinations, objectives, destination value propositions, thematic routes | Public government document | Quoted and summarised with attribution and direct link |
| **CARTO basemaps, Esri World Imagery** | CARTO / Esri, Maxar | Cartographic basemaps only | Free tiles, attribution | Not redistributed; loaded at runtime |

### Why SINAP rather than WDPA

Panama's own protected-area register is more current (2025 edition), carries the *Gaceta* legal
basis for each of its 91 areas, distinguishes marine from terrestrial realm, and has no
redistribution restriction or API token requirement. WDPA was therefore not used.

### Notes and caveats by source

- **OpenStreetMap** is volunteered. Coverage is best where visitors already go. Counts are used
  deliberately as a proxy for *existing tourism development*, never as an inventory of what exists.
- **Copernicus DEM** is a *surface* model: values include canopy and structures, so peak
  elevations run slightly high (the analysis records 3,520 m for Volcán Barú against a true
  3,475 m).
- **WorldPop** totals 4.02 million over the grid against roughly 4.3 million for 2020 — a modest
  undercount typical of constrained gridded estimates.
- **GBIF** richness is capped at 1,000 species per vertebrate class per resolution-5 cell by the
  faceting API; a small number of the richest cells hit that cap.

## Considered and deliberately not used

| Source | Reason | Phase-2 status |
|---|---|---|
| **Allen Coral Atlas** | Reproduction of the dataset is restricted without written consent from ASU. Reef-capable habitat is instead proxied from shelf depth <20 m, OSM-mapped reefs and marine protected-area designation. | High priority: reef extent **and condition** |
| **Key Biodiversity Areas / IBAs** | Access requires a data agreement that prohibits redistribution. GBIF richness, ecoregion rarity and Ramsar status stand in. | High priority under a data agreement |
| **WDPA / Protected Planet** | Requires an API token and carries redistribution conditions; SINAP is better for Panama. | Not needed |
| **World Bank ~90 m flood hazard** | Not yet supplied. | Designed for — see below |
| **Global Mangrove Watch** | WorldCover class 95 provides mangrove extent inside the same zonal-statistics pass. GMW would improve mangrove accuracy and add change over time. | Useful refinement |
| **HydroSHEDS** | The 334 MB South America basin file was avoided in favour of the national 52-watershed layer, which is authoritative for Panama and far lighter. | Not needed |
| **eBird** | Requires an API key; GBIF already carries 8.5 M Panamanian bird records. | Optional |

## Designed for the flood hazard layers

The pipeline reads rasters remotely and reduces them to per-hexagon statistics in
`13_rasters.py`. Adding the World Bank's ~90 m flood hazard maps means adding one more call to
`zonal_continuous()` and one more term to the resilience family — no redesign of the grid,
the classification or the application.

## Reproducibility

`data/raw/` is git-ignored and fully regenerable by `make fetch`. Every network call is cached
on disk, so re-runs are cheap and the analysis is deterministic given the same source vintages.
Committed outputs are limited to `data/outputs/` (CSV) and `web/public/data/` (simplified,
coordinate-rounded GeoJSON).
