"""Step 50 - group cells into named Opportunity Areas.

A national hex ranking is not the product. The product is a manageable number of specific
places a task team could actually take forward. We therefore keep only strongly-scoring
cells, join them into contiguous clusters of the same recommendation type, name them from
the real geography they sit in, and attach the evidence that produced them.
"""
import json
import sys
from pathlib import Path

import geopandas as gpd
import h3
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import CRS_M, PROC, log, save_geojson  # noqa: E402

MIN_CELLS = 4          # ~150 km2 - below this it is a site, not an area
FIT_PCTL = 0.85        # keep the strongest cells within each action class


def components(cells: set[str]) -> list[list[str]]:
    """Connected components over H3 adjacency."""
    seen, out = set(), []
    for c in cells:
        if c in seen:
            continue
        stack, comp = [c], []
        seen.add(c)
        while stack:
            cur = stack.pop()
            comp.append(cur)
            for nb in h3.grid_disk(cur, 1):
                if nb in cells and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        out.append(comp)
    return out


def main() -> None:
    d = pd.read_csv(PROC / "grid_classified.csv")
    grid = gpd.read_file("data/processed/grid.geojson").to_crs(CRS_M)
    pois = gpd.read_file("data/processed/osm_pois.geojson").to_crs(CRS_M)
    places = gpd.read_file("data/raw/stri_places.geojson").to_crs(CRS_M)
    geom = dict(zip(grid.h3, grid.geometry))

    # threshold within each class so every action type can surface somewhere
    keep = []
    for cls, grp in d.groupby("primary"):
        thr = grp.primary_fit.quantile(FIT_PCTL)
        sel = grp[grp.primary_fit >= thr]
        log(f"  {cls:8s} threshold fit {thr:.1f} -> {len(sel)} cells retained")
        keep.append(sel)
    kept = pd.concat(keep)

    clusters = []
    for cls, grp in kept.groupby("primary"):
        cset = set(grp.h3)
        for comp in components(cset):
            if len(comp) >= MIN_CELLS:
                clusters.append((cls, comp))
    log(f"  {len(clusters)} clusters of >= {MIN_CELLS} cells")

    # ---- naming ---------------------------------------------------------------------
    # Areas are named from authoritative geography, never from an individual OSM point.
    # An earlier pass named clusters after whatever attraction happened to be mapped inside
    # them, producing area names like "Mi jardin es su jardin" (a garden in Boquete) and
    # "Panama Outdoor Adventures" (a tour operator). Priority is now:
    #   1. a protected area covering a substantial share of the cluster
    #   2. the government destination the cluster sits in
    #   3. the dominant district, or the two dominant districts
    def name_cluster(sub, poly):
        pa_names = sub.pa_name.dropna()
        if len(pa_names):
            top = pa_names.value_counts()
            if top.iloc[0] / len(sub) >= 0.35:
                return str(top.index[0]).strip()

        gov = sub.gov_dest.dropna()
        if len(gov) / len(sub) >= 0.50:
            return str(gov.value_counts().index[0])

        # Guna Yala's district field reads "No asignado" in the national layer; fall back
        # to the province, which is the meaningful unit there.
        dist = sub.district.dropna()
        dist = dist[dist.str.strip().str.lower() != "no asignado"].value_counts()
        if len(dist) == 0:
            prov = sub.province.dropna().value_counts()
            return str(prov.index[0]) if len(prov) else "Unnamed area"
        if len(dist) > 1 and dist.iloc[1] / len(sub) >= 0.30:
            return f"{dist.index[0]}-{dist.index[1]}"
        return str(dist.index[0])

    rows = []
    for cls, comp in clusters:
        sub = d[d.h3.isin(comp)]
        poly = gpd.GeoSeries([geom[h] for h in comp], crs=CRS_M).union_all()
        pa_names = sub.pa_name.dropna()
        name = name_cluster(sub, poly)

        named_pois = pois[pois.within(poly) & pois.name.notna()]
        assets = (named_pois[named_pois.theme.isin(
            ["attraction", "beach", "waterfall", "peak", "viewpoint", "dive_surf", "marina_port"])]
            .name.dropna().unique().tolist()[:12])

        gov = sub.gov_dest.dropna()
        gov_dest = gov.value_counts().idxmax() if len(gov) else None
        gov_share = len(gov) / len(sub)

        rows.append({
            "cluster_id": f"{cls[:2]}{len(rows)+1:02d}",
            "name": name,
            "action": cls,
            "n_cells": len(comp),
            "area_km2": round(poly.area / 1e6, 1),
            "fit": round(sub.primary_fit.mean(), 1),
            "NAV": round(sub.NAV.mean(), 1), "TDL": round(sub.TDL.mean(), 1),
            "ACC": round(sub.ACC.mean(), 1), "BCV": round(sub.BCV.mean(), 1),
            "RES": round(sub.RES.mean(), 1), "JOBS": round(sub.JOBS.mean(), 1),
            "sensitivity": round(sub.sensitivity.mean(), 1),
            "protection_gap": round(sub.protection_gap.mean(), 1),
            "supply_gap": round(sub.supply_gap.mean(), 1),
            "pa_frac": round(sub.pa_frac.mean(), 3),
            "pa_strict_frac": round(sub.pa_strict_frac.mean(), 3),
            "pa_names": "; ".join(sorted(set(pa_names))[:5]),
            "mangrove_frac": round(sub.lc_mangrove.mean(), 4),
            "tree_frac": round(sub.lc_tree.mean(), 3),
            "shallow_frac": round(sub.shallow_frac.mean(), 3),
            "wetland_frac": round(sub.lc_wetland.mean(), 4),
            "relief_m": round(sub.relief_m.mean(), 0),
            "elev_max": round(sub.elev_max.max(), 0),
            "gbif_species": int(sub.gbif_species.mean()),
            "tt_gateway_h": round(sub.tt_gateway_h.median(), 2),
            "population": int(sub.population.sum()),
            "n_accommodation": int(sub.n_accommodation.sum()),
            "n_food_service": int(sub.n_food_service.sum()),
            "n_attraction": int(sub.n_attraction.sum()),
            "n_beach": int(sub.n_beach.sum()),
            "n_trail": int(sub.n_trail.sum()),
            "n_dive_surf": int(sub.n_dive_surf.sum()),
            "n_marina_port": int(sub.n_marina_port.sum()),
            "is_comarca": int(sub.is_comarca.max()),
            "provinces": "; ".join(sorted(set(sub.province.dropna()))[:4]),
            "districts": "; ".join(sorted(set(sub.district.dropna()))[:6]),
            "ecoregion": sub.ecoregion.value_counts().idxmax() if sub.ecoregion.notna().any() else None,
            "watershed": sub.watershed.value_counts().idxmax() if sub.watershed.notna().any() else None,
            "gov_dest": gov_dest,
            "gov_share": round(gov_share, 2),
            "gov_relation": ("reinforces" if gov_share >= 0.5 and cls == "INVEST"
                             else "refines" if gov_share >= 0.5
                             else "partial" if gov_share > 0.15 else "new"),
            "assets": "; ".join(assets),
            "h3_cells": ",".join(comp),
            "geometry": poly,
        })

    g = gpd.GeoDataFrame(rows, crs=CRS_M)
    # priority = strength x scale, so a strong 4-cell cluster does not beat a strong 20-cell one
    g["priority_score"] = (g.fit * np.log1p(g.n_cells)).round(1)
    g = g.sort_values("priority_score", ascending=False).reset_index(drop=True)
    g["rank"] = g.index + 1

    # two clusters can legitimately share a protected area or district; qualify the repeats
    seen: dict[str, int] = {}
    labels = []
    for r in g.itertuples():
        base = str(r.name)
        if base in seen:
            seen[base] += 1
            quals = [q for q in str(r.districts).split("; ") + str(r.provinces).split("; ")
                     if q and q.strip().lower() != "no asignado" and q not in base]
            labels.append(f"{base} ({quals[0]})" if quals else f"{base} {seen[base]}")
        else:
            seen[base] = 1
            labels.append(base)
    g["name"] = labels

    log(f"  {len(g)} opportunity areas by action: {g.action.value_counts().to_dict()}")
    log("  top 20:")
    for r in g.head(20).itertuples():
        log(f"    {r.rank:2d}. [{r.action:7s}] {r.name[:38]:38s} {r.area_km2:7.0f} km2  "
            f"fit {r.fit:4.1f}  gov:{r.gov_relation}")

    g["geometry"] = g.geometry.simplify(200)
    save_geojson(g, "opportunity_areas", decimals=4)
    g.drop(columns="geometry").to_csv(PROC / "opportunity_areas.csv", index=False)


if __name__ == "__main__":
    main()
