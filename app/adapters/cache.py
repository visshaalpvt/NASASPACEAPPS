"""
Disk-Backed Caching Engine for Earth Observation Baselines and Multi-Year Climatologies.
Caches multi-year baseline statistics (SMAP, IMERG, MODIS, POWER) by rounded coordinates
and calendar day-of-year (DOY) to achieve <3s warm query latency.
"""
import os
import json
import time
from typing import Optional, Any

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_key(namespace: str, lat: float, lon: float, doy: int) -> str:
    lat_r = round(lat, 2)
    lon_r = round(lon, 2)
    return f"{namespace}_{lat_r:.2f}_{lon_r:.2f}_doy{doy}.json"


def get_cached_baseline(namespace: str, lat: float, lon: float, doy: int, ttl_hours: float = 72.0) -> Optional[Any]:
    filename = _cache_key(namespace, lat, lon, doy)
    path = os.path.join(CACHE_DIR, filename)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        cached_time = obj.get("cached_at", 0)
        if time.time() - cached_time > (ttl_hours * 3600):
            return None
        return obj.get("data")
    except Exception:
        return None


def set_cached_baseline(namespace: str, lat: float, lon: float, doy: int, data: Any) -> None:
    filename = _cache_key(namespace, lat, lon, doy)
    path = os.path.join(CACHE_DIR, filename)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "namespace": namespace,
                "lat": round(lat, 2),
                "lon": round(lon, 2),
                "doy": doy,
                "cached_at": time.time(),
                "data": data
            }, f, indent=2)
    except Exception:
        pass


def get_cached_source_result(namespace: str, lat: float, lon: float, date_str: str, ttl_hours: float = 24.0) -> Optional[Any]:
    filename = f"result_{namespace}_{round(lat, 2):.2f}_{round(lon, 2):.2f}_{date_str}.json"
    path = os.path.join(CACHE_DIR, filename)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        cached_time = obj.get("cached_at", 0)
        if time.time() - cached_time > (ttl_hours * 3600):
            return None
        return obj.get("data")
    except Exception:
        return None


def set_cached_source_result(namespace: str, lat: float, lon: float, date_str: str, data: Any) -> None:
    filename = f"result_{namespace}_{round(lat, 2):.2f}_{round(lon, 2):.2f}_{date_str}.json"
    path = os.path.join(CACHE_DIR, filename)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "namespace": namespace,
                "lat": round(lat, 2),
                "lon": round(lon, 2),
                "date_str": date_str,
                "cached_at": time.time(),
                "data": data
            }, f, indent=2)
    except Exception:
        pass
