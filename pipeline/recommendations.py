"""Two independent recommendations per Opportunity Area.

The first version gave each area a single label - Invest / Develop, Protect / Restore and so
on - which conflated two different questions and left readers unsure whether "develop" meant
building hotels or building up ecosystems. It also made the two mutually exclusive, when the
most valuable places in Panama are precisely those that need both: develop the visitor
infrastructure AND restore the mangrove in front of it.

Every area therefore now carries two separate, parallel recommendations:

  INFRASTRUCTURE  what physical tourism investment is appropriate here, and specifically what
                  kind - accommodation, access, visitor facilities, trails, marine facilities,
                  water and sanitation.

  NATURE          what ecosystem investment is appropriate here - protect, restore, or both -
                  and for which ecosystems.

They are computed independently from the same evidence and can take any combination.
"""

INFRA_LEVELS = {
    "develop": ("Develop new capacity",
                "Real attraction, workable access and little existing supply. New visitor "
                "infrastructure is the binding constraint."),
    "upgrade": ("Upgrade and diversify",
                "An established destination. The constraint is the quality, resilience and "
                "spread of what already exists, not its quantity."),
    "light": ("Low-impact access only",
              "The conservation case leads here. Visitor infrastructure should be modest and "
              "sited to give the protected asset an economic constituency."),
    "none": ("No new development",
             "Either nothing here is reachable at screening scale, or sensitivity is high "
             "enough that new construction should be steered elsewhere."),
}

NATURE_LEVELS = {
    "protect_restore": ("Protect and restore",
                        "Both intact ecosystems worth holding and degraded ground worth "
                        "bringing back."),
    "protect": ("Protect",
                "Functioning ecosystems whose main risk is loss. Protection is cheaper and "
                "more certain than restoration."),
    "restore": ("Restore",
                "The ecosystem belongs here and is degraded or missing."),
    "maintain": ("Maintain",
                 "No ecosystem-specific action zone is indicated at screening scale."),
}


def infrastructure(r, nodes):
    """Level plus a specific, data-derived list of what to build or upgrade."""
    n_nodes = len(nodes)
    feasible = float(getattr(r, "dev_feasible_share", 0) or 0)
    sensitivity = float(getattr(r, "sensitivity", 0) or 0)
    tdl = float(r.TDL)
    access_km = float(getattr(r, "dist_access_km", 99) or 99)
    mode = str(getattr(r, "access_mode", "road") or "road")

    if n_nodes == 0 or feasible < 0.2:
        level = "none"
    elif r.action == "MANAGE" or sensitivity >= 70:
        level = "light"
    elif r.action == "PROTECT":
        level = "light"
    elif tdl >= 45:
        level = "upgrade"
    else:
        level = "develop"

    acts = []

    # --- accommodation ---
    if level in ("develop", "upgrade"):
        if level == "develop":
            acts.append(("Accommodation",
                         f"Little to no mapped capacity across {n_nodes} viable "
                         f"site{'' if n_nodes == 1 else 's'} ({int(r.n_accommodation)} points "
                         f"recorded in the whole area). Small-scale lodging - guesthouses, "
                         f"eco-lodges, community-run rooms - sized to the site rather than "
                         f"resort-scale."))
        else:
            acts.append(("Accommodation",
                         f"{int(r.n_accommodation)} accommodation points already mapped. The "
                         f"need is quality, standards and spreading capacity to shoulder sites "
                         f"rather than adding volume at the core."))
    elif level == "light":
        acts.append(("Accommodation",
                     "Community-run or concession lodging at very small scale only, sited "
                     "outside sensitive habitat and tied to the protected-area management plan."))

    # --- access ---
    if mode == "boat or air":
        acts.append(("Access - pier, landing or airstrip",
                     f"Nearest access is maritime or air ({access_km:.1f} km). Pier and "
                     f"small-boat handling, safe landing and passenger shelter, or airstrip "
                     f"surface and terminal condition, are the entry constraint."))
    elif access_km > 3:
        acts.append(("Access - last-mile road",
                     f"The nearest road is {access_km:.1f} km away. Last-mile surfacing and "
                     f"wet-season resilience determine whether visitors arrive at all."))
    elif level in ("develop", "upgrade"):
        acts.append(("Access - road condition",
                     "Roads reach the sites; condition, drainage and signage are what limit "
                     "reliability in the wet season."))

    # --- visitor facilities ---
    if level != "none":
        na, nt = int(r.n_attraction), int(r.n_trail)
        acts.append(("Visitor facilities",
                     f"{na} attraction{'' if na == 1 else 's'} and {nt} named "
                     f"trail{'' if nt == 1 else 's'} mapped. Orientation, sanitation, shade, "
                     f"waste collection, signage and interpretation at the identified sites."))

    # --- trails ---
    tree = float(getattr(r, "tree_frac", 0) or 0)
    relief = float(getattr(r, "relief_m", 0) or 0)
    if level in ("develop", "upgrade", "light") and (tree > 0.35 or relief > 500):
        acts.append(("Trails and viewpoints",
                     f"Forest cover {tree*100:.0f}% and {relief:.0f} m of local relief with "
                     f"{int(r.n_trail)} named trail{'' if int(r.n_trail) == 1 else 's'} "
                     f"recorded. A designed trail network built "
                     f"to survive the wet season, with viewpoints and trailhead facilities."))

    # --- marine facilities ---
    shallow = float(getattr(r, "shallow_frac", 0) or 0)
    if shallow > 0.1 or int(r.n_dive_surf) > 0 or int(r.n_marina_port) > 0:
        acts.append(("Marine facilities",
                     f"{shallow*100:.0f}% of the area is shallow shelf with "
                     f"{int(r.n_dive_surf)} dive/surf operators and {int(r.n_marina_port)} "
                     f"marinas or landings. Mooring buoys to stop anchor damage, a dive and "
                     f"snorkel landing, and operator licensing and safety standards."))

    # --- utilities ---
    if level in ("develop", "upgrade") and float(r.population) > 2000:
        acts.append(("Water and sanitation",
                     f"About {int(r.population):,} residents plus visitors. Potable water and "
                     f"wastewater treatment are the standard the destination's own natural "
                     f"asset depends on - untreated discharge degrades exactly what people "
                     f"come to see."))
    if level == "upgrade":
        acts.append(("Solid waste and visitor management",
                     "Established visitor volumes need waste collection, carrying-capacity "
                     "limits at pinch points, and redistribution of demand to shoulder sites."))

    if level == "none":
        acts = [("No new development",
                 "No site in this area passes the access screen, or sensitivity is too high. "
                 "Any visitor activity should be run from existing settlements outside it.")]

    return {"level": level, "label": INFRA_LEVELS[level][0],
            "rationale": INFRA_LEVELS[level][1], "actions": acts}


def nature(r, zones):
    """Level plus the ecosystem-specific zones, split into protect and restore."""
    if not len(zones):
        return {"level": "maintain", "label": NATURE_LEVELS["maintain"][0],
                "rationale": NATURE_LEVELS["maintain"][1], "protect": [], "restore": [],
                "protect_ha": 0, "restore_ha": 0}

    prot = zones[zones.action == "protect"]
    rest = zones[zones.action == "restore"]
    if len(prot) and len(rest):
        level = "protect_restore"
    elif len(prot):
        level = "protect"
    else:
        level = "restore"

    def pack(df):
        return [{"ecosystem": z.ecosystem, "hectares": int(z.eco_ha),
                 "area_km2": float(z.area_km2), "rationale": z.rationale}
                for z in df.sort_values("eco_ha", ascending=False).itertuples()]

    return {"level": level, "label": NATURE_LEVELS[level][0],
            "rationale": NATURE_LEVELS[level][1],
            "protect": pack(prot), "restore": pack(rest),
            "protect_ha": int(prot.eco_ha.sum()) if len(prot) else 0,
            "restore_ha": int(rest.eco_ha.sum()) if len(rest) else 0}
