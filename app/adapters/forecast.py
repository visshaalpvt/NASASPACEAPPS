"""
Open-Meteo 7-day NWP Forecast Adapter.
Explicitly noted in UI and Metadata: NON-NASA data source (used solely for forward outlook).
"""
import time
from typing import Optional, Dict, Any
import httpx

from app.adapters.base import SourceResult

DATASET_ID = "OPEN_METEO_SEAMLESS_DAILY_V1"
BASE_URL = "https://api.open-meteo.com/v1/forecast"


async def fetch_forecast(
    lat: float,
    lon: float,
    days: int = 7,
    timeout_sec: float = 15.0
) -> SourceResult:
    """
    Fetch 7-day numerical weather prediction for precipitation and temperature.
    """
    t0 = time.time()
    url = (
        f"{BASE_URL}?latitude={lat}&longitude={lon}&timezone=auto"
        f"&forecast_days={days}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
    )
    headers = {"User-Agent": "KisanRadar/1.0 (NASA-Space-Apps-2026)"}

    try:
        async with httpx.AsyncClient(timeout=timeout_sec) as client:
            resp = await client.get(url, headers=headers)

        latency = int((time.time() - t0) * 1000)

        if resp.status_code != 200:
            return SourceResult(
                source="Open-Meteo NWP (not NASA)",
                dataset_id=DATASET_ID,
                status="unavailable",
                latency_ms=latency,
                error=f"HTTP {resp.status_code}: {resp.text[:250]}"
            )

        daily = resp.json().get("daily", {})
        times = daily.get("time", [])
        if not times:
            return SourceResult(
                source="Open-Meteo NWP (not NASA)",
                dataset_id=DATASET_ID,
                status="unavailable",
                latency_ms=latency,
                error="No forecast timestamps returned"
            )

        return SourceResult(
            source="Open-Meteo NWP (not NASA)",
            dataset_id=DATASET_ID,
            status="live",
            observed_through=times[-1],
            freshness_note=f"Forward 7-day atmospheric forecast run initialized for window {times[0]} to {times[-1]}",
            latency_ms=latency,
            n_obs=len(times),
            units="Tmax/Tmin: °C, Rain: mm/day",
            data={
                "dates": times,
                "tmax": daily.get("temperature_2m_max", []),
                "tmin": daily.get("temperature_2m_min", []),
                "rain": daily.get("precipitation_sum", [])
            }
        )

    except Exception as e:
        latency = int((time.time() - t0) * 1000)
        return SourceResult(
            source="Open-Meteo NWP (not NASA)",
            dataset_id=DATASET_ID,
            status="unavailable",
            latency_ms=latency,
            error=f"Connection/Fetch Exception: {str(e)}"
        )
