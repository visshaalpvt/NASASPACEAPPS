"""
NASA SMAP Level-4 Global Daily 9 km Soil Moisture Adapter (GEE).
Current Active Dataset ID: NASA/SMAP/SPL4SMGP/008 (Version 8)
Bands: sm_rootzone (m^3/m^3), sm_surface (m^3/m^3), sm_rootzone_wetness (0-1)
"""
import time
import datetime as dt
from typing import Optional, Dict, Any

from app.adapters.base import SourceResult
from app.adapters.gee_auth import init_ee
from app.adapters.cache import get_cached_baseline, set_cached_baseline

DATASET_ID = "NASA/SMAP/SPL4SMGP/008"
FALLBACK_ID = "NASA/SMAP/SPL4SMGP/007"


def fetch_smap(lat: float, lon: float, days_back: int = 14) -> SourceResult:
    """
    Fetch live NASA SMAP Level-4 Soil Moisture via Earth Engine.
    """
    t0 = time.time()
    success, err_msg = init_ee()
    if not success:
        return SourceResult(
            source="NASA SMAP L4 (GEE)",
            dataset_id=DATASET_ID,
            status="SKIPPED-no-credentials",
            latency_ms=int((time.time() - t0) * 1000),
            error=err_msg
        )

    try:
        import ee
        point = ee.Geometry.Point([lon, lat])
        end_date = dt.date.today()
        start_date = end_date - dt.timedelta(days=days_back)

        target_id = DATASET_ID
        try:
            col = (
                ee.ImageCollection(target_id)
                .filterBounds(point)
                .filterDate(start_date.isoformat(), end_date.isoformat())
                .select(["sm_rootzone", "sm_surface", "sm_rootzone_wetness"])
            )
            size = col.size().getInfo()
            if size == 0:
                col = (
                    ee.ImageCollection(FALLBACK_ID)
                    .filterBounds(point)
                    .filterDate(start_date.isoformat(), end_date.isoformat())
                    .select(["sm_rootzone", "sm_surface", "sm_rootzone_wetness"])
                )
                size = col.size().getInfo()
                if size > 0:
                    target_id = FALLBACK_ID
        except Exception:
            target_id = FALLBACK_ID
            col = (
                ee.ImageCollection(target_id)
                .filterBounds(point)
                .filterDate(start_date.isoformat(), end_date.isoformat())
                .select(["sm_rootzone", "sm_surface", "sm_rootzone_wetness"])
            )
            size = col.size().getInfo()

        if size == 0:
            return SourceResult(
                source="NASA SMAP L4 (GEE)",
                dataset_id=target_id,
                status="unavailable",
                latency_ms=int((time.time() - t0) * 1000),
                error=f"No SMAP images returned for bounding point in the last {days_back} days"
            )

        latest_img = col.sort("system:time_start", False).first()
        time_start = latest_img.get("system:time_start").getInfo()
        obs_date = dt.datetime.utcfromtimestamp(time_start / 1000.0).strftime("%Y-%m-%d")

        stats = latest_img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=9000
        ).getInfo()

        current_wetness = stats.get("sm_rootzone_wetness")

        # Historical multi-year SMAP baseline (2015-present for matching calendar window +/- 7 days)
        smap_percentile = None
        smap_hist_mean = None
        smap_hist_count = 0
        try:
            target_doy = dt.datetime.strptime(obs_date, "%Y-%m-%d").timetuple().tm_yday
            cached_vals = get_cached_baseline("smap_rootzone", lat, lon, target_doy)
            if cached_vals is not None:
                hist_vals = cached_vals
                smap_hist_count = len(hist_vals)
            else:
                hist_col = (
                    ee.ImageCollection(target_id)
                    .filterBounds(point)
                    .select("sm_rootzone_wetness")
                    .filter(ee.Filter.calendarRange(max(1, target_doy - 7), min(365, target_doy + 7), "day_of_year"))
                )
                years = ee.List.sequence(2015, int(obs_date[:4]))
                def get_year_val(y):
                    y = ee.Number(y)
                    sub = hist_col.filter(ee.Filter.calendarRange(y, y, "year"))
                    val = sub.mean().reduceRegion(reducer=ee.Reducer.mean(), geometry=point, scale=9000).get("sm_rootzone_wetness")
                    return val

                hist_vals_raw = years.map(get_year_val).getInfo()
                hist_vals = [float(v) for v in hist_vals_raw if v is not None]
                smap_hist_count = len(hist_vals)
                if hist_vals:
                    set_cached_baseline("smap_rootzone", lat, lon, target_doy, hist_vals)

            if hist_vals and current_wetness is not None:
                smap_hist_mean = round(sum(hist_vals) / len(hist_vals), 3)
                v_arr = [float(x) for x in hist_vals]
                cw = float(current_wetness)
                # Weibull plotting position to avoid 0.0% / 100.0% boundary artifacts in small samples (N=10-12)
                n = float(len(v_arr))
                r = sum(1 for x in v_arr if x < cw) + 0.5 * sum(1 for x in v_arr if abs(x - cw) < 1e-4)
                rank = (r + 0.5) / (n + 1.0)
                smap_percentile = round(min(99.0, max(1.0, rank * 100.0)), 1)
        except Exception as e_hist:
            pass

        latency = int((time.time() - t0) * 1000)
        return SourceResult(
            source="NASA SMAP L4 (GEE)",
            dataset_id=target_id,
            status="live",
            observed_through=obs_date,
            freshness_note=f"Daily 9 km root-zone product with ~2-day satellite assimilation latency (observed through {obs_date})",
            latency_ms=latency,
            n_obs=size,
            units="sm_rootzone: m^3/m^3, sm_surface: m^3/m^3, sm_rootzone_wetness: fraction",
            data={
                "sm_rootzone": stats.get("sm_rootzone"),
                "sm_surface": stats.get("sm_surface"),
                "sm_rootzone_wetness": stats.get("sm_rootzone_wetness"),
                "sm_rootzone_wetness_percentile": smap_percentile,
                "sm_rootzone_wetness_historical_mean": smap_hist_mean,
                "smap_baseline_years": smap_hist_count,
                "images_in_window": size
            }
        )

    except Exception as e:
        latency = int((time.time() - t0) * 1000)
        return SourceResult(
            source="NASA SMAP L4 (GEE)",
            dataset_id=DATASET_ID,
            status="unavailable",
            latency_ms=latency,
            error=f"GEE execution exception: {str(e)}"
        )
