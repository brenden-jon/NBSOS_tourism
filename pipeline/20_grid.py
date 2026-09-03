"""Step 20 - build the national analysis grid.

Unit of analysis: H3 resolution 6 hexagons (~37 km2). Coverage is all land plus a 30 km
coastal band measured from EVERY coastline, including island coastlines, so that
archipelago destinations (Bocas del Toro, Las Perlas, Guna Yala, Coiba, Taboga, Islas
Secas) get proper marine cells rather than being clipped to their shorelines.

Large offshore MPAs (Banco Volcan, Cordillera de Coiba) extend far beyond this band; they
are carried as context layers, not as scored cells, because tourism relevance there is nil.
"""
import sys
from pathlib import Path

import geopandas as gpd
import h3
import pandas as pd
from shapely.geometry import Polygon
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).parent))
from common import CRS_M, CRS_WGS, arcgis_layer, log, save_geojson  # noqa: E402

H3_RES = 6
COAST_KM = 30          # outer limit of the marine search band
NEARSHORE_KM = 10      # water routinely used by coastal and island tourism


def cell_polygon(cell: str) -> Polygon:
    # h3 returns (lat, lng); shapely wants (lng, lat)
    return Polygon([(lng, lat) for lat, lng in h3.cell_to_boundary(cell)])


def main() -> None:
    land = gpd.read_file("data/processed/panama_land.geojson").to_crs(CRS_M)
    land_geom = land.geometry.union_all()
    log(f"  land area {land_geom.area/1e6:,.0f} km2")

    # Simplify only for the buffering step - the unsimplified geometry stays the mask.
    simp = land_geom.simplify(150)
    band = simp.buffer(COAST_KM * 1000).difference(simp)
    log(f"  {COAST_KM} km coastal band: {band.area/1e6:,.0f} km2")

    aoi_m = unary_union([land_geom, band])
    aoi_wgs = gpd.GeoSeries([aoi_m], crs=CRS_M).to_crs(CRS_WGS).iloc[0]

    cells = h3.geo_to_cells(aoi_wgs, H3_RES)
    log(f"  H3 res-{H3_RES} cells covering AOI: {len(cells)}")

    g = gpd.GeoDataFrame(
        {"h3": list(cells)},
        geometry=[cell_polygon(c) for c in cells],
        crs=CRS_WGS,
    ).to_crs(CRS_M)

    # land fraction per cell drives the land / coastal / marine split
    inter = g.geometry.intersection(land_geom)
    g["area_km2"] = (g.geometry.area / 1e6).round(2)
    g["land_km2"] = (inter.area / 1e6).round(3)
    g["land_frac"] = (g["land_km2"] / g["area_km2"]).clip(0, 1).round(3)

    g["dist_land_m"] = g.geometry.distance(land_geom)
    g["zone"] = "marine"
    g.loc[g.land_frac >= 0.98, "zone"] = "inland"
    g.loc[(g.land_frac > 0.02) & (g.land_frac < 0.98), "zone"] = "coastal"
    g.loc[(g.zone == "marine") & (g.dist_land_m < NEARSHORE_KM * 1000), "zone"] = "nearshore"

    # ---- keep only tourism-relevant water -------------------------------------------
    # The 30 km band is a search extent, not an analysis extent. Open ocean beyond the
    # shelf carries no tourism-nature opportunity: scored, it produces ~1,300 near-empty
    # cells that drag every coastal aggregate down and clutter the map. We therefore
    # retain marine cells only where they are nearshore, sit over mapped shallow shelf
    # (<20 m), or fall inside a marine protected area. Panama's large offshore MPAs and
    # the full protected-area layer remain available as context layers regardless.
    bath = arcgis_layer("Bathymetry_of_the_Republic_of_Panama", cache="stri_bathymetry").to_crs(CRS_M)
    bath["geometry"] = bath.geometry.make_valid()
    shelf = bath[bath.BATIMETRIA.isin([-10, -20])].geometry.union_all()
    pa = gpd.read_file("data/raw/stri_protected_areas.geojson").to_crs(CRS_M)
    pa["geometry"] = pa.geometry.make_valid()
    mpa = pa[pa.TYPE.isin(["100% Marine", "Marine", "Land and Marine"])].geometry.union_all()

    far = g.zone == "marine"
    keep_shelf = g.geometry.intersects(shelf)
    keep_mpa = g.geometry.intersects(mpa)
    drop = far & ~keep_shelf & ~keep_mpa
    log(f"  marine band: {int(far.sum())} open-water cells, "
        f"{int((far & keep_shelf).sum())} over shelf, {int((far & keep_mpa).sum())} in an MPA")
    before = len(g)
    g = g[~drop].copy()
    log(f"  dropped {before - len(g)} non-relevant open-ocean cells")

    # attach admin context by cell centroid (falls back to nearest for marine cells)
    dist = gpd.read_file("data/raw/stri_districts.geojson").to_crs(CRS_M)
    dist["geometry"] = dist.geometry.make_valid()
    cent = gpd.GeoDataFrame(geometry=g.geometry.centroid, crs=CRS_M)
    joined = gpd.sjoin_nearest(cent, dist[["Provincia", "Distrito", "geometry"]],
                               how="left", max_distance=60000)
    joined = joined[~joined.index.duplicated(keep="first")]
    g["province"] = joined["Provincia"].values
    g["district"] = joined["Distrito"].values

    # tag against government destinations
    dests = gpd.read_file("data/processed/gov_destinations.geojson").to_crs(CRS_M)
    g["gov_dest"] = None
    g["gov_tier"] = None
    for r in dests.itertuples():
        hit = g.geometry.intersects(r.geometry)
        # only claim a cell if a real share of it falls inside the destination
        share = g.loc[hit].geometry.intersection(r.geometry).area / g.loc[hit].geometry.area
        take = share[share > 0.25].index
        g.loc[take, "gov_dest"] = r.name
        g.loc[take, "gov_tier"] = r.tier

    log(f"  cells by zone: {g.zone.value_counts().to_dict()}")
    log(f"  cells inside a government destination: {g.gov_dest.notna().sum()} "
        f"({100*g.gov_dest.notna().mean():.1f}%)")
    log(f"  TOTAL CELLS: {len(g)}")

    g["dist_land_km"] = (g.dist_land_m / 1000).round(2)
    save_geojson(g[["h3", "area_km2", "land_km2", "land_frac", "zone", "dist_land_km",
                    "province", "district", "gov_dest", "gov_tier", "geometry"]],
                 "grid", decimals=5)


if __name__ == "__main__":
    main()
