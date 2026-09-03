"""Step 60 - export compact, web-ready artefacts.

Everything the application loads is written here. Geometry is simplified and coordinates are
rounded so the whole payload stays a few megabytes: a screening product does not need
survey-grade vertices.
"""
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import CRS_M, PROC, WEB_DATA, log, save_geojson  # noqa: E402

# Categorical ecosystem label per cell. A single-variable ramp answers "how much forest";
# a category answers "what is this place", which is what a reader actually wants from an
# ecosystem map. Order matters: rarer, more policy-relevant systems are tested first so a
# cell with both mangrove and forest reads as mangrove.
def eco_class(r):
    if r.zone in ("marine", "nearshore") and r.shallow_frac > 0.25:
        return "Shallow shelf / reef habitat"
    if r.lc_mangrove > 0.02:
        return "Mangrove"
    if r.lc_wetland > 0.05:
        return "Wetland"
    if r.zone == "marine":
        return "Open water"
    if r.lc_tree >= 0.60:
        return "Dense forest"
    if r.lc_tree >= 0.30:
        return "Forest mosaic"
    if r.lc_built >= 0.10:
        return "Built-up"
    if r.lc_crop >= 0.25:
        return "Cropland"
    if r.lc_grass >= 0.30:
        return "Grassland & pasture"
    if r.zone == "nearshore":
        return "Coastal water"
    return "Mixed / other"


def tourism_class(tdl):
    if tdl >= 60:
        return "Established hub"
    if tdl >= 35:
        return "Developing"
    if tdl >= 12:
        return "Emerging"
    if tdl > 0:
        return "Marginal"
    return "No mapped supply"


# Split deliberately. Everything needed to DRAW the map travels with the geometry; everything
# needed only when a user clicks a cell goes into a separate lookup keyed by h3. Carrying all
# 33 fields on 3,417 polygons produced a 3.25 MB payload that took tens of seconds to tile -
# and nine of those fields were repeated strings (ecoregion, protected-area name, district).
GRID_FIELDS = [
    "h3", "zone", "primary", "dev_feasible",
    "NAV", "TDL", "ACC", "BCV", "RES", "JOBS",
    "sensitivity", "protection_gap", "supply_gap",
    "eco_class", "tourism_class",
]

DETAIL_FIELDS = [
    "district", "province", "gov_dest", "in_gov_dest", "primary_label", "secondary",
    "infeasible_reason", "dist_road_km", "advisory_zone",
    "primary_fit", "pa_name", "ecoregion", "lc_tree", "lc_mangrove", "shallow_frac",
    "pa_frac", "pa_strict_frac", "relief_m", "gbif_species", "tt_gateway_h",
    "population", "n_accommodation",
]


def main() -> None:
    grid = gpd.read_file("data/processed/grid.geojson")[["h3", "geometry"]]
    d = pd.read_csv(PROC / "grid_classified.csv")
    g = grid.merge(d, on="h3")
    g["eco_class"] = [eco_class(r) for r in g.itertuples()]
    g["tourism_class"] = [tourism_class(t) for t in g.TDL]
    log("  ecosystem classes: " + ", ".join(
        f"{k}={v}" for k, v in g.eco_class.value_counts().items()))
    log("  tourism classes: " + ", ".join(
        f"{k}={v}" for k, v in g.tourism_class.value_counts().items()))
    keep = [c for c in GRID_FIELDS if c in g.columns]
    web = g[keep + ["geometry"]].copy()
    for c in web.columns:
        if web[c].dtype == "float64":
            # every numeric kept for drawing is a 0-100 score; integers are plenty
            web[c] = web[c].round(0).astype("int32")
    # 3 decimals is ~110 m - far finer than a 37 km2 screening cell needs
    save_geojson(web, "grid", decimals=3, to_web=True)

    # per-cell detail for the click inspector, keyed by h3 and loaded separately
    det_cols = [c for c in DETAIL_FIELDS if c in g.columns]
    det = g[["h3"] + det_cols].copy()
    for c in det.columns:
        if det[c].dtype == "float64":
            det[c] = det[c].round(3) if det[c].abs().max() <= 1.5 else det[c].round(1)
    detail = {
        r["h3"]: {k: (None if pd.isna(v) else v) for k, v in r.items() if k != "h3"}
        for r in det.to_dict("records")
    }
    for path in (PROC / "grid_detail.json", WEB_DATA / "grid_detail.json"):
        path.write_text(json.dumps(detail, ensure_ascii=False, allow_nan=False,
                                   separators=(",", ":")))
    log(f"  wrote grid_detail.json ({len(detail)} cells, {len(det_cols)} fields)")

    opp = gpd.read_file("data/processed/opportunity_areas.geojson")
    # carry the two headline recommendations onto the polygons so the map can colour by them
    narr_path = PROC / "narratives.json"
    if narr_path.exists():
        na = json.loads(narr_path.read_text())["areas"]
        lut = {a["cluster_id"]: a for a in na}
        opp["infra_level"] = opp.cluster_id.map(lambda c: lut.get(c, {}).get("infrastructure", {}).get("level"))
        opp["infra_label"] = opp.cluster_id.map(lambda c: lut.get(c, {}).get("infrastructure", {}).get("label"))
        opp["nature_level"] = opp.cluster_id.map(lambda c: lut.get(c, {}).get("nature", {}).get("level"))
        opp["nature_label"] = opp.cluster_id.map(lambda c: lut.get(c, {}).get("nature", {}).get("label"))
        opp["n_sites"] = opp.cluster_id.map(lambda c: len(lut.get(c, {}).get("sites", [])))
        opp["protect_ha"] = opp.cluster_id.map(lambda c: lut.get(c, {}).get("nature", {}).get("protect_ha", 0))
        opp["restore_ha"] = opp.cluster_id.map(lambda c: lut.get(c, {}).get("nature", {}).get("restore_ha", 0))
    save_geojson(opp.drop(columns=["h3_cells"], errors="ignore"),
                 "opportunity_areas", decimals=4, to_web=True)

    # protected areas, simplified for display
    pa = gpd.read_file("data/raw/stri_protected_areas.geojson").to_crs(CRS_M)
    pa["geometry"] = pa.geometry.make_valid().simplify(250)
    pa = pa[["NOMBRE", "CAT_MANEJO", "IUCN_CAT", "TYPE", "HECTARES", "ESTAB_YR",
             "DESIG_TYPE", "geometry"]].rename(columns={
                 "NOMBRE": "name", "CAT_MANEJO": "category", "IUCN_CAT": "iucn",
                 "TYPE": "realm", "HECTARES": "hectares", "ESTAB_YR": "established",
                 "DESIG_TYPE": "designation"})
    save_geojson(pa, "protected_areas", decimals=4, to_web=True)

    # tourism/nature points, slimmed
    pois = gpd.read_file("data/processed/osm_pois.geojson")
    pois = pois[["theme", "name", "kind", "geometry"]]
    save_geojson(pois, "osm_pois", decimals=5, to_web=True)

    trails = gpd.read_file("data/processed/osm_trails.geojson")[["name", "geometry"]]
    save_geojson(trails, "osm_trails", decimals=5, to_web=True)

    # ---- concrete zones ----
    for name in ("tourism_nodes", "nature_zones"):
        src = Path("data/processed") / f"{name}.geojson"
        if src.exists():
            gg = gpd.read_file(src)
            save_geojson(gg, name, decimals=5, to_web=True)

    # ---- national summary for the Analysis page ----
    tot_area = float(d.area_km2.sum()) if "area_km2" in d else np.nan
    summary = {
        "cells": int(len(d)),
        "cell_km2": 37,
        "land_km2": 74274,
        "coastal_band_km": 30,
        "by_action": {k: int(v) for k, v in d.primary.value_counts().items()},
        "cells_no_basis": int((d.primary == "NONE").sum()),
        "dev_feasible_cells": int(d.dev_feasible.sum()) if "dev_feasible" in d else None,
        "cells_in_gov_dest": int(d.gov_dest.notna().sum()),
        "share_in_gov_dest": round(100 * float(d.gov_dest.notna().mean()), 1),
        "protected_share": round(100 * float(d.pa_frac.mean()), 1),
        "strict_protected_share": round(100 * float(d.pa_strict_frac.mean()), 1),
        "mangrove_km2": round(float((d.lc_mangrove * d.area_km2).sum()), 0),
        "forest_share": round(100 * float((d.lc_tree * d.area_km2).sum() / d.area_km2.sum()), 1),
        "population": int(d.population.sum()),
        "osm_accommodation": int(d.n_accommodation.sum()),
        "osm_food": int(d.n_food_service.sum()),
        "median_tt_gateway_h": round(float(d.tt_gateway_h.median()), 2),
        "family_means": {f: round(float(d[f].mean()), 1) for f in
                         ["NAV", "TDL", "ACC", "BCV", "RES", "JOBS"]},
        "opportunity_areas": int(len(opp)),
        "opp_by_action": {k: int(v) for k, v in opp.action.value_counts().items()},
        "tourism_nodes": int(len(gpd.read_file(Path("data/processed/tourism_nodes.geojson")))
                             if Path("data/processed/tourism_nodes.geojson").exists() else 0),
        "nature_zones": int(len(gpd.read_file(Path("data/processed/nature_zones.geojson")))
                            if Path("data/processed/nature_zones.geojson").exists() else 0),
        "opp_in_gov_plan": int(opp.in_gov_plan.sum()),
        "opp_outside_gov_plan": int((1 - opp.in_gov_plan).sum()),
    }
    # correlation between attraction and supply - the core "gap" story
    summary["corr_nav_tdl"] = round(float(d.NAV.corr(d.TDL)), 3)
    summary["cells_high_nav_low_tdl"] = int(((d.NAV >= 60) & (d.TDL <= 40)).sum())

    for p in (PROC / "summary.json", WEB_DATA / "summary.json"):
        p.write_text(json.dumps(summary, indent=2, allow_nan=False))
    log("  summary: " + json.dumps({k: summary[k] for k in
        ["cells", "opportunity_areas", "share_in_gov_dest", "cells_high_nav_low_tdl"]}))

    # committed analytical outputs (small, human-readable)
    out_dir = Path("data/outputs")
    out_dir.mkdir(exist_ok=True)
    opp.drop(columns="geometry").to_csv(out_dir / "opportunity_areas.csv", index=False)
    g.drop(columns="geometry").to_csv(out_dir / "grid_scored.csv", index=False)
    log(f"  wrote data/outputs/ (opportunity_areas.csv, grid_scored.csv)")

    total = sum(f.stat().st_size for f in WEB_DATA.glob("*"))
    log(f"  web payload total: {total/1e6:.1f} MB")
    for f in sorted(WEB_DATA.glob("*"), key=lambda x: -x.stat().st_size):
        log(f"    {f.name:28s} {f.stat().st_size/1e6:6.2f} MB")


if __name__ == "__main__":
    main()
