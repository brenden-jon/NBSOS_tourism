"""Step 11 - fetch OpenStreetMap tourism, nature-asset and transport features for Panama.

OSM is volunteered data: coverage is uneven and biased toward places that already receive
visitors. That bias is analytically useful here (it proxies *current* tourism development)
but it must never be read as an inventory of what exists. See docs/limitations.md.
"""
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point

sys.path.insert(0, str(Path(__file__).parent))
from common import CRS_WGS, log, overpass, save_geojson  # noqa: E402

AREA = 'area["ISO3166-1"="PA"][admin_level=2]->.pa;'

# Thematic POI queries. `out center` gives ways/relations a representative point.
POI_QUERIES = {
    "accommodation": '''
      nwr["tourism"~"^(hotel|guest_house|hostel|motel|resort|apartment|chalet|camp_site|alpine_hut)$"](area.pa);
    ''',
    "attraction": '''
      nwr["tourism"~"^(attraction|museum|zoo|aquarium|theme_park|gallery|artwork)$"](area.pa);
      nwr["historic"~"^(fort|castle|ruins|archaeological_site|monument)$"](area.pa);
    ''',
    "viewpoint": '''
      nwr["tourism"="viewpoint"](area.pa);
    ''',
    "visitor_infra": '''
      nwr["tourism"~"^(information|picnic_site|camp_pitch)$"](area.pa);
    ''',
    "beach": '''
      nwr["natural"="beach"](area.pa);
      nwr["leisure"="beach_resort"](area.pa);
    ''',
    "waterfall": '''
      nwr["waterway"="waterfall"](area.pa);
      nwr["natural"="waterfall"](area.pa);
    ''',
    "peak": '''
      node["natural"="peak"](area.pa);
      node["natural"="volcano"](area.pa);
    ''',
    "hotspring": '''
      nwr["natural"="hot_spring"](area.pa);
      nwr["amenity"="public_bath"]["bath:type"="hot_spring"](area.pa);
    ''',
    "dive_surf": '''
      nwr["sport"~"scuba_diving|surfing"](area.pa);
      nwr["amenity"="dive_centre"](area.pa);
      nwr["shop"="scuba_diving"](area.pa);
    ''',
    "marina_port": '''
      nwr["leisure"="marina"](area.pa);
      nwr["amenity"="ferry_terminal"](area.pa);
      nwr["harbour"="yes"](area.pa);
    ''',
    "airport": '''
      nwr["aeroway"="aerodrome"](area.pa);
    ''',
    "food_service": '''
      node["amenity"~"^(restaurant|cafe|bar|pub)$"](area.pa);
      way["amenity"~"^(restaurant|cafe|bar|pub)$"](area.pa);
    ''',
    "reef_natural": '''
      nwr["natural"="reef"](area.pa);
    ''',
}

TRAIL_QUERY = '''
  nwr["route"="hiking"](area.pa);
  way["highway"~"^(path|footway|track)$"]["name"](area.pa);
'''

ROAD_QUERY = '''
  way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|motorway_link|trunk_link|primary_link|secondary_link)$"](area.pa);
'''


def q(body: str, out: str = "out center tags;") -> str:
    return f"[out:json][timeout:600];{AREA}({body});{out}"


def elements_to_points(data: dict, theme: str) -> gpd.GeoDataFrame:
    rows = []
    for el in data.get("elements", []):
        if el.get("type") == "node":
            lon, lat = el.get("lon"), el.get("lat")
        else:
            c = el.get("center") or {}
            lon, lat = c.get("lon"), c.get("lat")
        if lon is None or lat is None:
            continue
        tags = el.get("tags", {}) or {}
        rows.append({
            "osm_id": f"{el['type'][0]}{el['id']}",
            "theme": theme,
            "name": tags.get("name"),
            "kind": (tags.get("tourism") or tags.get("natural") or tags.get("historic")
                     or tags.get("leisure") or tags.get("amenity") or tags.get("aeroway")
                     or tags.get("sport") or tags.get("waterway") or tags.get("shop")),
            "geometry": Point(lon, lat),
        })
    return gpd.GeoDataFrame(rows, crs=CRS_WGS)


def main() -> None:
    log("Fetching OSM POIs via Overpass")
    frames = []
    for theme, body in POI_QUERIES.items():
        data = overpass(q(body), cache=f"osm_{theme}")
        gdf = elements_to_points(data, theme)
        log(f"  {theme}: {len(gdf)}")
        if len(gdf):
            frames.append(gdf)
    pois = gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs=CRS_WGS)
    pois = pois.drop_duplicates(subset=["osm_id"])
    log(f"  TOTAL POIs: {len(pois)}")
    save_geojson(pois, "osm_pois", decimals=5)

    # Trails - keep as points (representative centre) for density scoring
    log("Fetching OSM trails")
    tdata = overpass(q(TRAIL_QUERY), cache="osm_trails")
    trails = elements_to_points(tdata, "trail")
    log(f"  trails: {len(trails)}")
    save_geojson(trails, "osm_trails", decimals=5)

    # Roads - full geometry needed to build the accessibility friction surface
    log("Fetching OSM road network (geometry)")
    rdata = overpass(q(ROAD_QUERY, out="out geom;"), cache="osm_roads")
    rows = []
    for el in rdata.get("elements", []):
        geom = el.get("geometry")
        if not geom or len(geom) < 2:
            continue
        tags = el.get("tags", {}) or {}
        rows.append({
            "osm_id": f"w{el['id']}",
            "highway": tags.get("highway"),
            "surface": tags.get("surface"),
            "geometry": LineString([(p["lon"], p["lat"]) for p in geom]),
        })
    roads = gpd.GeoDataFrame(rows, crs=CRS_WGS)
    log(f"  roads: {len(roads)} ways")
    save_geojson(roads, "osm_roads", decimals=5)


if __name__ == "__main__":
    main()
