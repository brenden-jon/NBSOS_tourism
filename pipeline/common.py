"""Shared helpers for the Panama Tourism-Nature Opportunity Scan pipeline."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import geopandas as gpd
import requests

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
WEB_DATA = ROOT / "web" / "public" / "data"
for _d in (RAW, PROC, WEB_DATA):
    _d.mkdir(parents=True, exist_ok=True)

# Panama analysis CRS: UTM 17N. All area / distance maths happen here.
CRS_M = "EPSG:32617"
CRS_WGS = "EPSG:4326"

UA = {"User-Agent": "NBSOS-Tourism-Panama/0.1 (World Bank prototype; geospatial research)"}

# STRI GIS Portal (Smithsonian Tropical Research Institute) republishes the official
# MiAmbiente / IGNTG national layers as ArcGIS FeatureServers.
STRI = "https://services2.arcgis.com/HRY6x8qt5qjGnAA9/arcgis/rest/services"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def get_json(url: str, params: dict | None = None, tries: int = 4, timeout: int = 120) -> dict:
    """GET with retries, returning parsed JSON."""
    last = None
    for attempt in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as exc:  # noqa: BLE001 - transient network issues are expected
            last = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"GET failed after {tries} tries: {url} :: {last}")


def arcgis_layer(service: str, layer: int = 0, where: str = "1=1",
                 out_fields: str = "*", cache: str | None = None) -> gpd.GeoDataFrame:
    """Download a whole ArcGIS FeatureServer layer as GeoDataFrame, paginating past maxRecordCount."""
    if cache:
        cpath = RAW / f"{cache}.geojson"
        if cpath.exists():
            log(f"  cache hit: {cache}")
            return gpd.read_file(cpath)

    base = f"{STRI}/{service}/FeatureServer/{layer}/query"
    meta = get_json(f"{STRI}/{service}/FeatureServer/{layer}", {"f": "json"})
    step = min(int(meta.get("maxRecordCount", 1000)), 1000)

    feats: list[dict] = []
    offset = 0
    while True:
        page = get_json(base, {
            "where": where, "outFields": out_fields, "returnGeometry": "true",
            "outSR": 4326, "f": "geojson",
            "resultOffset": offset, "resultRecordCount": step,
        })
        got = page.get("features", [])
        feats.extend(got)
        if len(got) < step:
            break
        offset += step
        if offset > 200_000:
            raise RuntimeError(f"runaway pagination on {service}")

    gdf = gpd.GeoDataFrame.from_features(feats, crs=CRS_WGS)
    log(f"  {service}: {len(gdf)} features")
    if cache:
        gdf.to_file(RAW / f"{cache}.geojson", driver="GeoJSON")
    return gdf


def overpass(query: str, cache: str, timeout: int = 600) -> dict:
    """Run an Overpass QL query with on-disk caching, endpoint rotation and backoff.

    Public Overpass instances rate-limit (429) and time out (504) freely. We rotate across
    several mirrors and back off, because a national-scale query set will otherwise fail
    part-way through and leave the pipeline non-reproducible.
    """
    cpath = RAW / f"{cache}.json"
    if cpath.exists():
        log(f"  cache hit: {cache}")
        return json.loads(cpath.read_text())

    endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.private.coffee/api/interpreter",
        "https://overpass.osm.jp/api/interpreter",
    ]
    last = None
    for rnd in range(3):
        for ep in endpoints:
            try:
                r = requests.post(ep, data=query.encode("utf-8"), headers=UA, timeout=timeout)
                r.raise_for_status()
                data = r.json()
                cpath.write_text(json.dumps(data))
                log(f"  overpass {cache}: {len(data.get('elements', []))} elements via {ep.split('/')[2]}")
                time.sleep(3)  # be a good citizen between queries
                return data
            except Exception as exc:  # noqa: BLE001
                last = exc
                log(f"  overpass {cache} failed on {ep.split('/')[2]}: {str(exc)[:90]}")
                time.sleep(5 + 10 * rnd)
    raise RuntimeError(f"overpass failed for {cache}: {last}")


def save_geojson(gdf: gpd.GeoDataFrame, name: str, decimals: int = 5,
                 to_web: bool = False, processed: bool = True) -> Path:
    """Write a coordinate-rounded GeoJSON to data/processed and/or web/public/data.

    `processed=False` is for web-only, field-trimmed copies of a layer that an earlier
    pipeline step also owns. Writing those back to data/processed silently clobbered the
    full version - step 60's slimmed grid overwrote step 20's, so re-running the analysis
    afterwards failed on the missing columns.
    """
    out = gdf.to_crs(CRS_WGS)
    path = PROC / f"{name}.geojson"
    if processed:
        out.to_file(path, driver="GeoJSON", coordinate_precision=decimals)
    if to_web:
        wpath = WEB_DATA / f"{name}.geojson"
        out.to_file(wpath, driver="GeoJSON", coordinate_precision=decimals)
        log(f"  wrote {name}.geojson ({wpath.stat().st_size/1e6:.2f} MB) -> "
            f"{'processed + web' if processed else 'web only'}")
    else:
        log(f"  wrote {name}.geojson ({path.stat().st_size/1e6:.2f} MB)")
    return path
