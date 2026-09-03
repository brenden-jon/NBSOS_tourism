"""Step 15 - accessibility as modelled travel time, not straight-line distance.

Builds a 500 m friction surface over Panama and runs a multi-source least-cost accumulation
(scikit-image MCP_Geometric) from tourism gateways. Straight-line distance would badly
misrepresent Panama, where the Darien has no roads, the Caribbean coast east of Portobelo is
boat-access only, and island destinations depend on ports and airstrips.

ASSUMPTIONS (documented in docs/methodology.md)
  - road speeds by OSM highway class, halved where surface is unpaved
  - off-road land speed 4.5 km/h in open country falling to 1.5 km/h under dense tree cover,
    further reduced by terrain relief
  - sea is traversable at 20 km/h, standing in for boat access; this is a simplification -
    real island access depends on scheduled services from specific ports
  - travel time is *modelled*, not observed, and ignores traffic, ferry timetables and border
    formalities
"""
import sys
import warnings
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_origin
from skimage.graph import MCP_Geometric

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent))
from common import CRS_M, CRS_WGS, PROC, log  # noqa: E402

PIX = 500  # metres

ROAD_SPEED = {  # km/h
    "motorway": 90, "motorway_link": 60, "trunk": 75, "trunk_link": 50,
    "primary": 60, "primary_link": 45, "secondary": 50, "secondary_link": 40,
    "tertiary": 40, "unclassified": 25,
}

# Major tourism gateways (documented, not name-matched from OSM).
GATEWAYS = {
    "Tocumen International (PTY)": (-79.3835, 9.0714),
    "Albrook / Marcos A. Gelabert (PAC)": (-79.5556, 8.9733),
    "Panama Pacifico (BLB)": (-79.5997, 8.9147),
    "Enrique Malek, David (DAV)": (-82.4350, 8.3910),
    "Bocas del Toro, Isla Colon (BOC)": (-82.2508, 9.3408),
    "Scarlett Martinez, Rio Hato (RIH)": (-80.1281, 8.3757),
    "Enrique A. Jimenez, Colon (ONX)": (-79.8674, 9.3568),
}
CAPITAL = (-79.5199, 8.9824)  # Panama City centre


def build_friction(grid: gpd.GeoDataFrame, roads: gpd.GeoDataFrame,
                   rasters: pd.DataFrame) -> tuple[np.ndarray, object, tuple]:
    minx, miny, maxx, maxy = grid.total_bounds
    pad = 10_000
    minx, miny, maxx, maxy = minx - pad, miny - pad, maxx + pad, maxy + pad
    w = int((maxx - minx) / PIX)
    h = int((maxy - miny) / PIX)
    tr = from_origin(minx, maxy, PIX, PIX)
    log(f"  friction raster {h} x {w} at {PIX} m")

    # --- baseline: sea ---
    speed = np.full((h, w), 20.0, dtype="float32")

    # --- land: off-road speed modulated by tree cover and relief ---
    gg = grid.merge(rasters[["h3", "lc_tree", "relief_m"]], on="h3", how="left")
    gg["lc_tree"] = gg["lc_tree"].fillna(0.0)
    gg["relief_m"] = gg["relief_m"].fillna(0.0)
    gg["offroad"] = (4.5 - 3.0 * gg["lc_tree"]) * (1.0 - 0.4 * np.clip(gg["relief_m"] / 1500, 0, 1))
    gg["offroad"] = gg["offroad"].clip(0.8, 4.5)
    land = gg[gg.land_frac > 0.02]
    land_speed = rasterize([(g, v) for g, v in zip(land.geometry, land.offroad)],
                           out_shape=(h, w), transform=tr, fill=0, dtype="float32")
    speed = np.where(land_speed > 0, land_speed, speed)

    # --- roads burn over everything ---
    rs = roads.copy()
    rs["kmh"] = rs["highway"].map(ROAD_SPEED).fillna(20.0).astype("float64")
    unpaved = rs["surface"].isin(["unpaved", "gravel", "dirt", "ground", "earth", "sand", "grass"])
    rs.loc[unpaved, "kmh"] = rs.loc[unpaved, "kmh"] * 0.5
    rs = rs.sort_values("kmh")  # faster roads rasterised last so they win
    road_speed = rasterize([(g, v) for g, v in zip(rs.geometry, rs.kmh)],
                           out_shape=(h, w), transform=tr, fill=0, dtype="float32",
                           all_touched=True)
    speed = np.where(road_speed > 0, np.maximum(road_speed, speed), speed)

    # cost = hours to cross one pixel
    cost = (PIX / 1000.0) / speed
    return cost.astype("float64"), tr, (h, w)


def accumulate(cost: np.ndarray, tr, shape, origins_xy: list[tuple[float, float]]) -> np.ndarray:
    h, w = shape
    starts = []
    for x, y in origins_xy:
        col = int((x - tr.c) / PIX)
        row = int((tr.f - y) / PIX)
        if 0 <= row < h and 0 <= col < w:
            starts.append((row, col))
    if not starts:
        raise ValueError("no origins inside raster")
    mcp = MCP_Geometric(cost, fully_connected=True)
    acc, _ = mcp.find_costs(starts)
    return acc


def sample(acc: np.ndarray, tr, shape, pts: gpd.GeoSeries) -> np.ndarray:
    h, w = shape
    cols = ((pts.x - tr.c) / PIX).astype(int).clip(0, w - 1)
    rows = ((tr.f - pts.y) / PIX).astype(int).clip(0, h - 1)
    v = acc[rows, cols]
    return np.where(np.isfinite(v), v, np.nan)


def main() -> None:
    grid = gpd.read_file("data/processed/grid.geojson").to_crs(CRS_M)
    roads = gpd.read_file("data/processed/osm_roads.geojson").to_crs(CRS_M)
    rasters = pd.read_csv(PROC / "grid_rasters.csv")
    log(f"  {len(grid)} cells, {len(roads)} road ways")

    cost, tr, shape = build_friction(grid, roads, rasters)

    gw = gpd.GeoSeries(gpd.points_from_xy([v[0] for v in GATEWAYS.values()],
                                          [v[1] for v in GATEWAYS.values()]),
                       crs=CRS_WGS).to_crs(CRS_M)
    cap = gpd.GeoSeries(gpd.points_from_xy([CAPITAL[0]], [CAPITAL[1]]),
                        crs=CRS_WGS).to_crs(CRS_M)

    cent = grid.geometry.centroid

    log("  accumulating from tourism gateways...")
    acc_gw = accumulate(cost, tr, shape, list(zip(gw.x, gw.y)))
    log("  accumulating from Panama City...")
    acc_cap = accumulate(cost, tr, shape, list(zip(cap.x, cap.y)))

    out = pd.DataFrame({
        "h3": grid.h3.values,
        "tt_gateway_h": np.round(sample(acc_gw, tr, shape, cent), 2),
        "tt_capital_h": np.round(sample(acc_cap, tr, shape, cent), 2),
    })
    log(f"  travel time to nearest gateway: median {out.tt_gateway_h.median():.2f} h, "
        f"max {out.tt_gateway_h.max():.1f} h")
    log(f"  travel time to Panama City:     median {out.tt_capital_h.median():.2f} h, "
        f"max {out.tt_capital_h.max():.1f} h")

    # sanity: known destinations should land in sensible bands
    g2 = grid.merge(out, on="h3")
    for name in ["Bocas del Toro", "Boquete", "Pedasí", "Colón", "Chepigana"]:
        sub = g2[g2.district == name]
        if len(sub):
            log(f"    {name:16s} median gateway time {sub.tt_gateway_h.median():.2f} h")

    out.to_csv(PROC / "grid_access.csv", index=False)
    log(f"  wrote grid_access.csv ({len(out)} rows)")


if __name__ == "__main__":
    main()
