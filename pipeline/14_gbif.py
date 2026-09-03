"""Step 14 - species richness and recording effort from GBIF.

We aggregate at H3 resolution 5 (~250 km2) and inherit the value to the res-6 analysis
cells. Querying at res 6 directly would need ~4,400 API calls; res 5 needs ~650 and the
biodiversity signal is not meaningful at finer grain anyway given occurrence-record
positional and sampling bias.

IMPORTANT INTERPRETATION NOTE
  GBIF occurrence density measures *where people have recorded wildlife*, not where
  wildlife is. It is strongly biased toward research stations (Barro Colorado), road
  access and established birding sites. We therefore use it two ways, deliberately:
    - species richness  -> a weak positive biodiversity signal
    - record density    -> a proxy for existing wildlife-watching interest/effort
  Neither is treated as a survey. See docs/limitations.md.
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import geopandas as gpd
import h3
import numpy as np
import pandas as pd
import requests
from shapely.geometry import Polygon

sys.path.insert(0, str(Path(__file__).parent))
from common import PROC, RAW, UA, log  # noqa: E402

API = "https://api.gbif.org/v1/occurrence/search"
CACHE = RAW / "gbif"
CACHE.mkdir(parents=True, exist_ok=True)
THREAT_CACHE = RAW / "gbif_threatened"
THREAT_CACHE.mkdir(parents=True, exist_ok=True)

# IUCN Red List categories counted as threatened. GBIF exposes the assessment directly on
# occurrence search, so this needs no separate Red List API token.
THREATENED = ["CR", "EN", "VU"]

# Vertebrate classes: well recorded and the ones tourists actually come to see.
CLASS_KEYS = {"Aves": 212, "Mammalia": 359, "Amphibia": 131, "Reptilia": 358}
FACET_LIMIT = 1000


def cell_wkt(cell: str) -> str:
    """Counter-clockwise WKT polygon for a GBIF geometry query."""
    pts = [(lng, lat) for lat, lng in h3.cell_to_boundary(cell)]
    poly = Polygon(pts)
    if not poly.exterior.is_ccw:
        pts = pts[::-1]
    ring = pts + [pts[0]]
    return "POLYGON((" + ",".join(f"{x:.5f} {y:.5f}" for x, y in ring) + "))"


def query_cell(cell: str) -> dict:
    cpath = CACHE / f"{cell}.json"
    if cpath.exists():
        return json.loads(cpath.read_text())

    out = {"h3_5": cell, "records": 0, "species": 0, "capped": False}
    for cname, ckey in CLASS_KEYS.items():
        params = {
            "hasCoordinate": "true", "hasGeospatialIssue": "false",
            "classKey": ckey, "geometry": cell_wkt(cell),
            "facet": "speciesKey", "facetLimit": FACET_LIMIT, "limit": 0,
        }
        for attempt in range(4):
            try:
                r = requests.get(API, params=params, headers=UA, timeout=90)
                r.raise_for_status()
                d = r.json()
                break
            except Exception:  # noqa: BLE001
                if attempt == 3:
                    d = {"count": 0, "facets": []}
                time.sleep(2 * (attempt + 1))
        n_rec = d.get("count", 0)
        facets = d.get("facets") or []
        n_sp = len(facets[0]["counts"]) if facets else 0
        out["records"] += n_rec
        out["species"] += n_sp
        out[f"sp_{cname.lower()}"] = n_sp
        if n_sp >= FACET_LIMIT:
            out["capped"] = True
    cpath.write_text(json.dumps(out))
    return out


def query_threatened(cell: str) -> dict:
    """Distinct threatened (CR/EN/VU) species recorded in a cell, across all taxa."""
    cpath = THREAT_CACHE / f"{cell}.json"
    if cpath.exists():
        return json.loads(cpath.read_text())
    params = [("hasCoordinate", "true"), ("hasGeospatialIssue", "false"),
              ("geometry", cell_wkt(cell)), ("facet", "speciesKey"),
              ("facetLimit", 800), ("limit", 0)]
    params += [("iucnRedListCategory", c) for c in THREATENED]
    out = {"h3_5": cell, "threatened_records": 0, "threatened_species": 0}
    for attempt in range(4):
        try:
            r = requests.get(API, params=params, headers=UA, timeout=90)
            r.raise_for_status()
            d = r.json()
            facets = d.get("facets") or []
            out["threatened_records"] = d.get("count", 0)
            out["threatened_species"] = len(facets[0]["counts"]) if facets else 0
            break
        except Exception:  # noqa: BLE001
            time.sleep(2 * (attempt + 1))
    cpath.write_text(json.dumps(out))
    return out


def main() -> None:
    g = gpd.read_file("data/processed/grid.geojson")
    g["h3_5"] = [h3.cell_to_parent(c, 5) for c in g.h3]
    parents = sorted(g.h3_5.unique())
    log(f"  {len(g)} res-6 cells -> {len(parents)} res-5 parents to query")

    # GBIF tolerates modest concurrency; 8 workers turns ~90 min into ~12.
    done = [0]

    def work(cell):
        out = query_cell(cell)
        done[0] += 1
        if done[0] % 50 == 0:
            log(f"    {done[0]}/{len(parents)} ({100*done[0]/len(parents):.0f}%)")
        return out

    with ThreadPoolExecutor(max_workers=8) as ex:
        rows = list(ex.map(work, parents))
    df = pd.DataFrame(rows)

    log("  querying threatened (CR/EN/VU) species per cell")
    tdone = [0]

    def twork(cell):
        o = query_threatened(cell)
        tdone[0] += 1
        if tdone[0] % 100 == 0:
            log(f"    threatened {tdone[0]}/{len(parents)}")
        return o

    with ThreadPoolExecutor(max_workers=8) as ex:
        trows = list(ex.map(twork, parents))
    df = df.merge(pd.DataFrame(trows), on="h3_5", how="left")
    log(f"  threatened species per res-5 cell: median {df.threatened_species.median():.0f}, "
        f"max {df.threatened_species.max()}")
    log(f"  queried. capped cells: {int(df.capped.sum())} of {len(df)}")
    log(f"  species per res-5 cell: median {df.species.median():.0f}, max {df.species.max()}")
    log(f"  total records seen: {df.records.sum():,}")

    out = g[["h3", "h3_5"]].merge(df, on="h3_5", how="left")
    out = out.rename(columns={"records": "gbif_records", "species": "gbif_species"})
    out = out.rename(columns={"threatened_species": "gbif_threatened",
                              "threatened_records": "gbif_threatened_records"})
    out[["h3", "gbif_records", "gbif_species", "sp_aves", "sp_mammalia",
         "sp_amphibia", "sp_reptilia", "gbif_threatened",
         "gbif_threatened_records"]].to_csv(PROC / "grid_gbif.csv", index=False)
    log(f"  wrote grid_gbif.csv ({len(out)} rows)")


if __name__ == "__main__":
    main()
