"""Step 55 - compose an investment narrative for each Opportunity Area.

Every sentence below is generated from values actually computed for that area. Nothing is
hard-coded per place. Where a claim depends on an assumption (that mangrove and reef provide
coastal protection; that OSM density proxies tourism supply) the text says so.

The register aimed at is an early World Bank investment concept note: specific about place,
asset and action, explicit about what is not yet known.
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import PROC, WEB_DATA, log  # noqa: E402


def sfield(r, name: str) -> str:
    """Attribute as a clean string - pandas hands back NaN (a float) for empty text."""
    v = getattr(r, name, None)
    return "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v)


def pct(x):
    return f"{100*float(x):.0f}%"


def people(n):
    """Population to a sensible precision - false precision reads as false confidence."""
    n = float(n)
    if n >= 100_000:
        return f"{round(n / 10_000) * 10_000:,.0f}"
    if n >= 10_000:
        return f"{round(n / 1_000) * 1_000:,.0f}"
    if n >= 1_000:
        return f"{round(n / 100) * 100:,.0f}"
    return f"{round(n / 10) * 10:,.0f}"


def km2(frac, area):
    return float(frac) * float(area)


def listify(items, limit=4):
    items = [i for i in items if i][:limit]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def assets_of(r):
    return [a.strip() for a in sfield(r, "assets").split(";") if a.strip()]


def ecosystems(r):
    """Named ecosystem components present at a material level."""
    out = []
    a = r.area_km2
    if r.mangrove_frac > 0.005:
        out.append(("mangrove", f"mangrove ({km2(r.mangrove_frac, a):.0f} km²)"))
    if r.shallow_frac > 0.05:
        out.append(("reef", f"shallow shelf under 20 m ({km2(r.shallow_frac, a):.0f} km²)"))
    if r.tree_frac > 0.35:
        out.append(("forest", f"forest cover over {pct(r.tree_frac)} of the area"))
    if r.wetland_frac > 0.01:
        out.append(("wetland", f"herbaceous wetland ({km2(r.wetland_frac, a):.0f} km²)"))
    if r.relief_m > 700:
        out.append(("mountain", f"{r.relief_m:.0f} m of local relief, rising to {r.elev_max:.0f} m"))
    if r.n_beach >= 3:
        out.append(("beach", f"{int(r.n_beach)} mapped beaches"))
    return out


ECO_NOUN = {"mangrove": "mangrove", "reef": "shallow reef habitat", "forest": "forest",
            "wetland": "wetland", "mountain": "mountain terrain", "beach": "beaches"}


def eco_nouns(r):
    """Plain nouns for prose. The measured labels ("forest cover over 95% of the area")
    read fine in a list but not spliced into a sentence."""
    return [ECO_NOUN[k] for k, _ in ecosystems(r)]


def headline(r):
    eco = eco_nouns(r)
    place = r.name
    if r.action == "PROTECT":
        return (f"Close a protection gap around {place}: {listify(eco) or 'the natural asset base'} "
                f"here carry high biodiversity value, yet only {pct(r.pa_strict_frac)} of the area "
                f"sits under strict protection.")
    if r.action == "INVEST":
        return (f"Develop {place} as a nature-tourism destination: strong natural attraction "
                f"({r.NAV:.0f}/100) and workable access ({r.tt_gateway_h:.1f} h from a gateway) "
                f"against thin existing supply ({int(r.n_accommodation)} mapped accommodation points).")
    if r.action == "ADAPT":
        return (f"Strengthen the natural base of {place} \u2014 an established destination "
                f"({int(r.n_accommodation)} accommodation and {int(r.n_food_service)} food-service points) "
                f"whose ecosystems carry a measurable protective and attraction function.")
    return (f"Manage visitor pressure around {place}: biodiversity value of {r.BCV:.0f}/100 "
            f"with accessibility of {r.ACC:.0f}/100 makes this a place to steer development carefully.")


def why_here(r):
    b = []
    a = r.area_km2
    if r.NAV >= 60:
        b.append(f"Nature attraction score {r.NAV:.0f}/100 — top-tier natural draw at national screening scale.")
    if r.supply_gap >= 20:
        b.append(f"Attraction exceeds tourism supply by {r.supply_gap:.0f} points — a measured development gap.")
    if r.BCV >= 60:
        b.append(f"Biodiversity value {r.BCV:.0f}/100, with a mean of {int(r.gbif_species)} vertebrate "
                 f"species recorded per screening cell.")
    if r.protection_gap >= 45:
        b.append(f"Protection gap {r.protection_gap:.0f}/100: {pct(r.pa_frac)} of the area has some "
                 f"protected status but only {pct(r.pa_strict_frac)} is in a strict IUCN category (I–IV).")
    if r.RES >= 50:
        b.append(f"Resilience function {r.RES:.0f}/100 — ecosystems here sit between hazard and people "
                 f"or between slope and settlement.")
    if r.mangrove_frac > 0.01:
        b.append(f"Mangrove covers {km2(r.mangrove_frac, a):.0f} km² ({pct(r.mangrove_frac)} of the area).")
    if r.shallow_frac > 0.1:
        b.append(f"{pct(r.shallow_frac)} of the area is shallow shelf under 20 m — reef and seagrass-capable habitat.")
    if r.tt_gateway_h <= 3:
        b.append(f"Modelled travel time to the nearest tourism gateway is {r.tt_gateway_h:.1f} hours.")
    elif r.tt_gateway_h >= 6:
        b.append(f"Remote: {r.tt_gateway_h:.1f} hours modelled travel from the nearest gateway — "
                 f"access is the binding constraint.")
    if r.population > 5000:
        b.append(f"About {people(r.population)} people live inside the area \u2014 a local labour and enterprise base.")
    if r.is_comarca:
        b.append("The area intersects an indigenous comarca; any tourism development must be community-led.")
    return b


def natural_assets(r):
    eco = [label for _, label in ecosystems(r)]
    parts = []
    if eco:
        parts.append(f"The area's natural asset base comprises {listify(eco, 5)}.")
    pa = sfield(r, "pa_names")
    if pa:
        parts.append(f"It overlaps the protected area(s) {pa.replace('; ', ', ')}, "
                     f"covering {pct(r.pa_frac)} of the area.")
    named = assets_of(r)
    if named:
        parts.append(f"Named features mapped here include {listify(named, 6)}.")
    eco, ws = sfield(r, "ecoregion"), sfield(r, "watershed")
    if eco:
        parts.append(f"It sits predominantly in the {eco} ecoregion"
                     + (f", draining the {ws} basin." if ws else "."))
    return " ".join(parts)


def tourism_context(r):
    p = [f"OpenStreetMap records {int(r.n_accommodation)} accommodation points, "
         f"{int(r.n_food_service)} food-service points, {int(r.n_attraction)} attractions, "
         f"{int(r.n_trail)} named trails, {int(r.n_dive_surf)} dive/surf operators and "
         f"{int(r.n_marina_port)} marinas or ferry points."]
    p.append(f"Modelled travel time to the nearest tourism gateway is {r.tt_gateway_h:.1f} hours; "
             f"the accessibility score is {r.ACC:.0f}/100.")
    p.append("OSM density under-records places that receive few visitors, so a low count here is "
             "partly a symptom of low development rather than an independent measure of it.")
    return " ".join(p)


def resilience_text(r):
    kinds = dict(ecosystems(r))
    if "mangrove" in kinds or "reef" in kinds:
        return (f"Coastal ecosystems here — {listify([kinds.get('mangrove'), kinds.get('reef')])} — "
                f"sit between open water and low-lying settlement and tourism assets. On the screening "
                f"assumption that intact mangrove and reef attenuate wave energy and stabilise shorelines, "
                f"the area scores {r.RES:.0f}/100 for resilience function. This is a spatial coincidence "
                f"of ecosystem and exposure, not a modelled reduction in flood damage.")
    if r.tree_frac > 0.3:
        return (f"Forest covers {pct(r.tree_frac)} of the area across {r.relief_m:.0f} m of local relief in "
                f"the {sfield(r, 'watershed') or 'local'} basin. Maintaining that cover on slopes plausibly supports "
                f"infiltration, limits erosion and moderates runoff reaching downstream settlements and "
                f"tourism infrastructure. Resilience score {r.RES:.0f}/100. No hydrological modelling has "
                f"been undertaken.")
    return (f"Resilience function scores {r.RES:.0f}/100. The ecosystem-protection signal here is weak "
            f"relative to other candidate areas.")


def conservation_action(r):
    kinds = dict(ecosystems(r))
    acts = []
    if r.action in ("PROTECT", "MANAGE"):
        if "reef" in kinds or "mangrove" in kinds:
            acts.append("Assess the case for new or extended marine protection over the reef–mangrove "
                        "complex, including whether an existing coastal management category could be "
                        "upgraded rather than a new area declared.")
            acts.append("Where mangrove has been cleared, target replanting at the landward margin and "
                        "restore tidal connectivity before considering any engineered shoreline works.")
        if "forest" in kinds:
            acts.append("Consolidate forest protection on upper slopes and restore degraded margins, "
                        "prioritising continuity with existing protected land rather than isolated patches.")
        if r.pa_frac > 0.2 and r.pa_strict_frac < 0.2:
            acts.append("Review management effectiveness of the existing designation: much of this area "
                        "carries a permissive category that may not hold the values identified here.")
    if r.action == "ADAPT":
        if "mangrove" in kinds or "reef" in kinds:
            acts.append("Restore and protect the mangrove and reef fringe seaward of existing tourism "
                        "assets, and remove pressures — sediment, wastewater, anchor damage — that "
                        "degrade it.")
        acts.append("Bring wastewater and solid-waste management up to the standard the destination's "
                    "own natural asset depends on.")
        if r.tree_frac > 0.25:
            acts.append("Restore riparian and upper-catchment forest feeding the destination's water supply.")
    if r.action == "INVEST":
        acts.append("Establish the conservation baseline and zoning BEFORE visitor infrastructure is "
                    "sited, so that access is designed around sensitive habitat rather than retrofitted.")
        if "mangrove" in kinds or "reef" in kinds:
            acts.append("Protect the mangrove and shallow-water habitat that the proposed marine "
                        "activities would themselves depend on.")
    if not acts:
        acts.append("Maintain existing ecosystem extent and condition; no restoration priority is "
                    "indicated by the screening indicators.")
    return acts


def tourism_investment(r):
    kinds = dict(ecosystems(r))
    named = assets_of(r)
    inv = []
    if r.action == "INVEST":
        if "reef" in kinds or r.n_dive_surf > 0:
            inv.append("Snorkelling and diving access: mooring buoys to prevent anchor damage, a small "
                       "landing and briefing facility, operator licensing and safety standards.")
        if "beach" in kinds:
            inv.append("Managed beach access: parking set back from the dune line, sanitation, shade, "
                       "waste collection and signage.")
        if "forest" in kinds or "mountain" in kinds:
            inv.append("A designed trail network with viewpoints, interpretation and a trailhead facility, "
                       "built to a standard that survives the wet season.")
        if "mangrove" in kinds:
            inv.append("Low-impact mangrove access — boardwalk, kayak launch, guided boat routes — sited "
                       "to avoid nesting and nursery areas.")
        inv.append("Destination-level basics that currently constrain length of stay: potable water, "
                   "wastewater treatment, mobile coverage and last-mile road or pier condition.")
    elif r.action == "ADAPT":
        inv.append("Upgrade rather than expand: retrofit existing visitor infrastructure for resilience "
                   "and reduce the destination's own pressure on the asset that draws visitors.")
        inv.append("Visitor management — carrying capacity, timed access at pinch points, and "
                   "redistribution of demand to shoulder sites within the same destination.")
    elif r.action == "PROTECT":
        inv.append("Modest, carefully sited visitor access that gives the protected asset an economic "
                   "constituency: a visitor centre or ranger post, defined trails or moorings, and "
                   "concession arrangements that channel revenue to management.")
        inv.append("Support for local enterprises operating under the protected-area management plan "
                   "rather than outside it.")
    else:  # MANAGE
        inv.append("Direct new accommodation and construction to already-developed settlements at the "
                   "periphery, not into the sensitive core.")
        inv.append("Invest in the management capacity — rangers, monitoring, enforcement, permitting — "
                   "that a rising visitor trend will require.")
    if named:
        inv.append(f"Anchor points for any package: {listify(named, 5)}.")
    return inv


def jobs_text(r):
    kinds = dict(ecosystems(r))
    ch = []
    if "reef" in kinds or r.n_dive_surf > 0:
        ch.append("dive and snorkel guiding, boat operation and equipment servicing")
    if "forest" in kinds or "mountain" in kinds:
        ch.append("nature and birding guiding, trail construction and maintenance")
    if "mangrove" in kinds:
        ch.append("kayak and boat tours, and paid mangrove restoration and monitoring crews")
    if "beach" in kinds:
        ch.append("beach services, food and beverage, and small accommodation")
    if r.pa_frac > 0.2:
        ch.append("protected-area management, ranger and interpretation roles")
    ch.append("local food supply, crafts and transport into the visitor economy")
    txt = (f"With about {people(r.population)} residents inside the area and a local-opportunity score of "
           f"{r.JOBS:.0f}/100, the plausible employment channels are {listify(ch, 4)}.")
    if r.is_comarca:
        txt += (" Because the area intersects an indigenous comarca, the master plan's own requirement "
                "applies: development must be community-led, with free prior and informed consent and "
                "equitable, durable benefit sharing.")
    txt += (" No employment numbers are estimated. Converting these channels into jobs depends on "
            "skills, finance and tenure conditions this screening cannot observe.")
    return txt


def risks(r):
    out = []
    if r.action == "INVEST" and r.BCV >= 60:
        out.append("Development risk to the asset itself: biodiversity value here is high, so the "
                   "sequencing of protection before construction is not optional.")
    if r.sensitivity >= 70:
        out.append(f"High ecological sensitivity ({r.sensitivity:.0f}/100). Carrying capacity should be "
                   f"set before, not after, demand grows.")
    if r.tt_gateway_h >= 5:
        out.append(f"Access at {r.tt_gateway_h:.1f} hours from a gateway may cap realistic demand; "
                   f"improving access will itself increase pressure.")
    if r.is_comarca:
        out.append("Land tenure and governance in comarca territory require a distinct process; "
                   "conventional concession models may not apply.")
    if r.n_accommodation == 0 and r.action == "INVEST":
        out.append("No mapped accommodation at all — either a genuine greenfield or an OSM coverage gap. "
                   "Ground-truth before programming.")
    if r.pa_frac > 0.6:
        out.append("Most of the area is already designated; the binding constraint may be management "
                   "capacity and enforcement rather than legal status.")
    out.append("OSM-derived supply counts and GBIF-derived richness both carry recording bias; both "
               "should be validated locally before investment decisions.")
    return out


def further_analysis(r):
    out = ["Ground-truthing of tourism supply and visitor numbers, which no open dataset records reliably at this scale."]
    if r.mangrove_frac > 0.01 or r.shallow_frac > 0.05:
        out.append("Reef condition and mangrove health assessment — extent is mapped here, condition is not.")
        out.append("Coastal hazard overlay once the ~90 m flood hazard layers are available, to convert the "
                   "resilience proxy into an exposure-based estimate.")
    if r.tree_frac > 0.3:
        out.append("Catchment hydrology and erosion assessment to test the assumed watershed-protection benefit.")
    if r.action in ("PROTECT", "MANAGE"):
        out.append("Ecological, social, legal and stakeholder assessment before any protected-area "
                   "designation or boundary change is proposed. Nothing here constitutes a designation "
                   "recommendation.")
    if r.action == "INVEST":
        out.append("Demand assessment and site-level feasibility, including tenure, utilities and "
                   "environmental licensing.")
    out.append("Consultation with ATP, MiAmbiente and the relevant Comité de Gestión de Destino.")
    return out


def gov_text(r):
    if r.gov_relation == "reinforces":
        return (f"This area falls within the government's priority destination "
                f"\u201c{sfield(r, 'gov_dest')}\u201d ({pct(r.gov_share)} of the area). The analysis REINFORCES that "
                f"priority and points to the specific nature-based content of the investment.")
    if r.gov_relation == "refines":
        return (f"This area falls within the government's priority destination \u201c{sfield(r, 'gov_dest')}\u201d "
                f"({pct(r.gov_share)} of the area), but the analysis REFINES the emphasis: the binding "
                f"issue identified here is conservation, resilience or pressure management rather than "
                f"expansion of tourism supply.")
    if r.gov_relation == "partial":
        return (f"About {pct(r.gov_share)} of this area overlaps the government priority destination "
                f"\u201c{sfield(r, 'gov_dest')}\u201d. The analysis suggests the useful geography extends beyond the "
                f"destination as currently framed.")
    return ("This area lies OUTSIDE the ten priority destinations of the Plan Maestro 2025–2030. "
            "It is surfaced by the spatial analysis alone and would be a NEW candidate for "
            "consideration in tourism planning.")


def main() -> None:
    df = pd.read_csv(PROC / "opportunity_areas.csv")
    log(f"  composing narratives for {len(df)} areas")
    out = []
    for r in df.itertuples():
        out.append({
            "cluster_id": r.cluster_id, "rank": int(r.rank), "name": str(r.name),
            "action": r.action, "gov_relation": r.gov_relation,
            "gov_dest": sfield(r, "gov_dest") or None,
            "headline": headline(r),
            "why_here": why_here(r),
            "natural_assets": natural_assets(r),
            "tourism_context": tourism_context(r),
            "biodiversity": (
                f"A mean of {int(r.gbif_species)} vertebrate species have been recorded per screening "
                f"cell here, in the {sfield(r, 'ecoregion') or 'local'} ecoregion. "
                f"{pct(r.pa_frac)} of the area carries protected status and {pct(r.pa_strict_frac)} is "
                f"in a strict IUCN category. Biodiversity value scores {r.BCV:.0f}/100 and the "
                f"protection gap {r.protection_gap:.0f}/100."),
            "resilience": resilience_text(r),
            "conservation_action": conservation_action(r),
            "tourism_investment": tourism_investment(r),
            "jobs": jobs_text(r),
            "risks": risks(r),
            "further_analysis": further_analysis(r),
            "gov_alignment": gov_text(r),
        })
    payload = {"generated_from": "pipeline/55_narratives.py", "areas": out}
    # allow_nan=False is deliberate. Python's json.dumps emits bare NaN by default, which is
    # NOT valid JSON: the browser's fetch().json() throws and the whole narrative payload
    # silently fails to load, leaving every dossier blank. Fail loudly here instead.
    for p in (PROC / "narratives.json", WEB_DATA / "narratives.json"):
        p.write_text(json.dumps(payload, indent=1, ensure_ascii=False, allow_nan=False))
    log(f"  wrote narratives.json ({len(out)} areas)")


if __name__ == "__main__":
    main()
