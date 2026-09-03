"""Step 16 - join protection, ecosystems, bathymetry and tourism-asset counts onto the grid.

Protection comes from Panama's own SINAP layer (MiAmbiente, 2025 edition via STRI), not WDPA:
it is the national source of record, carries the legal basis (Gaceta) for each area, and has
no redistribution restriction.
"""
import sys
from collections import Counter
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import CRS_M, PROC, arcgis_layer, log  # noqa: E402

# IUCN categories treated as "strict" protection for the gap analysis
STRICT = {"Ia", "Ib", "II", "III", "IV"}
SHALLOW_DEPTHS = {-10, -20}


def frac_cover(grid: gpd.GeoDataFrame, layer: gpd.GeoDataFrame) -> np.ndarray:
    """Fraction of each grid cell covered by the union of `layer`."""
    if len(layer) == 0:
        return np.zeros(len(grid))
    union = layer.geometry.union_all()
    inter = grid.geometry.intersection(union)
    return (inter.area / grid.geometry.area).clip(0, 1).values


def dominant(grid: gpd.GeoDataFrame, layer: gpd.GeoDataFrame, field: str) -> list:
    """Largest-area attribute value per cell."""
    j = gpd.overlay(grid[["h3", "geometry"]], layer[[field, "geometry"]],
                    how="intersection", keep_geom_type=False)
    if not len(j):
        return [None] * len(grid)
    j["a"] = j.geometry.area
    best = j.sort_values("a").groupby("h3").tail(1).set_index("h3")[field]
    return grid.h3.map(best).tolist()


def main() -> None:
    grid = gpd.read_file("data/processed/grid.geojson").to_crs(CRS_M)
    out = pd.DataFrame({"h3": grid.h3.values})
    log(f"  grid {len(grid)} cells")

    # ---------- protected areas ----------
    pa = gpd.read_file("data/raw/stri_protected_areas.geojson").to_crs(CRS_M)
    pa["geometry"] = pa.geometry.make_valid()
    out["pa_frac"] = frac_cover(grid, pa).round(3)
    out["pa_strict_frac"] = frac_cover(grid, pa[pa.IUCN_CAT.isin(STRICT)]).round(3)
    out["pa_marine_frac"] = frac_cover(grid, pa[pa.TYPE.isin(["100% Marine", "Marine", "Land and Marine"])]).round(3)
    out["ramsar_frac"] = frac_cover(
        grid, pa[pa.CAT_MANEJO.str.contains("Humedal de Importancia", na=False)]).round(3)
    out["pa_name"] = dominant(grid, pa, "NOMBRE")
    out["pa_category"] = dominant(grid, pa, "CAT_MANEJO")
    log(f"  protection: mean cover {out.pa_frac.mean():.3f}; "
        f"cells >50% protected {int((out.pa_frac>0.5).sum())}")

    # ---------- ecoregions / life zones / watersheds ----------
    eco = gpd.read_file("data/raw/stri_ecoregions.geojson").to_crs(CRS_M)
    eco["geometry"] = eco.geometry.make_valid()
    out["ecoregion"] = dominant(grid, eco, "eco_name")

    lz = gpd.read_file("data/raw/stri_lifezones.geojson").to_crs(CRS_M)
    lz["geometry"] = lz.geometry.make_valid()
    out["lifezone"] = dominant(grid, lz, "LEGEND_EN")

    ws = gpd.read_file("data/raw/stri_watersheds.geojson").to_crs(CRS_M)
    ws["geometry"] = ws.geometry.make_valid()
    out["watershed"] = dominant(grid, ws, "Nom_Cuen_Hidro")
    log(f"  ecoregions {out.ecoregion.nunique()} distinct, "
        f"life zones {out.lifezone.nunique()}, watersheds {out.watershed.nunique()}")

    # ---------- bathymetry: shallow shelf = reef/seagrass-capable habitat ----------
    bath = arcgis_layer("Bathymetry_of_the_Republic_of_Panama", cache="stri_bathymetry").to_crs(CRS_M)
    bath["geometry"] = bath.geometry.make_valid()
    shallow = bath[bath.BATIMETRIA.isin(SHALLOW_DEPTHS)]
    out["shallow_frac"] = frac_cover(grid, shallow).round(3)
    log(f"  shallow shelf (<=20 m): cells with any {int((out.shallow_frac>0).sum())}")

    # ---------- distance to coast ----------
    land = gpd.read_file("data/processed/panama_land.geojson").to_crs(CRS_M)
    coast = land.geometry.union_all().boundary
    out["dist_coast_km"] = (grid.geometry.centroid.distance(coast) / 1000).round(2)
    out.loc[grid.zone.values == "inland", "dist_coast_km"] *= 1  # sign not needed at screening scale

    # ---------- tourism assets from OSM ----------
    pois = gpd.read_file("data/processed/osm_pois.geojson").to_crs(CRS_M)
    trails = gpd.read_file("data/processed/osm_trails.geojson").to_crs(CRS_M)
    trails["theme"] = "trail"
    allp = pd.concat([pois, trails], ignore_index=True)
    allp = gpd.GeoDataFrame(allp, geometry="geometry", crs=CRS_M)

    j = gpd.sjoin(allp, grid[["h3", "geometry"]], how="inner", predicate="within")
    counts = j.groupby(["h3", "theme"]).size().unstack(fill_value=0)
    counts.columns = [f"n_{c}" for c in counts.columns]
    out = out.merge(counts.reset_index(), on="h3", how="left")
    for c in [c for c in out.columns if c.startswith("n_")]:
        out[c] = out[c].fillna(0).astype(int)
    log(f"  OSM assets joined: {len(j)} of {len(allp)} fell inside the grid")
    log("  totals: " + ", ".join(f"{c[2:]}={out[c].sum()}"
                                 for c in sorted(out.columns) if c.startswith("n_")))

    out.to_csv(PROC / "grid_vectors.csv", index=False)
    log(f"  wrote grid_vectors.csv ({out.shape[0]} rows, {out.shape[1]} cols)")


if __name__ == "__main__":
    main()
