"""Step 13 - zonal statistics from global rasters onto the H3 grid.

Rasters are read remotely as COGs at decimated resolution (overview levels), so nothing
large is ever written to disk. Only the per-hexagon aggregates are kept. This is what lets
the repository stay small while the analysis stays real.

  ESA WorldCover 2021 v200 (10 m, CC BY 4.0)  -> land-cover fractions incl. mangrove class 95
  Copernicus DEM GLO-30 (30 m, free/open)     -> elevation, relief, low-elevation coastal zone
  WorldPop 2020 constrained (100 m, CC BY 4.0)-> population
"""
import sys
import warnings
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import Resampling
from rasterio.features import rasterize

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent))
from common import PROC, RAW, log  # noqa: E402

WC_URL = ("/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
          "ESA_WorldCover_10m_2021_v200_{tile}_Map.tif")
DEM_URL = ("/vsicurl/https://copernicus-dem-30m.s3.amazonaws.com/"
           "Copernicus_DSM_COG_10_{ns}_00_{ew}_00_DEM/Copernicus_DSM_COG_10_{ns}_00_{ew}_00_DEM.tif")
POP_REMOTE = ("https://data.worldpop.org/GIS/Population/Global_2000_2020_Constrained/"
              "2020/BSGM/PAN/pan_ppp_2020_UNadj_constrained.tif")

WC_CLASSES = {10: "tree", 20: "shrub", 30: "grass", 40: "crop", 50: "built",
              60: "bare", 70: "snow", 80: "water", 90: "wetland", 95: "mangrove", 100: "moss"}


def zonal_hist(url: str, shapes, n_zones: int, decim: int, classes: dict) -> np.ndarray:
    """Return counts[n_zones, max_class+1] of categorical values per zone."""
    with rasterio.open(url) as src:
        h, w = src.height // decim, src.width // decim
        arr = src.read(1, out_shape=(h, w), resampling=Resampling.nearest)
        tr = src.transform * src.transform.scale(src.width / w, src.height / h)
        zones = rasterize(shapes, out_shape=(h, w), transform=tr, fill=-1,
                          dtype="int32", all_touched=False)
    ok = zones >= 0
    if not ok.any():
        return np.zeros((n_zones, max(classes) + 1), dtype=np.int64)
    key = zones[ok].astype(np.int64) * (max(classes) + 1) + arr[ok].astype(np.int64)
    counts = np.bincount(key, minlength=n_zones * (max(classes) + 1))
    return counts.reshape(n_zones, max(classes) + 1)


def zonal_continuous(url: str, shapes, n_zones: int, decim: int, resampling=Resampling.average):
    """Return (sum, count, max) per zone for a continuous raster."""
    with rasterio.open(url) as src:
        if decim <= 1:
            h, w = src.height, src.width
            arr = src.read(1).astype("float64")
        else:
            h, w = max(1, src.height // decim), max(1, src.width // decim)
            arr = src.read(1, out_shape=(h, w), resampling=resampling).astype("float64")
        nod = src.nodata
        tr = src.transform * src.transform.scale(src.width / w, src.height / h)
        zones = rasterize(shapes, out_shape=(h, w), transform=tr, fill=-1,
                          dtype="int32", all_touched=False)
    valid = (zones >= 0) & np.isfinite(arr)
    if nod is not None:
        valid &= arr != nod
    valid &= arr > -1000
    z = zones[valid].astype(np.int64)
    v = arr[valid]
    s = np.bincount(z, weights=v, minlength=n_zones)
    c = np.bincount(z, minlength=n_zones).astype(np.float64)
    # NB: must seed with +/-inf, not NaN - np.maximum(NaN, x) is NaN and would poison every cell
    mx = np.full(n_zones, -np.inf)
    np.maximum.at(mx, z, v)
    lo = np.full(n_zones, np.inf)
    np.minimum.at(lo, z, v)
    return s, c, mx, lo


def wc_tiles(bounds) -> list[str]:
    minx, miny, maxx, maxy = bounds
    out = []
    for lat in range(int(np.floor(miny / 3) * 3), int(np.ceil(maxy / 3) * 3), 3):
        for lon in range(int(np.floor(minx / 3) * 3), int(np.ceil(maxx / 3) * 3), 3):
            ns = f"N{lat:02d}" if lat >= 0 else f"S{abs(lat):02d}"
            ew = f"W{abs(lon):03d}" if lon < 0 else f"E{lon:03d}"
            out.append(f"{ns}{ew}")
    return out


def dem_tiles(bounds) -> list[tuple[str, str]]:
    minx, miny, maxx, maxy = bounds
    out = []
    for lat in range(int(np.floor(miny)), int(np.ceil(maxy))):
        for lon in range(int(np.floor(minx)), int(np.ceil(maxx))):
            out.append((f"N{lat:02d}" if lat >= 0 else f"S{abs(lat):02d}",
                        f"W{abs(lon):03d}" if lon < 0 else f"E{lon:03d}"))
    return out


def main() -> None:
    g = gpd.read_file("data/processed/grid.geojson")
    n = len(g)
    shapes = [(geom, i) for i, geom in enumerate(g.geometry)]
    bounds = g.total_bounds
    log(f"  grid: {n} cells, bounds {np.round(bounds,2).tolist()}")

    # ---- ESA WorldCover ----
    lc_cache = PROC / "_cache_worldcover.csv"
    if lc_cache.exists():
        lc = pd.read_csv(lc_cache)
        log("  WorldCover: cache hit")
    else:
        lc = None
    maxc = max(WC_CLASSES)
    if lc is None:
        total = np.zeros((n, maxc + 1), dtype=np.int64)
        for tile in wc_tiles(bounds):
            url = WC_URL.format(tile=tile)
            try:
                total += zonal_hist(url, shapes, n, decim=10, classes=WC_CLASSES)
                log(f"  WorldCover {tile}: ok")
            except Exception as exc:  # noqa: BLE001
                log(f"  WorldCover {tile}: skipped ({str(exc)[:60]})")
        px = total.sum(axis=1)
        lc = pd.DataFrame({"h3": g.h3.values})
        for code, name in WC_CLASSES.items():
            lc[f"lc_{name}"] = np.where(px > 0, total[:, code] / np.maximum(px, 1), 0.0).round(4)
        lc["lc_pixels"] = px
        lc.to_csv(lc_cache, index=False)
    log(f"  WorldCover done. mean tree cover {lc.lc_tree.mean():.3f}, "
        f"cells with mangrove {int((lc.lc_mangrove>0).sum())}")

    # ---- Copernicus DEM ----
    dem_cache = PROC / "_cache_dem.csv"
    if dem_cache.exists():
        dem = pd.read_csv(dem_cache)
        log("  DEM: cache hit")
        s = c = None
    else:
      s = np.zeros(n); c = np.zeros(n)
      mx = np.full(n, -np.inf); mn = np.full(n, np.inf)
      for ns, ew in dem_tiles(bounds):
        url = DEM_URL.format(ns=ns, ew=ew)
        try:
            s_, c_, mx_, mn_ = zonal_continuous(url, shapes, n, decim=4)
            s += s_; c += c_
            mx = np.fmax(mx, mx_); mn = np.fmin(mn, mn_)
            log(f"  DEM {ns}{ew}: ok")
        except Exception as exc:  # noqa: BLE001
            log(f"  DEM {ns}{ew}: skipped ({str(exc)[:50]})")
      mx = np.where(np.isfinite(mx), mx, np.nan)
      mn = np.where(np.isfinite(mn), mn, np.nan)
      dem = pd.DataFrame({
          "h3": g.h3.values,
          "elev_mean": np.where(c > 0, s / np.maximum(c, 1), np.nan).round(1),
          "elev_max": np.round(mx, 1),
          "elev_min": np.round(mn, 1),
      })
      dem["relief_m"] = (dem.elev_max - dem.elev_min).round(1)
      dem.to_csv(dem_cache, index=False)
    log(f"  DEM done. max elevation {np.nanmax(dem.elev_max):.0f} m (Volcan Baru ~3,475 m)")

    # ---- WorldPop (server has no range-request support: fetch once, cache on disk) ----
    pop_local = RAW / "worldpop_pan_2020.tif"
    if not pop_local.exists():
        import requests
        from common import UA
        log("  downloading WorldPop national raster (one-off)...")
        with requests.get(POP_REMOTE, headers=UA, stream=True, timeout=600) as r:
            r.raise_for_status()
            with open(pop_local, "wb") as fh:
                for chunk in r.iter_content(1 << 20):
                    fh.write(chunk)
        log(f"    cached {pop_local.stat().st_size/1e6:.0f} MB")
    ps, pc, _, _ = zonal_continuous(str(pop_local), shapes, n, decim=1, resampling=Resampling.sum)
    pop = pd.DataFrame({"h3": g.h3.values, "population": np.round(ps, 0)})
    log(f"  WorldPop done. national total {pop.population.sum():,.0f} (census 2023 ~4.4M)")

    out = lc.merge(dem, on="h3").merge(pop, on="h3")
    out.to_csv(PROC / "grid_rasters.csv", index=False)
    log(f"  wrote grid_rasters.csv ({out.shape[0]} rows, {out.shape[1]} cols)")


if __name__ == "__main__":
    main()
