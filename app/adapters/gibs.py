"""
NASA Global Imagery Browse Services (GIBS) WMTS Capabilities Validator & Adapter.
Validates layer presence, CRS (EPSG:3857), TileMatrixSet, and temporal dimension directly
against the live OGC WMTSCapabilities XML.
Caches parsed capabilities metadata for 24 hours (86,400 seconds) to avoid redownloading 5.8 MB XML.
"""
import os
import json
import time
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
import httpx

from app.adapters.base import SourceResult

DATASET_ID = "NASA_GIBS_EPSG3857_BEST_WMTS"
CAPABILITIES_URL = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/1.0.0/WMTSCapabilities.xml"
CACHE_TTL_SECONDS = 86400  # 24 hours

CANDIDATE_LAYERS = [
    "MODIS_Terra_CorrectedReflectance_TrueColor",
    "MODIS_Terra_L3_NDVI_Monthly",
    "MODIS_Terra_Land_Surface_Temp_Day",
    "IMERG_Precipitation_Rate"
]

NAMESPACES = {
    "wmts": "http://www.opengis.net/wmts/1.0",
    "ows": "http://www.opengis.net/ows/1.1"
}

_MEMORY_CACHE = {
    "timestamp": 0.0,
    "result": None
}


def _get_cache_path() -> str:
    cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "cache")
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, "gibs_capabilities.json")


def _read_disk_cache() -> Optional[Dict[str, Any]]:
    path = _get_cache_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
            if time.time() - d.get("timestamp", 0) < CACHE_TTL_SECONDS:
                return d.get("data")
        except Exception:
            pass
    return None


def _write_disk_cache(data: Dict[str, Any]):
    path = _get_cache_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"timestamp": time.time(), "data": data}, f)
    except Exception:
        pass


async def validate_gibs_layers(timeout_sec: float = 25.0, force_refresh: bool = False) -> SourceResult:
    """
    Fetch and validate WMTSCapabilities from NASA GIBS with 24h caching.
    """
    t0 = time.time()

    # 1. Check in-memory cache
    if not force_refresh and (time.time() - _MEMORY_CACHE["timestamp"] < CACHE_TTL_SECONDS) and _MEMORY_CACHE["result"]:
        res = _MEMORY_CACHE["result"]
        return SourceResult(
            source=res.source,
            dataset_id=res.dataset_id,
            status="cached",
            observed_through=res.observed_through,
            freshness_note="Served from 24h local memory cache of NASA GIBS Capabilities",
            latency_ms=int((time.time() - t0) * 1000),
            n_obs=res.n_obs,
            units=res.units,
            data=res.data
        )

    # 2. Check disk cache
    if not force_refresh:
        cached_disk = _read_disk_cache()
        if cached_disk:
            latency = int((time.time() - t0) * 1000)
            res = SourceResult(
                source="NASA GIBS WMTS",
                dataset_id=DATASET_ID,
                status="cached",
                observed_through=cached_disk.get("validated_layers", {}).get(CANDIDATE_LAYERS[0], {}).get("default_time"),
                freshness_note="Served from 24h disk cache of NASA GIBS Capabilities",
                latency_ms=latency,
                n_obs=len(cached_disk.get("validated_layers", {})),
                units="Tiles (EPSG:3857 Web Mercator)",
                data=cached_disk
            )
            _MEMORY_CACHE["timestamp"] = time.time()
            _MEMORY_CACHE["result"] = res
            return res

    # 3. Live XML fetch
    try:
        async with httpx.AsyncClient(timeout=timeout_sec) as client:
            resp = await client.get(CAPABILITIES_URL, headers={"User-Agent": "KisanRadar/1.0 (NASA-Space-Apps)"})

        latency = int((time.time() - t0) * 1000)

        if resp.status_code != 200:
            return SourceResult(
                source="NASA GIBS WMTS",
                dataset_id=DATASET_ID,
                status="unavailable",
                latency_ms=latency,
                error=f"Capabilities fetch failed HTTP {resp.status_code}"
            )

        root = ET.fromstring(resp.content)
        layers_in_xml = {}

        for layer_elem in root.findall(".//wmts:Layer", NAMESPACES):
            id_elem = layer_elem.find("ows:Identifier", NAMESPACES)
            if id_elem is None or not id_elem.text:
                continue
            layer_id = id_elem.text

            tms_links = [
                t.text for t in layer_elem.findall(".//wmts:TileMatrixSetLink/wmts:TileMatrixSet", NAMESPACES)
                if t.text
            ]
            formats = [f.text for f in layer_elem.findall("wmts:Format", NAMESPACES) if f.text]

            time_dim = layer_elem.find(".//wmts:Dimension[ows:Identifier='Time']", NAMESPACES)
            default_time = None
            if time_dim is not None:
                def_elem = time_dim.find("wmts:Default", NAMESPACES)
                if def_elem is not None:
                    default_time = def_elem.text

            layers_in_xml[layer_id] = {
                "identifier": layer_id,
                "tile_matrix_sets": tms_links,
                "formats": formats,
                "default_time": default_time
            }

        validated = {}
        dropped = []
        for cand in CANDIDATE_LAYERS:
            if cand in layers_in_xml:
                info = layers_in_xml[cand]
                gmc_levels = [t for t in info["tile_matrix_sets"] if "GoogleMapsCompatible_Level" in t]
                max_level = 9
                if gmc_levels:
                    try:
                        max_level = max(int(l.split("Level")[-1]) for l in gmc_levels)
                    except ValueError:
                        max_level = 9

                format_ext = "png"
                if any("jpeg" in f.lower() or "jpg" in f.lower() for f in info["formats"]):
                    if "image/png" not in info["formats"]:
                        format_ext = "jpg"

                validated[cand] = {
                    "layer_id": cand,
                    "max_zoom": max_level,
                    "format_ext": format_ext,
                    "default_time": info["default_time"],
                    "url_template": f"https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/{cand}/default/{{time}}/GoogleMapsCompatible_Level{max_level}/{{z}}/{{y}}/{{x}}.{format_ext}"
                }
            else:
                dropped.append(cand)

        payload = {"validated_layers": validated, "dropped_layers": dropped}
        _write_disk_cache(payload)

        res = SourceResult(
            source="NASA GIBS WMTS",
            dataset_id=DATASET_ID,
            status="live",
            observed_through=validated.get(CANDIDATE_LAYERS[0], {}).get("default_time"),
            freshness_note="Live WMTS Capabilities validated from NASA GIBS; cached for 24h",
            latency_ms=latency,
            n_obs=len(validated),
            units="Tiles (EPSG:3857 Web Mercator)",
            error=f"Dropped unvalidated layers: {dropped}" if dropped else None,
            data=payload
        )
        _MEMORY_CACHE["timestamp"] = time.time()
        _MEMORY_CACHE["result"] = res
        return res

    except Exception as e:
        latency = int((time.time() - t0) * 1000)
        return SourceResult(
            source="NASA GIBS WMTS",
            dataset_id=DATASET_ID,
            status="unavailable",
            latency_ms=latency,
            error=f"XML Parsing / Fetch error: {str(e)}"
        )
