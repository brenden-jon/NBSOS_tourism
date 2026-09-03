"""Step 30 - build the six indicator families.

Design principle: NO single opaque composite. Six named families are computed from named
sub-indicators, every one of which is kept on the cell so the application can show a user
exactly why a place scores as it does.

Normalisation is percentile rank (0-100) computed over the cells where the sub-indicator is
meaningful. Percentile rank is used rather than min-max because almost every count variable
here is heavily right-skewed (Panama City has two orders of magnitude more hotels than
anywhere else) and min-max would flatten the rest of the country to zero.

Zone handling: a marine cell has no forest and an inland cell has no reef. Rather than
scoring absent things as zero - which would systematically punish whole zones - each family
declares which sub-indicators apply in which zone and re-normalises the weights over the
applicable set.
"""
import sys
from pathlib import Path

import geopandas as gpd
import h3
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import PROC, log  # noqa: E402

LAND_ZONES = {"inland", "coastal"}
SEA_ZONES = {"marine", "nearshore"}


PRESENCE_FLOOR = 15.0


def prank(s: pd.Series, mask: pd.Series | None = None,
          floor: float = PRESENCE_FLOOR) -> pd.Series:
    """Percentile rank to 0-100, computed over `mask` rows and over non-zero values only.

    Two decisions matter here and both were made deliberately:

    1. True zeros are pinned to 0 rather than given the mid-rank of the tied zero block.
       Most of Panama has no mapped hotel and no mangrove; ranking across all cells would
       hand every empty cell the median of a huge tie and inflate emptiness into a score.

    2. Non-zero values are mapped onto [floor, 100], not [0, 100]. PRESENCE ITSELF IS
       INFORMATION: a cell with one hotel is categorically different from a cell with none,
       and should not score ~0.2 merely because 400 other cells also have hotels. Without
       this floor the tourism-development family collapses - p90 lands near 3/100 - and the
       development gap term (100 - TDL) stops discriminating entirely.
    """
    out = pd.Series(0.0, index=s.index)
    m = pd.Series(True, index=s.index) if mask is None else mask.fillna(False)
    v = s.where(m)
    pos = m & v.notna() & (v > 0)
    if pos.sum() > 1:
        out[pos] = floor + (100.0 - floor) * v[pos].rank(pct=True)
    elif pos.sum() == 1:
        out[pos] = 100.0
    return out.round(1)


def logn(s: pd.Series) -> pd.Series:
    return np.log1p(s.fillna(0).clip(lower=0))


def ring_smooth(values: pd.Series, cells: list[str], ring_weight: float = 0.5) -> pd.Series:
    """Own value plus a discounted share of the immediate H3 neighbours.

    At 37 km2 a destination does not stop at a cell boundary. Bocas town and the water it
    sends boats onto are different cells; a dive operator sits on land while the reef it
    visits is offshore. Without this, 90% of cells register zero tourism development and
    marine cells register almost no natural attraction - both artefacts of the tessellation
    rather than facts about Panama.
    """
    idx = {h: i for i, h in enumerate(cells)}
    v = values.fillna(0).to_numpy(dtype=float)
    out = v.copy()
    for i, h in enumerate(cells):
        acc = 0.0
        for nb in h3.grid_disk(h, 1):
            if nb == h:
                continue
            j = idx.get(nb)
            if j is not None:
                acc += v[j]
        out[i] += ring_weight * acc
    return pd.Series(out, index=values.index)


def weighted(df: pd.DataFrame, spec: dict[str, float], applies: pd.Series) -> pd.Series:
    """Weighted mean of sub-indicators, renormalising weights over applicable rows."""
    num = pd.Series(0.0, index=df.index)
    den = pd.Series(0.0, index=df.index)
    for col, w in spec.items():
        ok = applies if isinstance(applies, pd.Series) else pd.Series(True, index=df.index)
        num += df[col].fillna(0) * w * ok
        den += w * ok
    return (num / den.replace(0, np.nan)).fillna(0).round(1)


def main() -> None:
    grid = gpd.read_file("data/processed/grid.geojson")
    r = pd.read_csv(PROC / "grid_rasters.csv")
    v = pd.read_csv(PROC / "grid_vectors.csv")
    a = pd.read_csv(PROC / "grid_access.csv")
    gb_path = PROC / "grid_gbif.csv"
    d = grid.drop(columns="geometry").merge(r, on="h3").merge(v, on="h3").merge(a, on="h3")
    if gb_path.exists():
        d = d.merge(pd.read_csv(gb_path), on="h3", how="left")
    else:
        log("  !! grid_gbif.csv missing - biodiversity richness will be zero")
        d["gbif_species"] = 0
        d["gbif_records"] = 0
    for c in ["gbif_species", "gbif_records"]:
        d[c] = d[c].fillna(0)
    n_cols = [c for c in d.columns if c.startswith("n_")]
    for c in n_cols:
        d[c] = d[c].fillna(0)
    log(f"  {len(d)} cells, {len(d.columns)} raw columns")

    is_land = d.zone.isin(LAND_ZONES)
    is_sea = d.zone.isin(SEA_ZONES)
    is_coastal = d.zone.isin({"coastal", "nearshore"})

    # ------------------------------------------------------------------ #
    # sub-indicators
    # ------------------------------------------------------------------ #
    # -- ecosystems
    d["s_forest"] = prank(d.lc_tree, is_land)
    d["s_mangrove"] = prank(d.lc_mangrove)
    d["s_wetland"] = prank(d.lc_wetland)
    d["s_shallow"] = prank(d.shallow_frac)
    d["s_relief"] = prank(d.relief_m, is_land)

    # -- named natural attractions people actually visit (OSM), smoothed over the 1-ring
    cells = d.h3.tolist()
    d["nat_features"] = d[["n_beach", "n_waterfall", "n_peak", "n_viewpoint",
                           "n_reef_natural", "n_hotspring"]].sum(axis=1)
    d["nat_features_nb"] = ring_smooth(d.nat_features, cells)
    d["beach_nb"] = ring_smooth(d.n_beach, cells)
    d["s_nat_features"] = prank(logn(d.nat_features_nb))
    d["s_beach"] = prank(logn(d.beach_nb))
    # protective / shelf habitat also reads across the shoreline
    d["s_shallow_nb"] = prank(ring_smooth(d.shallow_frac, cells))
    d["s_mangrove_nb"] = prank(ring_smooth(d.lc_mangrove, cells))

    # -- protection as an attraction (national parks draw visitors) and as conservation
    iucn_w = d.pa_strict_frac.fillna(0) * 1.0 + (d.pa_frac.fillna(0) - d.pa_strict_frac.fillna(0)) * 0.5
    d["s_pa_attract"] = prank(iucn_w)
    d["s_pa_cover"] = prank(d.pa_frac)
    d["s_ramsar"] = prank(d.ramsar_frac)

    # -- wildlife
    d["s_species"] = prank(d.gbif_species)
    d["s_records"] = prank(logn(d.gbif_records))

    # -- ecoregion / life-zone rarity: rarer contexts carry more conservation weight
    for src, dst in [("ecoregion", "s_eco_rare"), ("lifezone", "s_lz_rare")]:
        share = d[src].map(d[src].value_counts(normalize=True))
        d[dst] = prank(-np.log(share.fillna(1.0)))

    # -- tourism supply, smoothed: a destination's supply serves its surroundings
    d["accom_nb"] = ring_smooth(d.n_accommodation, cells)
    d["food_nb"] = ring_smooth(d.n_food_service, cells)
    d["infra_nb"] = ring_smooth(d.n_attraction + d.n_visitor_infra + d.n_viewpoint, cells)
    d["trail_nb"] = ring_smooth(d.n_trail, cells)
    d["marine_ops_nb"] = ring_smooth(d.n_dive_surf + d.n_marina_port, cells)
    d["airport_nb"] = ring_smooth(d.n_airport, cells)
    d["s_accom"] = prank(logn(d.accom_nb))
    d["s_food"] = prank(logn(d.food_nb))
    d["s_attract_infra"] = prank(logn(d.infra_nb))
    d["s_trails"] = prank(logn(d.trail_nb))
    d["s_marine_ops"] = prank(logn(d.marine_ops_nb))
    d["s_airport"] = prank(logn(d.airport_nb))

    # -- accessibility (inverted: quicker = higher)
    d["s_access_gw"] = 100 - prank(logn(d.tt_gateway_h), pd.Series(True, index=d.index))
    d["s_access_cap"] = 100 - prank(logn(d.tt_capital_h), pd.Series(True, index=d.index))

    # -- people
    d["s_pop"] = prank(logn(d.population))

    # ------------------------------------------------------------------ #
    # NAV - Nature Attraction Value
    # ------------------------------------------------------------------ #
    land_nav = {"s_forest": .18, "s_relief": .15, "s_nat_features": .22,
                "s_pa_attract": .13, "s_species": .17, "s_mangrove": .07, "s_beach": .08}
    sea_nav = {"s_shallow_nb": .30, "s_mangrove_nb": .16, "s_nat_features": .16,
               "s_pa_attract": .14, "s_beach": .12, "s_marine_ops": .12}
    d["NAV"] = np.where(is_land,
                        weighted(d, land_nav, pd.Series(True, index=d.index)),
                        weighted(d, sea_nav, pd.Series(True, index=d.index)))
    d["NAV"] = d["NAV"].round(1)

    # ------------------------------------------------------------------ #
    # TDL - Tourism Development Level (what is already built)
    # ------------------------------------------------------------------ #
    d["TDL"] = weighted(d, {"s_accom": .34, "s_food": .22, "s_attract_infra": .18,
                            "s_trails": .10, "s_marine_ops": .10, "s_airport": .06},
                        pd.Series(True, index=d.index))

    # ------------------------------------------------------------------ #
    # ACC - Accessibility
    # ------------------------------------------------------------------ #
    d["ACC"] = weighted(d, {"s_access_gw": .65, "s_access_cap": .35},
                        pd.Series(True, index=d.index))

    # ------------------------------------------------------------------ #
    # BCV - Biodiversity & Conservation Value
    # ------------------------------------------------------------------ #
    land_bcv = {"s_species": .26, "s_forest": .22, "s_eco_rare": .14, "s_lz_rare": .10,
                "s_pa_cover": .10, "s_mangrove": .10, "s_ramsar": .08}
    sea_bcv = {"s_shallow_nb": .26, "s_mangrove_nb": .20, "s_species": .18, "s_pa_cover": .14,
               "s_ramsar": .12, "s_eco_rare": .10}
    d["BCV"] = np.where(is_land,
                        weighted(d, land_bcv, pd.Series(True, index=d.index)),
                        weighted(d, sea_bcv, pd.Series(True, index=d.index)))
    d["BCV"] = d["BCV"].round(1)

    # ------------------------------------------------------------------ #
    # RES - screening-level resilience contribution of nature
    #   Coastal: protective ecosystems in front of low-lying people and tourism assets.
    #   Inland : catchment tree cover on slopes above people and tourism assets downstream.
    # NOT a hazard model. No avoided damages are implied. See docs/limitations.md.
    # ------------------------------------------------------------------ #
    idx = {h: i for i, h in enumerate(d.h3)}
    assets = (d.population.fillna(0) / 1000.0
              + d.n_accommodation.fillna(0) * 2.0 + d.n_food_service.fillna(0))
    low_lying = (d.elev_mean.fillna(999) < 10).astype(float)

    # exposure behind each cell: assets in the cell and its 2-ring neighbourhood that are low-lying
    exposure = np.zeros(len(d))
    for i, h in enumerate(d.h3):
        ring = h3.grid_disk(h, 2)
        tot = 0.0
        for nb in ring:
            j = idx.get(nb)
            if j is not None:
                tot += assets.iloc[j] * low_lying.iloc[j]
        exposure[i] = tot
    d["coastal_exposure"] = np.round(exposure, 2)
    d["s_coastal_exposure"] = prank(pd.Series(exposure, index=d.index), is_coastal)
    protective = (d.lc_mangrove.fillna(0) * 2.0 + d.shallow_frac.fillna(0)
                  + d.lc_wetland.fillna(0))
    d["s_protective_eco"] = prank(protective, is_coastal)
    res_coastal = np.sqrt(d.s_protective_eco.clip(lower=0) * d.s_coastal_exposure.clip(lower=0))

    # inland: exposure downstream within the same watershed (lower mean elevation)
    ws_assets = d.assign(a=assets).groupby("watershed")["a"].transform("sum")
    ws_rank = d.groupby("watershed")["elev_mean"].rank(pct=True)
    d["s_upper_catchment"] = prank(ws_rank.fillna(0.5) * d.lc_tree.fillna(0), is_land)
    d["s_ws_exposure"] = prank(logn(ws_assets), is_land)
    res_inland = np.sqrt(d.s_upper_catchment.clip(lower=0) * d.s_ws_exposure.clip(lower=0))

    d["RES"] = np.where(is_coastal, np.fmax(res_coastal, res_inland * 0.7),
                        np.where(is_land, res_inland, res_coastal)).round(1)

    # ------------------------------------------------------------------ #
    # JOBS - local economic opportunity from nature tourism
    #   Not a jobs forecast. A qualitative lens: is there a local workforce and community
    #   base that could capture tourism value, and would investment here advance the
    #   government's own decentralisation objective?
    # ------------------------------------------------------------------ #
    pop_nb = np.zeros(len(d))
    for i, h in enumerate(d.h3):
        for nb in h3.grid_disk(h, 1):
            j = idx.get(nb)
            if j is not None:
                pop_nb[i] += d.population.fillna(0).iloc[j]
    d["pop_neighbourhood"] = np.round(pop_nb, 0)
    d["s_labour"] = prank(logn(pd.Series(pop_nb, index=d.index)))
    d["is_comarca"] = d.province.astype(str).str.contains("Comarca", na=False).astype(int)
    d["s_comarca"] = d.is_comarca * 100.0
    # decentralisation: distance from the Panama City metro concentration
    d["s_decentral"] = prank(logn(d.tt_capital_h))
    d["JOBS"] = weighted(d, {"s_labour": .40, "s_decentral": .25,
                             "s_comarca": .15, "s_access_gw": .20},
                         pd.Series(True, index=d.index))

    fam = ["NAV", "TDL", "ACC", "BCV", "RES", "JOBS"]
    log("  indicator families (mean / p90 / max):")
    for f in fam:
        log(f"    {f:5s} {d[f].mean():6.1f} {d[f].quantile(.9):6.1f} {d[f].max():6.1f}")

    d.to_csv(PROC / "grid_indicators.csv", index=False)
    log(f"  wrote grid_indicators.csv ({d.shape[0]} rows, {d.shape[1]} cols)")


if __name__ == "__main__":
    main()
