"""Indicative employment model for the Opportunity Areas.

THIS IS NOT A FORECAST. It is an order-of-magnitude translation of a stated, hypothetical
investment package into jobs, so that a reader can compare areas on the same basis and see
what scale of employment is in play. Every coefficient is a published or conventional
planning benchmark, stated as a RANGE, and every result is reported as a range.

What it cannot know: whether finance is available, whether land tenure permits development,
whether the labour force has the skills, what visitor demand will actually be, or whether
the package below is the right one. Those are exactly the questions the "further analysis"
section of each area asks for.

BENCHMARKS AND SOURCES
  jobs per hotel room            0.4-0.8 direct. Conventional mid-market accommodation
                                 staffing ratio for Latin America.
  food, retail and transport     0.25-0.5 additional direct jobs per room serving visitors.
  guiding and activities         1.5-4 jobs per developed natural asset (guiding, boat and
                                 dive operation, equipment, interpretation).
  ecosystem restoration          0.15-0.45 person-years per hectare. Derived from restoration
                                 costs of roughly US$2,500-6,000/ha in a Latin American
                                 setting (global median ~US$1,100/ha, Caribbean estimates
                                 far higher), a ~35% labour share, and ~US$5,000 per
                                 person-year including on-costs. Spread over a 5-year
                                 programme in the FTE figure.
  protected-area management      0.4-1.2 ranger, monitoring and interpretation posts per
                                 1,000 ha brought under active management.
  indirect and induced           1.7-2.4x direct. Consistent with WTTC's Panama total
                                 (~392,000 jobs, 2024) against a direct share of roughly 40%.

  Panama context for scale: WTTC put total travel and tourism employment at about 392,000
  jobs in 2024, roughly 19.5% of GDP.
"""

RANGES = {
    "rooms_per_node_new": (25, 60),     # a new nature-tourism node
    "rooms_per_node_upgrade": (8, 20),  # an established destination: upgrade, not expansion
    "jobs_per_room": (0.4, 0.8),
    "service_jobs_per_room": (0.25, 0.5),
    "guide_jobs_per_asset": (1.5, 4.0),
    "restoration_person_years_per_ha": (0.15, 0.45),
    "ranger_jobs_per_1000ha": (0.4, 1.2),
    "indirect_multiplier": (1.7, 2.4),
}
PROGRAMME_YEARS = 5


def _rng(key):
    return RANGES[key]


def estimate(action, n_nodes, n_natural_assets, restore_ha, protect_ha):
    """Return an indicative employment range for one Opportunity Area."""
    upgrade = action == "ADAPT"
    rooms_lo, rooms_hi = _rng("rooms_per_node_upgrade" if upgrade else "rooms_per_node_new")
    rooms = (n_nodes * rooms_lo, n_nodes * rooms_hi)

    jr = _rng("jobs_per_room")
    sr = _rng("service_jobs_per_room")
    ga = _rng("guide_jobs_per_asset")
    rp = _rng("restoration_person_years_per_ha")
    rg = _rng("ranger_jobs_per_1000ha")

    accom = (rooms[0] * jr[0], rooms[1] * jr[1])
    service = (rooms[0] * sr[0], rooms[1] * sr[1])
    guiding = (n_natural_assets * ga[0], n_natural_assets * ga[1])
    # restoration person-years spread across the programme -> FTE while it runs
    restoration = (restore_ha * rp[0] / PROGRAMME_YEARS,
                   restore_ha * rp[1] / PROGRAMME_YEARS)
    management = (protect_ha / 1000 * rg[0], protect_ha / 1000 * rg[1])

    direct_lo = accom[0] + service[0] + guiding[0] + restoration[0] + management[0]
    direct_hi = accom[1] + service[1] + guiding[1] + restoration[1] + management[1]
    im = _rng("indirect_multiplier")

    def r(x):
        """Round to a precision that does not pretend to know more than it does."""
        if x >= 1000:
            return int(round(x / 100) * 100)
        if x >= 100:
            return int(round(x / 10) * 10)
        return int(round(x / 5) * 5)

    return {
        "rooms": [r(rooms[0]), r(rooms[1])],
        "accommodation": [r(accom[0]), r(accom[1])],
        "services": [r(service[0]), r(service[1])],
        "guiding": [r(guiding[0]), r(guiding[1])],
        "restoration_fte": [r(restoration[0]), r(restoration[1])],
        "management": [r(management[0]), r(management[1])],
        "direct_total": [r(direct_lo), r(direct_hi)],
        "with_indirect": [r(direct_lo * im[0]), r(direct_hi * im[1])],
        "programme_years": PROGRAMME_YEARS,
        "restore_ha": int(round(restore_ha)),
        "protect_ha": int(round(protect_ha)),
    }
