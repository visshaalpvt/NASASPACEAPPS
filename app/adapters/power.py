"""
NASA POWER Daily Agroclimatology Adapter.
Dataset: NASA POWER Point Daily API (Community: AG)
Parameters: T2M, T2M_MAX, T2M_MIN, PRECTOTCORR, RH2M, ALLSKY_SFC_SW_DWN, GWETROOT, GWETTOP, GWETPROF
Note: GWET* are modelled wetness fractions from MERRA-2, not direct SMAP satellite telemetry.
Full baseline range: 2001-01-01 to today - 5 days (~9,400+ daily observations).
"""
import time
import datetime as dt
from typing import Optional, Dict, Any
import httpx
import numpy as np

from app.adapters.base import SourceResult

DATASET_ID = "NASA_POWER_AG_POINT_DAILY_V2"
PARAMS = "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,ALLSKY_SFC_SW_DWN,GWETROOT,GWETTOP,GWETPROF"
BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"


async def fetch_power(
    lat: float,
    lon: float,
    start_year: int = 2001,
    end_date: Optional[dt.date] = None,
    timeout_sec: float = 60.0
) -> SourceResult:
    """
    Fetch daily NASA POWER agroclimatology from start_year (2001) to today - 5 days.
    """
    t0 = time.time()
    if end_date is None:
        # 5-day assimilation lag for MERRA-2 daily products
        end_date = dt.date.today() - dt.timedelta(days=5)

    start_str = f"{start_year}0101"
    end_str = end_date.strftime("%Y%m%d")

    url = (
        f"{BASE_URL}?parameters={PARAMS}&community=AG"
        f"&longitude={lon}&latitude={lat}&start={start_str}&end={end_str}&format=JSON"
    )

    headers = {"User-Agent": "KisanRadar/1.0 (NASA-Space-Apps-2026)"}

    try:
        async with httpx.AsyncClient(timeout=timeout_sec) as client:
            resp = await client.get(url, headers=headers)
        
        latency = int((time.time() - t0) * 1000)

        if resp.status_code != 200:
            return SourceResult(
                source="NASA POWER",
                dataset_id=DATASET_ID,
                status="unavailable",
                latency_ms=latency,
                error=f"HTTP {resp.status_code}: {resp.text[:300]}"
            )

        data_json = resp.json()
        props = data_json.get("properties", {}).get("parameter", {})
        if not props or "T2M" not in props:
            return SourceResult(
                source="NASA POWER",
                dataset_id=DATASET_ID,
                status="unavailable",
                latency_ms=latency,
                error="Response JSON missing 'parameter' dictionary or 'T2M' values"
            )

        days = sorted(props["T2M"].keys())
        if not days:
            return SourceResult(
                source="NASA POWER",
                dataset_id=DATASET_ID,
                status="unavailable",
                latency_ms=latency,
                error="Zero observation days returned by NASA POWER API"
            )

        # Parse arrays with -999 as NaN
        dates = [f"{d[:4]}-{d[4:6]}-{d[6:]}" for d in days]
        cleaned: Dict[str, Any] = {"dates": dates}
        for p in PARAMS.split(","):
            vals = [props.get(p, {}).get(d, np.nan) for d in days]
            arr = np.array(vals, dtype=float)
            arr[arr <= -990.0] = np.nan
            cleaned[p] = arr.tolist()

        latest_obs = dates[-1]

        return SourceResult(
            source="NASA POWER",
            dataset_id=DATASET_ID,
            status="live",
            observed_through=latest_obs,
            freshness_note=f"Full multi-year daily climatology with standard 5-day MERRA-2 processing lag (latest observation: {latest_obs})",
            latency_ms=latency,
            n_obs=len(days),
            units="T2M: °C, PRECTOTCORR: mm/day, RH2M: %, ALLSKY_SFC_SW_DWN: MJ/m^2/day, GWET*: fraction (0-1)",
            data=cleaned
        )

    except Exception as e:
        latency = int((time.time() - t0) * 1000)
        return SourceResult(
            source="NASA POWER",
            dataset_id=DATASET_ID,
            status="unavailable",
            latency_ms=latency,
            error=f"Connection/Fetch Exception: {str(e)}"
        )
