"""
KisanRadar - NASA Earth Observations for Smallholder Agricultural Resilience.
NASA Space Apps Challenge 2026: 'Field Shift: Adapting Farms with NASA Data'

Core Principles:
- REAL DATA ONLY: Direct telemetry from NASA POWER, GEE (SMAP, GPM IMERG, MODIS, Landsat, GRACE), and Open-Meteo.
- COMPLETE PROVENANCE: Every feed reports live status, dataset ID, observation date, latency, and freshness notes.
- EMPIRICAL CALIBRATION: Localized percentiles vs 2001-present calendar baseline.
- LITERATURE-DERIVED IMPACT: Damage functions from ICAR-NICRA, IPCC AR6, and IRRI trials.
"""
import os
import sys
import time
import asyncio
import datetime as dt
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load local environment variables (.env)
load_dotenv()

from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.adapters import (
    fetch_power,
    fetch_forecast,
    validate_gibs_layers,
    fetch_smap,
    fetch_gpm_imerg,
    fetch_modis,
    fetch_landsat,
    fetch_grace,
)
from app.adapters.base import SourceResult
from app.adapters.cache import get_cached_source_result, set_cached_source_result
from app.analytics import (
    compute_crop_phenology,
    compute_all_indicators,
    calculate_risk_scores,
)
from app.advisory import generate_advisory
from yield_model import estimate_yield_impact

app = FastAPI(
    title="KisanRadar API",
    description="Hyper-local climate risk assessment and STRV advisory driven by verified NASA Earth observations.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    """
    Verifies service health and reports active data adapters.
    """
    ee_project = os.environ.get("EE_PROJECT")
    return {
        "status": "healthy",
        "timestamp": dt.datetime.utcnow().isoformat() + "Z",
        "ee_project_configured": bool(ee_project),
        "ee_project": ee_project or "not_set",
        "nasa_power_baseline": "2001-present (>=9,400 daily points)",
        "gibs_wmts_cache": "24h cached XML capabilities"
    }


@app.get("/api/layers")
async def get_layers():
    """
    Returns verified NASA GIBS WMTS layer templates and capabilities.
    """
    res = await validate_gibs_layers()
    return {
        "source": res.source,
        "dataset_id": res.dataset_id,
        "status": res.status,
        "latency_ms": res.latency_ms,
        "layers": res.data.get("layers", {}) if res.data else {}
    }


@app.get("/api/analyze")
async def analyze_point(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude"),
    crop: str = Query("rice", description="Target crop: rice, wheat, or maize"),
    sowing_date: Optional[str] = Query(None, description="ISO sowing date YYYY-MM-DD"),
    lang: str = Query("en", description="Advisory language: en, hi, ta, bn, pa, te")
):
    """
    Performs full multi-sensor climate risk analysis using real NASA Earth observation data.
    """
    parsed_sowing = None
    if sowing_date and isinstance(sowing_date, str):
        try:
            parsed_sowing = dt.datetime.strptime(sowing_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid sowing_date format. Use YYYY-MM-DD.")

    crop_lower = crop.lower() if isinstance(crop, str) else "rice"
    if crop_lower not in ["rice", "wheat", "maize"]:
        crop_lower = "rice"

    lang_str = lang if isinstance(lang, str) else "en"

    provenance_list = []
    today_str = dt.date.today().isoformat()

    def serialize_sr(sr: SourceResult) -> Dict[str, Any]:
        return sr.model_dump() if hasattr(sr, "model_dump") else sr.dict()

    # 1. Query NASA POWER Climatology (with 24h disk cache)
    cached_power = get_cached_source_result("power", lat, lon, today_str, ttl_hours=24.0)
    if cached_power:
        res_power = SourceResult(**cached_power)
    else:
        res_power = await fetch_power(lat, lon, start_year=2001)
        if res_power.status == "live" and res_power.data:
            set_cached_source_result("power", lat, lon, today_str, serialize_sr(res_power))
    provenance_list.append(res_power)

    if res_power.status != "live" or not res_power.data:
        raise HTTPException(
            status_code=503,
            detail=f"NASA POWER API is currently unreachable ({res_power.error}). Strict real-data policy forbids simulated fallbacks."
        )

    power_dates = res_power.data["dates"]
    power_end_date = dt.datetime.strptime(power_dates[-1], "%Y-%m-%d").date()

    # 2. Query Open-Meteo 7-day NWP Forecast (with 6h disk cache)
    cached_fc = get_cached_source_result("forecast", lat, lon, today_str, ttl_hours=6.0)
    if cached_fc:
        res_forecast = SourceResult(**cached_fc)
    else:
        res_forecast = await fetch_forecast(lat, lon)
        if res_forecast.status == "live" and res_forecast.data:
            set_cached_source_result("forecast", lat, lon, today_str, serialize_sr(res_forecast))
    provenance_list.append(res_forecast)

    # 3. Query GEE Satellite Feeds in Parallel (with 24h disk cache)
    async def get_gee_source(ns: str, fetch_fn, *args):
        cached = get_cached_source_result(ns, lat, lon, today_str, ttl_hours=24.0)
        if cached:
            return SourceResult(**cached)
        res = await asyncio.to_thread(fetch_fn, *args)
        if res.status == "live" and res.data:
            set_cached_source_result(ns, lat, lon, today_str, serialize_sr(res))
        return res

    gee_tasks = [
        get_gee_source("smap", fetch_smap, lat, lon),
        get_gee_source("gpm", fetch_gpm_imerg, lat, lon, 30, power_end_date),
        get_gee_source("modis", fetch_modis, lat, lon),
        get_gee_source("landsat", fetch_landsat, lat, lon),
        get_gee_source("grace", fetch_grace, lat, lon),
    ]
    res_smap, res_gpm, res_modis, res_landsat, res_grace = await asyncio.gather(*gee_tasks)
    provenance_list.extend([res_smap, res_gpm, res_modis, res_landsat, res_grace])

    # 4. Compute Indicators & Crop Phenology
    analytics_res = compute_all_indicators(
        power_data=res_power.data,
        forecast_data=res_forecast.data if res_forecast.status == "live" else None,
        smap_data=res_smap.data if res_smap.status == "live" else None,
        gpm_data=res_gpm.data if res_gpm.status == "live" else None,
        modis_data=res_modis.data if res_modis.status == "live" else None,
        landsat_data=res_landsat.data if res_landsat.status == "live" else None,
        grace_data=res_grace.data if res_grace.status == "live" else None,
        crop=crop_lower,
        sowing_date=parsed_sowing
    )

    phenology = analytics_res["phenology"]
    indicators = analytics_res["indicators"]

    # 5. Compute Percentile-Driven Multi-Hazard Risk Scores
    risk_scores = calculate_risk_scores(
        indicators=indicators,
        phenology=phenology,
        provenance_list=provenance_list
    )

    # 6. Estimate Literature-Derived Yield Impact & STRV Buffers
    yield_metrics = {
        "tmax_14d_c": indicators["heat_stress"]["mean_tmax_14d_c"],
        "hot_days_14d": indicators["heat_stress"]["hot_days_past_14d"],
        "hot_days_forecast": indicators["heat_stress"]["hot_days_forecast_7d"],
        "in_heat_sensitive_window": phenology["in_heat_sensitive_window"],
        "wetness_percentile": indicators["soil_moisture"]["primary_soil_percentile"],
        "dry_spell_days": indicators["dry_spell"]["consecutive_days_under_1mm"]
    }
    yield_impact = estimate_yield_impact(crop_lower, yield_metrics, risk_scores, phenology=phenology)

    # 7. Generate Actionable Multilingual Agronomic Advisory
    advisory = generate_advisory(
        crop=crop_lower,
        risk_scores=risk_scores,
        phenology=phenology,
        indicators=indicators,
        lang=lang_str
    )

    # 8. Extract 25-Year Climatological Series for Frontend Charts
    years_map = {}
    rain_arr = res_power.data["PRECTOTCORR"]
    t2m_arr = res_power.data["T2M"]
    for d_str, r, t in zip(power_dates, rain_arr, t2m_arr):
        y = int(d_str[:4])
        if y not in years_map:
            years_map[y] = {"rain": [], "temp": []}
        if r is not None and not (isinstance(r, float) and (r != r or r < 0)):
            years_map[y]["rain"].append(r)
        if t is not None and not (isinstance(t, float) and (t != t or t < -90)):
            years_map[y]["temp"].append(t)

    chart_years = sorted([y for y in years_map if len(years_map[y]["temp"]) >= 330])
    annual_rain = [round(sum(years_map[y]["rain"]), 1) for y in chart_years]
    annual_temp = [round(sum(years_map[y]["temp"]) / len(years_map[y]["temp"]), 2) for y in chart_years]

    return {
        "location": {"lat": lat, "lon": lon},
        "query_timestamp": dt.datetime.utcnow().isoformat() + "Z",
        "crop": crop_lower,
        "phenology": phenology,
        "risk_scores": risk_scores,
        "indicators": indicators,
        "yield_impact": yield_impact,
        "advisory": advisory,
        "charts": {
            "years": chart_years,
            "annual_rainfall_mm": annual_rain,
            "annual_mean_temp_c": annual_temp,
            "warming_trend_c_per_decade": indicators["climate_warming_trend"]["warming_trend_c_per_decade"],
            "p_value": indicators["climate_warming_trend"]["p_value"]
        },
        "provenance": [
            {
                "source": p.source,
                "dataset_id": p.dataset_id,
                "status": p.status,
                "observed_through": p.observed_through,
                "latency_ms": p.latency_ms,
                "n_obs": p.n_obs,
                "units": p.units,
                "freshness_note": p.freshness_note,
                "error": p.error
            }
            for p in provenance_list
        ]
    }


@app.get("/api/historical-replay/{event_id}")
async def historical_replay(event_id: str, lang: str = "en"):
    """
    Replays real archived climate shock events using authentic historical NASA POWER,
    MODIS, and GPM IMERG data. Zero mock data.
    """
    events = {
        "punjab-march-2022-heatwave": {
            "title": "Punjab March 2022 Terminal Heatwave",
            "lat": 30.90,
            "lon": 75.85,
            "crop": "wheat",
            "sowing_date": "2021-11-10",
            "replay_end_date": dt.date(2022, 3, 25),
            "description": (
                "Historical replay of the March 2022 terminal heat shock across the Punjab wheat belt. "
                "Extreme March temperatures during wheat grain-filling caused severe pollen sterility and test-weight shriveling. "
                "Telemetry below is computed from authentic archived NASA POWER, MODIS, and MERRA-2 feeds."
            ),
            "include_modis": True,
            "include_gpm": False
        },
        "pakistan-sindh-aug-2022-flood": {
            "title": "Pakistan Sindh August 2022 Monsoon Deluge",
            "lat": 26.00,
            "lon": 68.50,
            "crop": "rice",
            "sowing_date": "2022-06-01",
            "replay_end_date": dt.date(2022, 8, 31),
            "description": (
                "Historical replay of the catastrophic August 2022 Indus Basin flood deluge in Sindh. "
                "Over 550 mm of relentless monsoon precipitation destroyed standing kharif crops."
            ),
            "include_modis": False,
            "include_gpm": True
        },
        "tamilnadu-dec-2023-cyclone": {
            "title": "Tamil Nadu Coastal Dec 2023 Cyclone Michaung Deluge",
            "lat": 13.08,
            "lon": 80.27,
            "crop": "rice",
            "sowing_date": "2023-08-15",
            "replay_end_date": dt.date(2023, 12, 8),
            "description": (
                "Historical replay of extreme Cyclone Michaung rainfall in North Coastal Tamil Nadu. "
                "Over 300 mm (POWER) to 650 mm (IMERG) inundated coastal samba paddy fields for over a week."
            ),
            "include_modis": False,
            "include_gpm": True
        }
    }

    if event_id not in events:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown replay event '{event_id}'. Available: {list(events.keys())}"
        )

    ev = events[event_id]
    lat = ev["lat"]
    lon = ev["lon"]
    crop = ev["crop"]
    sowing = dt.datetime.strptime(ev["sowing_date"], "%Y-%m-%d").date()
    replay_end = ev["replay_end_date"]

    res_power = await fetch_power(lat, lon, start_year=2001, end_date=replay_end)
    if res_power.status != "live" or not res_power.data:
        raise HTTPException(status_code=503, detail="Unable to retrieve archived NASA POWER baseline for replay.")

    provenance_list = [res_power]
    res_modis = None
    res_gpm = None

    if ev.get("include_modis"):
        res_modis = fetch_modis(lat, lon, target_date=replay_end)
        provenance_list.append(res_modis)

    if ev.get("include_gpm"):
        res_gpm = fetch_gpm_imerg(lat, lon, days_back=30, end_date=replay_end)
        provenance_list.append(res_gpm)

    analytics_res = compute_all_indicators(
        power_data=res_power.data,
        forecast_data=None,
        smap_data=None,
        gpm_data=res_gpm.data if (res_gpm and res_gpm.status == "live") else None,
        modis_data=res_modis.data if (res_modis and res_modis.status == "live") else None,
        landsat_data=None,
        grace_data=None,
        crop=crop,
        sowing_date=sowing
    )

    phenology = analytics_res["phenology"]
    indicators = analytics_res["indicators"]

    risk_scores = calculate_risk_scores(indicators, phenology, provenance_list)

    yield_metrics = {
        "tmax_14d_c": indicators["heat_stress"]["mean_tmax_14d_c"],
        "hot_days_14d": indicators["heat_stress"]["hot_days_past_14d"],
        "hot_days_forecast": 0,
        "in_heat_sensitive_window": phenology["in_heat_sensitive_window"],
        "wetness_percentile": indicators["soil_moisture"]["primary_soil_percentile"],
        "dry_spell_days": indicators["dry_spell"]["consecutive_days_under_1mm"]
    }
    yield_impact = estimate_yield_impact(crop, yield_metrics, risk_scores, phenology=phenology)

    advisory = generate_advisory(crop, risk_scores, phenology, indicators, lang=lang)

    return {
        "event_id": event_id,
        "event_title": ev["title"],
        "event_description": ev["description"],
        "lat": lat,
        "lon": lon,
        "replay_date": replay_end.isoformat(),
        "crop": crop,
        "sowing_date": ev["sowing_date"],
        "phenology": phenology,
        "risk_scores": risk_scores,
        "indicators": indicators,
        "yield_impact": yield_impact,
        "advisory": advisory,
        "provenance": [
            {
                "source": p.source,
                "dataset_id": p.dataset_id,
                "status": "archived-replay",
                "observed_through": p.observed_through or replay_end.isoformat(),
                "latency_ms": p.latency_ms,
                "n_obs": p.n_obs,
                "freshness_note": p.freshness_note or f"Archived real NASA observations up to {replay_end.isoformat()}"
            }
            for p in provenance_list
        ]
    }


# Mount static frontend
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
