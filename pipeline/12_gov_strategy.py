"""Step 12 - turn the ATP master plan into a structured, mappable layer.

The plan names destinations but publishes no boundaries. We derive destination polygons by
dissolving the official distrito units that contain the places the plan names. These polygons
are an ANALYTICAL OPERATIONALISATION, not official geography, and are labelled as such.
"""
import json
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import CRS_M, PROC, WEB_DATA, log, save_geojson  # noqa: E402
from gov_strategy_source import DESTINATIONS, PLAN, ROUTES  # noqa: E402


def main() -> None:
    d = gpd.read_file("data/raw/stri_districts.geojson")
    d["geometry"] = d.geometry.make_valid()
    d = d.to_crs(CRS_M)

    key = {(str(r.Provincia).strip(), str(r.Distrito).strip()): r.Index for r in d.itertuples()}

    rows, missing = [], []
    for dest in DESTINATIONS:
        idxs = []
        for prov, dist in dest["districts"]:
            k = (prov, dist)
            if k in key:
                idxs.append(key[k])
            else:
                missing.append((dest["id"], prov, dist))
        if not idxs:
            continue
        geom = d.loc[idxs].geometry.union_all()
        rows.append({
            "id": dest["id"], "name": dest["name"], "tier": dest["tier"],
            "products": "; ".join(dest["products"]),
            "nature_hooks": "; ".join(dest["nature_hooks"]),
            "vocation_en": dest["vocation_en"], "vocation_es": dest["vocation_es"],
            "districts": "; ".join(f"{p}/{x}" for p, x in dest["districts"]),
            "geometry": geom,
        })

    if missing:
        raise SystemExit(f"District name mismatches - fix gov_strategy_source: {missing}")

    gdf = gpd.GeoDataFrame(rows, crs=CRS_M)
    gdf["area_km2"] = (gdf.geometry.area / 1e6).round(1)
    # simplify for web delivery (50 m is far below screening scale)
    # 300 m: these are district unions used as an overlay at national scale, not a boundary record
    gdf["geometry"] = gdf.geometry.simplify(300)
    log(f"  built {len(gdf)} destination polygons "
        f"({(gdf.tier == 'priority').sum()} priority, {(gdf.tier == 'action_plan').sum()} action-plan)")
    for r in gdf.sort_values("area_km2", ascending=False).itertuples():
        log(f"    {r.tier:12s} {r.name[:46]:46s} {r.area_km2:>9,.0f} km2")
    save_geojson(gdf, "gov_destinations", decimals=4, to_web=True)

    meta = {"plan": PLAN, "routes": ROUTES,
            "destinations": [{k: v for k, v in x.items() if k != "geometry"} for x in rows]}
    for target in (PROC / "gov_strategy.json", WEB_DATA / "gov_strategy.json"):
        target.write_text(json.dumps(meta, indent=2, ensure_ascii=False, allow_nan=False))
    log(f"  wrote gov_strategy.json ({len(meta['destinations'])} destinations, {len(ROUTES)} routes)")


if __name__ == "__main__":
    main()
