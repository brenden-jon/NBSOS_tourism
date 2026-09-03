"""Step 52 - turn each Opportunity Area into two concrete, separately mappable answers.

An Opportunity Area is still hundreds of square kilometres. A task team cannot act on
"invest somewhere in these 700 km2". This step produces the two things they actually need,
as distinct outputs:

  1. TOURISM NODES - specific sites where visitor infrastructure could go. Anchored on real
     named features (a beach, a waterfall, a dive site, a viewpoint), and admitted only if
     the site has road access, a settlement within reach to supply labour and services, and
     is not inside a strict protection core.

  2. NATURE ACTION ZONES - specific places where ecosystem investment supports that tourism,
     each labelled with the ecosystem and whether the action is PROTECT (it is there and
     working) or RESTORE (it should be there and is degraded or absent).

Keeping these separate matters: they are different budget lines, different implementing
agencies and different timelines.
"""
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import CRS_M, PROC, log, save_geojson  # noqa: E402

# --- tourism node admission rules ---
MAX_ROAD_KM = 2.5          # a site nobody can reach is not an infrastructure site
MAX_SETTLEMENT_KM = 12     # labour, services and supply have to come from somewhere
CLUSTER_KM = 4.0           # assets within this of each other form one node
MAX_NODES_PER_AREA = 5

# A node is anchored on a NATURAL asset - that is the product this tool is about. Built
# attractions still count toward the asset mix and the case for a node, but they never name
# one: an earlier pass produced nodes called "Museo de Arte Contemporaneo" and "Mi jardin es
# su jardin", which is not a nature-tourism finding.
NATURAL_ANCHORS = ["beach", "waterfall", "viewpoint", "dive_surf", "peak",
                   "reef_natural", "hotspring", "marina_port"]
SUPPORTING_THEMES = ["attraction", "visitor_infra"]
ANCHOR_THEMES = NATURAL_ANCHORS + SUPPORTING_THEMES

ASSET_LABEL = {
    "beach": "beach", "waterfall": "waterfall", "viewpoint": "viewpoint",
    "dive_surf": "dive/surf site", "peak": "peak", "attraction": "attraction",
    "reef_natural": "reef", "hotspring": "hot spring", "marina_port": "marina/landing",
}

# --- nature action thresholds ---
MANGROVE_PRESENT = 0.015
SHELF_PRESENT = 0.25
FOREST_INTACT = 0.60
FOREST_DEGRADED = 0.30
WETLAND_PRESENT = 0.02
STRICT_PROTECTED = 0.25


def build_nodes(opps, pois, roads_u, places_u, grid_m):
    """Concrete candidate sites for visitor infrastructure, anchored on named features."""
    named = pois[pois.name.notna() & pois.theme.isin(ANCHOR_THEMES)].copy()
    named["road_km"] = named.geometry.distance(roads_u) / 1000
    named["settle_km"] = named.geometry.distance(places_u) / 1000

    strict = grid_m[grid_m.pa_strict_frac > STRICT_PROTECTED].geometry.union_all()

    rows = []
    for area in opps.itertuples():
        if area.action not in ("INVEST", "ADAPT"):
            continue
        inside = named[named.within(area.geometry)].copy()
        ok = inside[(inside.road_km <= MAX_ROAD_KM) &
                    (inside.settle_km <= MAX_SETTLEMENT_KM)]
        if not len(ok):
            continue
        ok = ok[~ok.geometry.within(strict)] if not strict.is_empty else ok
        if not len(ok):
            continue

        # greedy clustering: strongest-connected asset first, absorb neighbours
        remaining = ok.copy()
        made = 0
        while len(remaining) and made < MAX_NODES_PER_AREA:
            natural = remaining[remaining.theme.isin(NATURAL_ANCHORS)]
            if not len(natural):
                break  # nothing natural left to anchor on
            # seed on the natural asset with the most company within CLUSTER_KM
            counts = natural.geometry.apply(
                lambda g: int((remaining.geometry.distance(g) <= CLUSTER_KM * 1000).sum()))
            seed_idx = counts.idxmax()
            seed = natural.loc[seed_idx]
            near = remaining[remaining.geometry.distance(seed.geometry) <= CLUSTER_KM * 1000]

            themes = near.theme.value_counts().to_dict()
            asset_names = [n for n in near.name.dropna().unique().tolist()][:6]
            rows.append({
                "node_id": f"{area.cluster_id}-N{made+1}",
                "area_id": area.cluster_id,
                "area_name": area.name,
                "action": area.action,
                "name": str(seed["name"]),
                "anchor_type": ASSET_LABEL.get(seed.theme, seed.theme),
                "n_assets": int(len(near)),
                "assets": "; ".join(asset_names),
                "n_natural": int(near.theme.isin(NATURAL_ANCHORS).sum()),
                "asset_mix": "; ".join(f"{ASSET_LABEL.get(k, k)} x{v}" for k, v in themes.items()),
                "road_km": round(float(near.road_km.min()), 2),
                "settlement_km": round(float(near.settle_km.min()), 2),
                "geometry": seed.geometry,
            })
            remaining = remaining.drop(near.index)
            made += 1
    if not rows:
        return gpd.GeoDataFrame(columns=["node_id", "geometry"], crs=CRS_M)
    g = gpd.GeoDataFrame(rows, crs=CRS_M)
    # rank nodes: more assets, closer road, closer settlement
    g["node_score"] = (np.log1p(g.n_natural) * 45 + np.log1p(g.n_assets) * 12
                       - g.road_km * 6 - g.settlement_km * 1.2).round(1)
    return g.sort_values(["area_id", "node_score"], ascending=[True, False])


def build_nature_zones(opps, cells):
    """Ecosystem-specific protect / restore zones inside each Opportunity Area."""
    rows = []
    for area in opps.itertuples():
        sub = cells[cells.h3.isin(str(area.h3_cells).split(","))]
        if not len(sub):
            continue
        a_cell = sub.area_km2.mean() if "area_km2" in sub else 37.0

        def add(mask, eco, action, why):
            sel = sub[mask]
            if len(sel) < 2:
                return
            geom = sel.geometry.union_all()
            rows.append({
                "zone_id": f"{area.cluster_id}-{eco[:3].upper()}{action[0]}",
                "area_id": area.cluster_id, "area_name": area.name,
                "ecosystem": eco, "action": action,
                "n_cells": int(len(sel)),
                "area_km2": round(float(geom.area / 1e6), 1),
                "eco_ha": int(round(_eco_hectares(sel, eco))),
                "rationale": why,
                "geometry": geom,
            })

        coastal = sub.zone.isin(["coastal", "nearshore"])
        # "belongs here" signals: if an ecosystem occurs anywhere in this area, its absence
        # in a comparable cell nearby is a restoration candidate rather than simply nature
        # that never existed.
        area_has_mangrove = float(sub.lc_mangrove.max()) >= MANGROVE_PRESENT
        area_has_forest = float(sub.lc_tree.max()) >= FOREST_INTACT
        exposure_cut = float(sub.coastal_exposure.median()) if coastal.any() else 0.0
        # --- mangrove ---
        add(coastal & (sub.lc_mangrove >= MANGROVE_PRESENT), "mangrove", "protect",
            "Mangrove is present and functioning between open water and low-lying assets; "
            "protecting standing mangrove is cheaper and more certain than replanting it.")
        add(coastal & (sub.lc_mangrove < MANGROVE_PRESENT) & area_has_mangrove
            & (sub.coastal_exposure >= exposure_cut), "mangrove", "restore",
            "Mangrove is thin or fragmented here but the coastal setting supports it and there "
            "are people and tourism assets behind it; replanting at the landward margin and "
            "restoring tidal flow is indicated.")
        # --- reef / shelf ---
        add(coastal & (sub.shallow_frac >= SHELF_PRESENT) & (sub.pa_strict_frac < STRICT_PROTECTED),
            "reef and shallow shelf", "protect",
            "Shallow reef-capable habitat with little strict protection, in an area where "
            "snorkelling and diving are or could be the product.")
        # --- forest ---
        add((~coastal) & (sub.lc_tree >= FOREST_INTACT), "forest", "protect",
            "Intact forest on slopes above settlements and visitor infrastructure; retaining "
            "cover is the low-cost option and it is also the attraction.")
        add((sub.lc_tree < FOREST_DEGRADED) & (sub.relief_m > 200) & area_has_forest,
            "forest", "restore",
            "Cleared or degraded slopes in the same catchment as the destination; replanting "
            "targets erosion, dry-season flow and the visual quality of the landscape.")
        # --- wetland ---
        add(sub.lc_wetland >= WETLAND_PRESENT, "wetland", "protect",
            "Herbaceous wetland with water-regulation and birdlife value that is itself a "
            "visitor product.")
        # --- riparian corridor: degraded land close to the coast, behind the mangrove line ---
        add(coastal & (sub.lc_tree < FOREST_DEGRADED) & (sub.lc_crop > 0.2)
            & (sub.dist_coast_km < 5), "coastal woodland", "restore",
            "Cleared coastal land immediately behind the shoreline. Replanting here buffers "
            "runoff and sediment reaching nearshore habitat and improves the setting visitors "
            "actually experience.")
    if not rows:
        return gpd.GeoDataFrame(columns=["zone_id", "geometry"], crs=CRS_M)
    return gpd.GeoDataFrame(rows, crs=CRS_M)


def _eco_hectares(sel, eco):
    a = sel.area_km2 * 100  # km2 -> ha
    if eco == "mangrove":
        return float((sel.lc_mangrove * a).sum())
    if eco.startswith("reef"):
        return float((sel.shallow_frac * a).sum())
    if eco == "forest":
        return float((sel.lc_tree * a).sum())
    if eco == "wetland":
        return float((sel.lc_wetland * a).sum())
    return float(a.sum())


def main() -> None:
    opps = gpd.read_file("data/processed/opportunity_areas.geojson").to_crs(CRS_M)
    # step 60 rewrites the processed copy without h3_cells; the CSV keeps the membership
    membership = pd.read_csv(PROC / "opportunity_areas.csv")[["cluster_id", "h3_cells"]]
    opps = opps.drop(columns=["h3_cells"], errors="ignore").merge(membership, on="cluster_id")
    grid = gpd.read_file("data/processed/grid.geojson").to_crs(CRS_M)[["h3", "geometry"]]
    cls = pd.read_csv(PROC / "grid_classified.csv")
    cells = grid.merge(cls, on="h3")
    pois = gpd.read_file("data/processed/osm_pois.geojson").to_crs(CRS_M)
    roads = gpd.read_file("data/processed/osm_roads.geojson").to_crs(CRS_M)
    places = gpd.read_file("data/raw/stri_places.geojson").to_crs(CRS_M)
    log(f"  {len(opps)} areas, {len(pois)} POIs")

    roads_u = roads.geometry.union_all()
    places_u = places.geometry.union_all()

    nodes = build_nodes(opps, pois, roads_u, places_u, cells)
    log(f"  tourism nodes: {len(nodes)} across "
        f"{nodes.area_id.nunique() if len(nodes) else 0} areas")
    if len(nodes):
        for r in nodes.head(12).itertuples():
            log(f"    {r.node_id:10s} {r.name[:34]:34s} {r.n_assets:2d} assets  "
                f"road {r.road_km:4.1f} km  town {r.settlement_km:4.1f} km")
        save_geojson(nodes, "tourism_nodes", decimals=5, to_web=True)

    zones = build_nature_zones(opps, cells)
    log(f"  nature action zones: {len(zones)}")
    if len(zones):
        log("  by ecosystem/action: " +
            str(zones.groupby(["ecosystem", "action"]).size().to_dict()))
        zones["geometry"] = zones.geometry.simplify(200)
        save_geojson(zones, "nature_zones", decimals=4, to_web=True)

    nodes.drop(columns="geometry").to_csv(PROC / "tourism_nodes.csv", index=False)
    zones.drop(columns="geometry").to_csv(PROC / "nature_zones.csv", index=False)


if __name__ == "__main__":
    main()
