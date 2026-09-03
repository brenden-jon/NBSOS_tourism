"""Step 10 - fetch authoritative Panama national layers from the STRI GIS Portal.

STRI (Smithsonian Tropical Research Institute) republishes the official MiAmbiente /
IGNTG national layers as open ArcGIS FeatureServices. These are preferred over global
datasets (e.g. WDPA) because they are the national source of record for Panama.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import CRS_M, arcgis_layer, log, save_geojson  # noqa: E402

LAYERS = {
    "provinces":       ("Panama_Province_Boundaries_2024", 0),
    "districts":       ("Panama_Distritos_Boundaries_2024", 0),
    "corregimientos":  ("Panama_Corregimientos_Boundaries_2024", 0),
    "protected_areas": ("Panama_AP_2025", 0),
    "watersheds":      ("Watersheds_Panama_2022", 0),
    "streams":         ("Panama_Detailed_Stream_Network_2022", 0),
    "places":          ("Populated_Places_Points_Panama", 0),
    "ecoregions":      ("Ecorregiones_Terrestres_de_Panam%C3%A1", 0),
    "lifezones":       ("Holdridge_Life_Zones", 0),
    "lakes":           ("Lakes_and_Reservoirs_from_Panama_2024", 0),
}


def main() -> None:
    log("Fetching national layers from STRI GIS Portal")
    for name, (service, layer) in LAYERS.items():
        try:
            gdf = arcgis_layer(service, layer, cache=f"stri_{name}")
            gdf = gdf[~gdf.geometry.isna()].copy()
            # repair any invalid rings before downstream overlays
            gdf["geometry"] = gdf.geometry.make_valid()
            log(f"  {name}: {len(gdf)} features, geom={gdf.geom_type.unique().tolist()}")
        except Exception as exc:  # noqa: BLE001
            log(f"  !! {name} FAILED: {exc}")

    # National land polygon (dissolve of provinces) - the coastline reference for the grid.
    prov = arcgis_layer(LAYERS["provinces"][0], cache="stri_provinces")
    prov["geometry"] = prov.geometry.make_valid()
    land = prov.to_crs(CRS_M).dissolve().reset_index(drop=True)
    land["geometry"] = land.geometry.buffer(0)
    area_km2 = float(land.geometry.area.iloc[0]) / 1e6
    log(f"  national land area: {area_km2:,.0f} km2 (reference ~75,420 km2)")
    save_geojson(land, "panama_land", decimals=5)


if __name__ == "__main__":
    main()
