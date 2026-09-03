"""Step 40 - translate indicators into recommendation types.

Four action types, following the NBS intervention hierarchy (protect what works before
restoring, restore before building new):

  PROTECT   Protect / Restore     high nature and biodiversity value with a protection gap
  INVEST    Invest / Develop      real attraction, workable access, little tourism supply yet
  ADAPT     Adapt / Strengthen    established destination whose nature base needs shoring up
  MANAGE    Manage / Avoid        sensitive, reachable places where pressure should be limited
  NONE      No strong basis       nothing here rises to a screening-level recommendation

WHY A FIFTH, EMPTY CLASS EXISTS
  Ranking four fits and taking the best forces every cell into a recommendation, including
  cells that are at the bottom of everything. That produced the worst output of the first
  version: cells with a nature-attraction score of 0, no population, no road and a modelled
  17-hour journey from the nearest gateway, deep in the Darien Gap, classified as
  "Invest / Develop" purely because that was their least-bad percentile. A class must now be
  QUALIFIED on absolute evidence before it can be ranked at all, and a cell that qualifies
  for nothing is reported as such.

WHY WEIGHTED GEOMETRIC MEANS RATHER THAN WEIGHTED SUMS
  An additive score lets a missing condition be bought back by the others. In a first pass
  this produced nonsense: because most of Panama has no mapped tourism supply at all, the
  term (100 - TDL) sat near 100 almost everywhere and handed every empty cell a free 24
  points of "Invest" fit - so cells with a nature-attraction score of 25 were being
  recommended for tourism development. Likewise "Manage / Avoid" was landing on remote
  Darien forest with an accessibility score of 7, where there is no visitor pressure to
  manage.

  A weighted geometric mean makes each factor NECESSARY: if attraction is low, no amount of
  accessibility or headroom rescues the score. Weights still sum to 1, so results stay on a
  0-100 scale and remain directly comparable.

These types are NOT mutually exclusive in reality - the most interesting places in Panama are
exactly those where "protect the reef" and "develop the snorkelling access" are the same
recommendation. So all four fits are kept, the strongest becomes primary, and any other
scoring above threshold is reported as secondary.
"""
import sys
from pathlib import Path

import h3
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import PROC, log  # noqa: E402

SECONDARY_PCTL = 75  # a non-primary action is reported if it ranks in the national top quartile

ACTIONS = {
    "PROTECT": "Protect / Restore",
    "INVEST": "Invest / Develop",
    "ADAPT": "Adapt / Strengthen",
    "MANAGE": "Manage / Avoid",
    "NONE": "No strong basis",
}

# Absolute evidence a cell must show before an action can even be considered for it.
# These are floors, not weights: they cannot be traded off against another indicator.
QUALIFY = {
    "INVEST":  "real natural attraction, workable access, and development feasibility",
    "PROTECT": "genuine biodiversity or resilience value to protect",
    "ADAPT":   "tourism supply that actually exists on the ground",
    "MANAGE":  "high sensitivity AND enough access for pressure to be real",
}
MIN_NAV_INVEST = 40
MIN_ACC_INVEST = 35
MIN_BCV_PROTECT = 40
MIN_TDL_ADAPT = 25
MIN_BCV_MANAGE = 45
MIN_ACC_MANAGE = 35


def geo(**terms: tuple[pd.Series, float]) -> pd.Series:
    """Weighted geometric mean of 0-100 series. Weights must sum to 1.

    Values are floored at 1 rather than 0: a true zero would annihilate the whole score,
    and at screening resolution "none recorded" is rarely the same as "none exists".
    """
    total_w = sum(w for _, w in terms.values())
    assert abs(total_w - 1.0) < 1e-9, f"weights sum to {total_w}, not 1"
    acc = 0.0
    for series, w in terms.values():
        acc = acc + w * np.log(np.clip(series.astype(float), 1, 100))
    return pd.Series(np.exp(acc), index=next(iter(terms.values()))[0].index)


def main() -> None:
    d = pd.read_csv(PROC / "grid_indicators.csv").copy()
    feas = pd.read_csv(PROC / "grid_feasibility.csv")
    d = d.merge(feas, on="h3", how="left")
    d["dev_feasible"] = d.dev_feasible.fillna(0).astype(int)
    log(f"  {len(d)} cells, {int(d.dev_feasible.sum())} development-feasible")

    NAV, TDL, ACC = d.NAV, d.TDL, d.ACC
    BCV, RES, JOBS = d.BCV, d.RES, d.JOBS
    pa_strict = d.pa_strict_frac.fillna(0) * 100
    pa_any = d.pa_frac.fillna(0) * 100

    # ---- sensitivity: how much should we hesitate before recommending construction? ----
    sensitivity = (0.6 * BCV + 0.4 * pa_strict).round(1)
    damp = 1 - 0.5 * np.clip((sensitivity - 70) / 30, 0, 1)

    # ---- derived diagnostics ----
    protection_headroom = np.clip(100 - pa_strict, 1, 100)          # value not yet strictly held
    supply_headroom = np.clip(100 - TDL, 1, 100)                    # room to add supply
    conservation_value = np.maximum(NAV, RES)
    # pressure: outstanding biodiversity that is genuinely reachable
    pressure = 100 * np.clip((BCV - 50) / 50, 0, 1) * np.clip((ACC - 35) / 65, 0, 1)

    new_cols = {
        "sensitivity": sensitivity,
        "protection_gap": (conservation_value * protection_headroom / 100).round(1),
        "supply_gap": np.clip(NAV - TDL, 0, None).round(1),
        "pressure": pressure.round(1),
        # ---- fit scores --------------------------------------------------------------
        # INVEST: attraction is necessary; access, headroom and local capacity modulate it.
        "fit_invest": (geo(a=(NAV, .40), b=(ACC, .25), c=(supply_headroom, .20),
                           d=(JOBS, .15)) * damp).round(1),
        # PROTECT: biodiversity value is necessary, and it must not already be strictly held.
        "fit_protect": geo(a=(BCV, .40), b=(protection_headroom, .28),
                           c=(conservation_value, .22), d=(JOBS, .10)).round(1),
        # ADAPT: only meaningful where tourism supply actually exists.
        "fit_adapt": geo(a=(TDL, .40), b=(RES, .28), c=(BCV, .20), d=(ACC, .12)).round(1),
        # MANAGE: sensitivity AND reachability - there is no pressure to manage in the roadless Darien.
        "fit_manage": geo(a=(BCV, .38), b=(sensitivity, .30), c=(ACC, .22),
                          d=(pressure, .10)).round(1),
    }
    d = pd.concat([d, pd.DataFrame(new_cols, index=d.index)], axis=1)

    # ---- spatially smooth the fit scores before comparing them ----------------------
    # Recommendations are regional, not per-hexagon: a destination, a reef system or a
    # catchment spans several 37 km2 cells. Ranking raw per-cell fits produced a
    # salt-and-pepper map where neighbouring cells flipped between classes for trivial
    # differences. Blending each cell with a discounted share of its immediate neighbours
    # yields coherent regions without moving any cell far from its own evidence.
    cells = d.h3.tolist()
    pos = {h: i for i, h in enumerate(cells)}
    for col in ["fit_invest", "fit_protect", "fit_adapt", "fit_manage"]:
        v = d[col].to_numpy(dtype=float)
        out = np.empty_like(v)
        for i, h in enumerate(cells):
            acc, wsum = v[i], 1.0
            for nb in h3.grid_disk(h, 1):
                j = pos.get(nb)
                if j is not None and j != i:
                    acc += 0.40 * v[j]
                    wsum += 0.40
            out[i] = acc / wsum
        d[col] = np.round(out, 1)

    # ---- compare the four fits by PERCENTILE RANK, not raw value --------------------
    # The four scores do not share a natural scale: protection headroom is high almost
    # everywhere in Panama, so fit_protect sits structurally above fit_invest and a raw
    # argmax labelled 69% of the country "Protect". Ranking each fit against its own
    # national distribution asks the right question - is this cell more exceptional as a
    # protection case than as a development case? - and yields a balanced, comparable read.
    fits = d[["fit_protect", "fit_invest", "fit_adapt", "fit_manage"]]
    keys = ["PROTECT", "INVEST", "ADAPT", "MANAGE"]
    pct = fits.rank(pct=True) * 100
    pct.columns = [f"pct_{c}" for c in fits.columns]
    d = pd.concat([d, pct.round(1)], axis=1)

    # ---- absolute qualification gates -----------------------------------------------
    qual = pd.DataFrame({
        "PROTECT": BCV >= MIN_BCV_PROTECT,
        "INVEST": (d.dev_feasible == 1) & (NAV >= MIN_NAV_INVEST) & (ACC >= MIN_ACC_INVEST),
        "ADAPT": TDL >= MIN_TDL_ADAPT,
        "MANAGE": (BCV >= MIN_BCV_MANAGE) & (ACC >= MIN_ACC_MANAGE),
    })
    log("  cells qualifying for each action (absolute gates):")
    for k in keys:
        log(f"    {ACTIONS[k]:22s} {int(qual[k].sum()):5d}")

    masked = pct.copy()
    masked.columns = keys
    masked = masked.where(qual, other=-1.0)

    primary, sec = [], []
    for i in range(len(d)):
        row = masked.iloc[i]
        if (row < 0).all():
            primary.append("NONE")
            sec.append("")
            continue
        best = row.idxmax()
        primary.append(best)
        sec.append("; ".join(k for k in keys if k != best and row[k] >= 75))

    d = pd.concat([d, pd.DataFrame({
        "primary": primary,
        "primary_fit": np.where(np.array(primary) == "NONE", 0.0,
                                [fits.iloc[i][f"fit_{p.lower()}"] if p != "NONE" else 0.0
                                 for i, p in enumerate(primary)]),
        "primary_rank": masked.max(axis=1).clip(lower=0).round(1),
        "primary_label": [ACTIONS[p] for p in primary],
        "secondary": sec,
        "in_gov_dest": d.gov_dest.notna().astype(int).values,
    }, index=d.index)], axis=1)

    log("  primary class distribution:")
    for k, n in d.primary.value_counts().items():
        log(f"    {ACTIONS[k]:22s} {n:5d} ({100*n/len(d):4.1f}%)")

    log("  mean indicator profile by primary class:")
    prof = d.groupby("primary")[["NAV", "TDL", "ACC", "BCV", "RES", "JOBS",
                                 "sensitivity", "primary_fit", "primary_rank"]].mean().round(1)
    for line in prof.to_string().split("\n"):
        log("    " + line)

    log(f"  cells inside a government priority destination: {int(d.in_gov_dest.sum())}")
    inv = d[d.primary == "INVEST"]
    log(f"  INVEST sanity: max travel time {inv.tt_gateway_h.max():.1f} h, "
        f"max access distance {inv.dist_access_km.max():.1f} km "
        f"({int((inv.access_mode == 'boat or air').sum())} reached by boat/air), "
        f"advisory-zone cells {int(inv.advisory_zone.sum())} (must be 0)")
    d.to_csv(PROC / "grid_classified.csv", index=False)
    log(f"  wrote grid_classified.csv ({d.shape[0]} rows, {d.shape[1]} cols)")


if __name__ == "__main__":
    main()
