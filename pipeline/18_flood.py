"""Step 18 - real flood hazard, and the population standing in it.

DATA
  WRI Aqueduct Floods v2 (Ward et al.), 30 arcsec (~1 km), CC BY 4.0.
    riverine  inunriver_historical_000000000WATCH_1980_rp{RP}.tif
    coastal   inuncoast_historical_nosub_hist_rp{RP}_0.tif  (no subsidence, historical SLR)
  Pixel values are inundation depth in metres for the given return period.
  https://www.wri.org/data/aqueduct-floods-hazard-maps

WHAT THIS STEP PRODUCES
  Per screening cell, for the 1-in-10 and 1-in-100 year events, separately for riverine and
  coastal flooding:
    *_frac        share of the cell inundated
    *_depth_mean  mean depth over inundated ground
    *_pop         population living on inundated ground

  Population is intersected with the hazard AT THE HAZARD'S OWN RESOLUTION: WorldPop (100 m)
  is summed onto the 30 arcsec flood grid first, then masked by depth, then aggregated to
  hexagons. Doing it the other way round - taking a cell's total population and scaling it by
  the flooded fraction - would smear people evenly across terrain they do not occupy.

LIMITS
  Aqueduct is a global model. It does not resolve flood defences, and Panama has urban
  drainage and canal-zone infrastructure it cannot see. Treat these as screening-level
  exposure, not a local flood study. The ~90 m World Bank hazard maps would supersede this.
"""
import sys
import warnings
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import requests
from rasterio.enums import Resampling
from rasterio.features import rasterize
from rasterio.warp import reproject
from rasterio.windows import from_bounds

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent))
from common import CRS_WGS, PROC, RAW, UA, log  # noqa: E402

BASE = "https://aqueduct.wridata.org/AqueductFloods20"
LAYERS = {
    "riv_rp10":  "inunriver_historical_000000000WATCH_1980_rp00010.tif",
    "riv_rp100": "inunriver_historical_000000000WATCH_1980_rp00100.tif",
    "cst_rp10":  "inuncoast_historical_nosub_hist_rp0010_0.tif",
    "cst_rp100": "inuncoast_historical_nosub_hist_rp0100_0.tif",
}
PAD = 0.3          # degrees of margin around the grid
MIN_DEPTH = 0.05   # m - below this the model is noise, not flooding


def fetch(name: str) -> Path:
    dest = RAW / f"aqueduct_{name}.tif"
    if dest.exists() and dest.stat().st_size > 1_000_000:
        return dest
    url = f"{BASE}/{LAYERS[name]}"
    log(f"  downloading {name} ({LAYERS[name]})...")
    with requests.get(url, headers=UA, stream=True, timeout=1800) as r:
        r.raise_for_status()
        with open(dest, "wb") as fh:
            for chunk in r.iter_content(1 << 22):
                fh.write(chunk)
    log(f"    {dest.stat().st_size/1e6:.0f} MB")
    return dest


def main() -> None:
    grid = gpd.read_file("data/processed/grid.geojson").to_crs(CRS_WGS)
    minx, miny, maxx, maxy = grid.total_bounds
    bounds = (minx - PAD, miny - PAD, maxx + PAD, maxy + PAD)
    n = len(grid)
    log(f"  {n} cells, bounds {np.round(bounds, 2).tolist()}")

    # ---- reference grid: the hazard raster's own 30 arcsec lattice over Panama ----
    ref_path = fetch("riv_rp100")
    with rasterio.open(ref_path) as src:
        win = from_bounds(*bounds, transform=src.transform).round_offsets().round_lengths()
        ref_transform = src.window_transform(win)
        ref_shape = (int(win.height), int(win.width))
        ref_crs = src.crs
    log(f"  hazard window {ref_shape[0]} x {ref_shape[1]} at 30 arcsec")

    # ---- population summed onto that lattice ----
    pop_src = RAW / "worldpop_pan_2020.tif"
    pop_on_hazard = np.zeros(ref_shape, dtype="float64")
    with rasterio.open(pop_src) as ps:
        reproject(
            source=rasterio.band(ps, 1),
            destination=pop_on_hazard,
            src_transform=ps.transform, src_crs=ps.crs,
            dst_transform=ref_transform, dst_crs=ref_crs,
            resampling=Resampling.sum,
        )
    pop_on_hazard[~np.isfinite(pop_on_hazard)] = 0
    pop_on_hazard[pop_on_hazard < 0] = 0
    log(f"  population re-gridded onto the hazard lattice: {pop_on_hazard.sum():,.0f}")

    # ---- hexagon ids burned onto the same lattice ----
    zones = rasterize(((g, i) for i, g in enumerate(grid.geometry)),
                      out_shape=ref_shape, transform=ref_transform, fill=-1, dtype="int32")
    valid = zones >= 0
    z = zones[valid].astype(np.int64)
    cell_px = np.bincount(z, minlength=n).astype(float)
    pop_px = np.bincount(z, weights=pop_on_hazard[valid], minlength=n)

    out = pd.DataFrame({"h3": grid.h3.values,
                        "flood_pixels": cell_px.astype(int),
                        "pop_on_hazard_grid": np.round(pop_px, 0)})

    # ---- each hazard layer ----
    for name in LAYERS:
        path = fetch(name)
        with rasterio.open(path) as src:
            win = from_bounds(*bounds, transform=src.transform).round_offsets().round_lengths()
            depth = src.read(1, window=win).astype("float32")
            nod = src.nodata
        if depth.shape != ref_shape:
            depth = depth[:ref_shape[0], :ref_shape[1]]
        if nod is not None:
            depth[depth == nod] = 0
        depth[~np.isfinite(depth)] = 0
        depth[depth < MIN_DEPTH] = 0

        wet = depth > 0
        wet_px = np.bincount(z, weights=wet[valid].astype(float), minlength=n)
        depth_sum = np.bincount(z, weights=(depth * wet)[valid], minlength=n)
        pop_wet = np.bincount(z, weights=(pop_on_hazard * wet)[valid], minlength=n)

        out[f"{name}_frac"] = np.where(cell_px > 0, wet_px / np.maximum(cell_px, 1), 0).round(4)
        out[f"{name}_depth"] = np.where(wet_px > 0, depth_sum / np.maximum(wet_px, 1), 0).round(2)
        out[f"{name}_pop"] = np.round(pop_wet, 0)
        log(f"  {name}: {int((out[f'{name}_frac'] > 0).sum())} cells affected, "
            f"{out[f'{name}_pop'].sum():,.0f} people exposed nationally, "
            f"mean depth {out.loc[out[f'{name}_depth'] > 0, f'{name}_depth'].mean():.2f} m")

    out["flood_pop_rp100"] = (out.riv_rp100_pop + out.cst_rp100_pop).round(0)
    out["flood_frac_rp100"] = out[["riv_rp100_frac", "cst_rp100_frac"]].max(axis=1)
    log(f"  combined RP100 exposure: {out.flood_pop_rp100.sum():,.0f} people "
        f"({100*out.flood_pop_rp100.sum()/max(out.pop_on_hazard_grid.sum(),1):.1f}% of population)")

    out.to_csv(PROC / "grid_flood.csv", index=False)
    log(f"  wrote grid_flood.csv ({len(out)} rows, {out.shape[1]} cols)")


if __name__ == "__main__":
    main()
