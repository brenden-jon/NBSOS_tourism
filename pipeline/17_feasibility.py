"""Step 17 - development feasibility screens.

The first version of this analysis recommended tourism development on cells with a nature
attraction score of 0, no population, no roads and a modelled 17-hour journey from the
nearest gateway - deep inside the Darien Gap. That is not a marginal error, it is a
category error: those places are not candidates for tourism investment on any timescale
this tool should be talking about.

Three screens are computed here and applied as HARD GATES on development recommendations
in step 40, rather than as soft score penalties:

  access_km         distance to the nearest ACCESS POINT - a road, or a marina, ferry
                    terminal or airstrip. Panama's tourism is substantially island-based
                    (Bocas del Toro, Las Perlas, Guna Yala, the Golfo de Chiriqui
                    archipelagos), and an earlier version of this screen used road distance
                    alone. That excluded 131 high-attraction coastal and island cells -
                    including Bocas del Toro nearshore, three hours from a gateway - purely
                    because islands do not have roads to them. Boats and airstrips are how
                    those destinations are reached, and they count.
  remoteness        modelled travel time to the nearest tourism gateway
  advisory_zone     the Darien Gap border region

ON THE ADVISORY ZONE
  The Darien Gap - the roadless forest along Panama's border with Colombia - carries
  standing "do not travel" advisories from most governments and is an active irregular
  migration corridor. No open dataset encodes this, so it is defined here explicitly and
  transparently: land within 40 km of the Colombian border that has no road access. It is
  a documented analytical exclusion, not a measurement, and it is labelled as such
  wherever it appears. It suppresses tourism-development recommendations only; the
  conservation value of the Darien is unaffected and still scored.
"""
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).parent))
from common import CRS_M, PROC, RAW, UA, log  # noqa: E402

COL_ADM0 = ("https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/"
            "COL/ADM0/geoBoundaries-COL-ADM0_simplified.geojson")

ROAD_CLASSES = ["motorway", "trunk", "primary", "secondary", "tertiary",
                "unclassified", "motorway_link", "trunk_link", "primary_link", "secondary_link"]

BORDER_BUFFER_KM = 40
MAX_ACCESS_KM = 15      # a road, pier or airstrip within this counts as reachable
MAX_GATEWAY_H = 8


def main() -> None:
    grid = gpd.read_file("data/processed/grid.geojson").to_crs(CRS_M)
    cent = grid.geometry.centroid
    out = pd.DataFrame({"h3": grid.h3.values})
    log(f"  {len(grid)} cells")

    # ---- distance to the nearest usable road ----
    roads = gpd.read_file("data/processed/osm_roads.geojson").to_crs(CRS_M)
    roads = roads[roads.highway.isin(ROAD_CLASSES)]
    road_union = roads.geometry.union_all()
    out["dist_road_km"] = (cent.distance(road_union) / 1000).round(2).values
    log(f"  road distance: median {out.dist_road_km.median():.1f} km, "
        f"cells >10 km from a road: {int((out.dist_road_km > 10).sum())}")

    # ---- distance to the nearest maritime or air access point ----
    pois = gpd.read_file("data/processed/osm_pois.geojson").to_crs(CRS_M)
    access_pts = pois[pois.theme.isin(["marina_port", "airport"])]
    if len(access_pts):
        ap_union = access_pts.geometry.union_all()
        out["dist_port_air_km"] = (cent.distance(ap_union) / 1000).round(2).values
    else:
        out["dist_port_air_km"] = 9999.0
    out["dist_access_km"] = out[["dist_road_km", "dist_port_air_km"]].min(axis=1).round(2)
    out["access_mode"] = np.where(out.dist_road_km <= out.dist_port_air_km,
                                  "road", "boat or air")
    log(f"  access distance: median {out.dist_access_km.median():.1f} km; "
        f"cells reachable within {MAX_ACCESS_KM} km: "
        f"{int((out.dist_access_km <= MAX_ACCESS_KM).sum())}")
    log(f"  cells whose nearest access is maritime/air: "
        f"{int((out.access_mode == 'boat or air').sum())}")

    # ---- distance to the nearest settlement ----
    places = gpd.read_file("data/raw/stri_places.geojson").to_crs(CRS_M)
    place_union = places.geometry.union_all()
    out["dist_settlement_km"] = (cent.distance(place_union) / 1000).round(2).values

    # ---- Darien Gap advisory zone ----
    cpath = RAW / "colombia_adm0.geojson"
    if not cpath.exists():
        log("  downloading Colombia boundary (geoBoundaries, one-off)...")
        r = requests.get(COL_ADM0, headers=UA, timeout=300)
        r.raise_for_status()
        cpath.write_bytes(r.content)
    col = gpd.read_file(cpath).to_crs(CRS_M)
    col_geom = col.geometry.union_all()
    out["dist_colombia_km"] = (cent.distance(col_geom) / 1000).round(2).values

    near_border = out.dist_colombia_km < BORDER_BUFFER_KM
    roadless = out.dist_road_km > 10
    out["advisory_zone"] = (near_border & roadless).astype(int)
    log(f"  within {BORDER_BUFFER_KM} km of Colombia: {int(near_border.sum())} cells; "
        f"of those roadless: {int(out.advisory_zone.sum())} flagged as advisory zone")

    # ---- composite development feasibility ----
    # Not a score to be traded off - a gate. A place either can carry visitor
    # infrastructure at screening scale or it cannot.
    tt = pd.read_csv(PROC / "grid_access.csv").set_index("h3").tt_gateway_h
    out["tt_gateway_h"] = out.h3.map(tt).values
    out["dev_feasible"] = (
        (out.dist_access_km <= MAX_ACCESS_KM)
        & (out.tt_gateway_h <= MAX_GATEWAY_H)
        & (out.advisory_zone == 0)
    ).astype(int)
    reasons = pd.Series("feasible", index=out.index)
    reasons[out.dist_access_km > MAX_ACCESS_KM] = (
        f"no road, pier or airstrip within {MAX_ACCESS_KM} km")
    reasons[out.tt_gateway_h > MAX_GATEWAY_H] = (
        f"over {MAX_GATEWAY_H} h from the nearest tourism gateway")
    reasons[out.advisory_zone == 1] = "Darien Gap border region (standing travel advisories)"
    out["infeasible_reason"] = np.where(out.dev_feasible == 1, None, reasons)

    log(f"  development-feasible cells: {int(out.dev_feasible.sum())} of {len(out)} "
        f"({100*out.dev_feasible.mean():.1f}%)")
    log("  infeasible by reason: " +
        str(out.loc[out.dev_feasible == 0, "infeasible_reason"].value_counts().to_dict()))

    out.drop(columns=["tt_gateway_h"]).to_csv(PROC / "grid_feasibility.csv", index=False)
    log(f"  wrote grid_feasibility.csv ({len(out)} rows)")


if __name__ == "__main__":
    main()
