"""Step 19 - what the ecosystems actually do for the people standing in the flood zone.

This is the step that turns "there is mangrove here" and "there are people in the flood
zone here" into a statement about protection. It is screening-level and the coefficients are
published ranges, not calibrated local values - but it is a model, not a coincidence count,
and it is stated with its sources.

COASTAL - quantified
  Mangrove wave attenuation. McIvor et al. (2012) report wave-height reduction of 13-66% per
  100 m of mangrove width. We use a 50% reduction per 100 m as the central case, applied
  exponentially with width:  attenuation = 1 - 0.5 ^ (width / 100).
  Mangrove width is estimated as mangrove area divided by the length of coastline in the
  cell - a crude but conventional proxy that is wrong wherever mangrove sits in a lagoon
  rather than as a shore-parallel belt.

  Coral reef wave attenuation. Ferrario et al. (2014, Nature Communications) find reefs
  dissipate 97% of wave energy on average. We apply a reduced, presence-scaled version
  because we have reef-capable shelf extent, not reef condition.

  The two combine multiplicatively on the residual: 1 - (1-m)(1-r).

  What this is NOT: a surge model. Wave attenuation is not the same as reducing still-water
  flood depth, and Aqueduct's coastal layer is a surge-plus-depth product. The result should
  be read as "the share of wave energy reaching these people that existing ecosystems remove",
  not as avoided flooding and certainly not as avoided damages.

RIVERINE - deliberately NOT quantified
  Catchment forest does moderate runoff, but the effect on peak flows at basin scale is
  contested and strongly dependent on soil, antecedent conditions and event size. Claiming a
  percentage here would be false precision. Instead this step ranks catchments by the
  combination of flood-exposed population downstream and forest cover upstream, which is a
  prioritisation statement rather than a hydrological one.
"""
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import CRS_M, PROC, log  # noqa: E402

HALVING_WIDTH_M = 100.0     # mangrove width that halves wave height (McIvor et al. 2012)
REEF_MAX_ATT = 0.60         # capped well below Ferrario's 0.97: we have extent, not condition
TOTAL_ATT_CEILING = 0.90    # no ecosystem removes all wave energy; the exponential model
                            # asymptotes to 1 and would otherwise report physically silly
                            # figures wherever the mangrove belt is a kilometre wide
MANGROVE_RESTORE_TARGET_M = 150.0   # width a restoration programme could plausibly reach


def main() -> None:
    grid = gpd.read_file("data/processed/grid.geojson").to_crs(CRS_M)
    cls = pd.read_csv(PROC / "grid_indicators.csv")
    fl = pd.read_csv(PROC / "grid_flood.csv")
    d = grid.merge(cls, on="h3").merge(fl, on="h3")
    log(f"  {len(d)} cells")

    # ---- coastline length inside each cell ----
    land = gpd.read_file("data/processed/panama_land.geojson").to_crs(CRS_M)
    coast = land.geometry.union_all().boundary
    d["coast_len_m"] = d.geometry.intersection(coast).length.round(0)
    has_coast = d.coast_len_m > 0
    log(f"  {int(has_coast.sum())} cells contain coastline")

    # ---- mangrove belt width proxy ----
    d["mangrove_ha"] = (d.lc_mangrove * d.area_km2 * 100).round(1)
    mangrove_m2 = d.lc_mangrove * d.area_km2 * 1e6
    d["mangrove_width_m"] = np.where(has_coast,
                                     mangrove_m2 / d.coast_len_m.replace(0, np.nan), 0.0)
    d["mangrove_width_m"] = d.mangrove_width_m.fillna(0).clip(0, 3000).round(0)

    # ---- attenuation ----
    att_mg = 1 - 0.5 ** (d.mangrove_width_m / HALVING_WIDTH_M)
    att_reef = REEF_MAX_ATT * np.clip(d.shallow_frac.fillna(0) / 0.5, 0, 1)
    d["att_mangrove"] = att_mg.round(3)
    d["att_reef"] = att_reef.round(3)
    d["att_total"] = np.minimum(1 - (1 - att_mg) * (1 - att_reef), TOTAL_ATT_CEILING).round(3)

    # ---- who is behind it ----
    d["coastal_pop_exposed"] = d.cst_rp100_pop.fillna(0)
    d["coastal_pop_buffered"] = (d.coastal_pop_exposed * d.att_total).round(0)

    prot = d.coastal_pop_buffered.sum()
    expo = d.coastal_pop_exposed.sum()
    log(f"  coastal RP100 exposure {expo:,.0f} people; "
        f"wave energy reaching {prot:,.0f} of them is moderated by existing mangrove/reef "
        f"({100*prot/max(expo,1):.0f}%)")

    # ---- restoration headroom: exposed, coastal, thin or missing mangrove ----
    restorable = has_coast & (d.coastal_pop_exposed > 0) & (d.mangrove_width_m < MANGROVE_RESTORE_TARGET_M)
    target_att = 1 - 0.5 ** (MANGROVE_RESTORE_TARGET_M / HALVING_WIDTH_M)
    gain = np.clip(target_att - att_mg, 0, None)
    d["mangrove_restore_ha"] = np.where(
        restorable,
        np.clip((MANGROVE_RESTORE_TARGET_M - d.mangrove_width_m), 0, None)
        * d.coast_len_m / 10000.0, 0).round(0)
    d["coastal_pop_gain"] = np.where(restorable,
                                     d.coastal_pop_exposed * gain * (1 - att_reef), 0).round(0)
    log(f"  restoration headroom: {int(restorable.sum())} cells, "
        f"{d.mangrove_restore_ha.sum():,.0f} ha, extending moderation to "
        f"{d.coastal_pop_gain.sum():,.0f} more exposed people")

    # ---- riverine: catchment prioritisation, not a discharge model ----
    ws = d.groupby("watershed", dropna=False)
    d["ws_flood_pop"] = ws.riv_rp100_pop.transform("sum")
    d["ws_forest_frac"] = ws.lc_tree.transform("mean").round(3)
    # position in the catchment: 1 = headwaters, 0 = outlet
    d["ws_elev_rank"] = ws.elev_mean.rank(pct=True).round(3)
    upper = d.ws_elev_rank > 0.5
    d["catchment_role"] = np.where(upper, "upper catchment", "lower catchment")

    # retention value: forested headwaters above a lot of exposed people
    d["riv_retention_value"] = np.where(
        upper, d.lc_tree.fillna(0) * np.log1p(d.ws_flood_pop), 0).round(2)
    # restoration priority: bare headwaters above a lot of exposed people
    d["riv_restore_priority"] = np.where(
        upper & (d.lc_tree.fillna(0) < 0.4),
        (0.4 - d.lc_tree.fillna(0)) * np.log1p(d.ws_flood_pop), 0).round(2)

    top = d.groupby("watershed").agg(
        flood_pop=("riv_rp100_pop", "sum"), forest=("lc_tree", "mean")).nlargest(6, "flood_pop")
    log("  catchments with most RP100 riverine exposure:")
    for w, r in top.iterrows():
        log(f"    {str(w)[:42]:42s} {r.flood_pop:>9,.0f} people   forest {100*r.forest:.0f}%")

    cols = ["h3", "coast_len_m", "mangrove_ha", "mangrove_width_m", "att_mangrove",
            "att_reef", "att_total", "coastal_pop_exposed", "coastal_pop_buffered",
            "mangrove_restore_ha", "coastal_pop_gain", "ws_flood_pop", "ws_forest_frac",
            "ws_elev_rank", "catchment_role", "riv_retention_value", "riv_restore_priority"]
    d[cols].to_csv(PROC / "grid_nbs.csv", index=False)
    log(f"  wrote grid_nbs.csv ({len(d)} rows)")


if __name__ == "__main__":
    main()
