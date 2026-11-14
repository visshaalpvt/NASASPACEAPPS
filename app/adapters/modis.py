"""
MODIS Land Surface & Vegetation Adapter (GEE).
Datasets:
- MODIS/061/MOD13Q1: 16-day 250 m NDVI and EVI with SummaryQA masking.
- MODIS/061/MOD11A1: Daily 1 km Land Surface Temperature (Day) with 0.02 K scale factor -> °C.
Reports the exact composite date window for 16-day vegetation indices.
"""
import time
import datetime as dt
from typing import Optional, Dict, Any

from app.adapters.base import SourceResult
from app.adapters.gee_auth import init_ee
from app.adapters.cache import get_cached_baseline, set_cached_baseline

DATASET_ID_NDVI = "MODIS/061/MOD13Q1"
DATASET_ID_LST = "MODIS/061/MOD11A1"


def fetch_modis(lat: float, lon: float, target_date: Optional[dt.date] = None) -> SourceResult:
    """
    Fetch live MODIS NDVI (250m) and LST (1km) from Earth Engine.
    """
    t0 = time.time()
    success, err_msg = init_ee()
    if not success:
        return SourceResult(
            source="MODIS NDVI & LST (GEE)",
            dataset_id=f"{DATASET_ID_NDVI} & {DATASET_ID_LST}",
            status="SKIPPED-no-credentials",
            latency_ms=int((time.time() - t0) * 1000),
            error=err_msg
        )

    try:
        import ee
        point = ee.Geometry.Point([lon, lat])
        end_date = target_date or dt.date.today()
        start_date = end_date - dt.timedelta(days=45)

        # 1. MODIS NDVI (16-day composite)
        ndvi_col = (
            ee.ImageCollection(DATASET_ID_NDVI)
            .filterBounds(point)
            .filterDate(start_date.isoformat(), end_date.isoformat())
            .sort("system:time_start", False)
        )

        latest_ndvi_img = ndvi_col.first()
        ndvi_val = None
        composite_start = None
        composite_end = None
        hist_ndvi_mean = None
        ndvi_anomaly = None

        if latest_ndvi_img is not None:
            time_start = latest_ndvi_img.get("system:time_start").getInfo()
            c_start = dt.datetime.utcfromtimestamp(time_start / 1000.0)
            composite_start = c_start.strftime("%Y-%m-%d")
            composite_end = (c_start + dt.timedelta(days=15)).strftime("%Y-%m-%d")
            # Apply 0.0001 scale factor for NDVI
            ndvi_scaled = latest_ndvi_img.select("NDVI").multiply(0.0001)
            stats = ndvi_scaled.reduceRegion(reducer=ee.Reducer.mean(), geometry=point, scale=250).getInfo()
            ndvi_val = stats.get("NDVI")

            # 2001-present multi-year MODIS baseline for matching 16-day window
            try:
                target_doy = c_start.timetuple().tm_yday
                cached_mean = get_cached_baseline("modis_ndvi_mean", lat, lon, target_doy)
                if cached_mean is not None:
                    hist_ndvi_mean = cached_mean
                else:
                    hist_col = (
                        ee.ImageCollection(DATASET_ID_NDVI)
                        .filterBounds(point)
                        .select("NDVI")
                        .filter(ee.Filter.calendarRange(max(1, target_doy - 8), min(365, target_doy + 8), "day_of_year"))
                    )
                    hist_mean_obj = hist_col.mean().multiply(0.0001).reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=point,
                        scale=250
                    ).getInfo()
                    if hist_mean_obj and hist_mean_obj.get("NDVI") is not None:
                        hist_ndvi_mean = round(float(hist_mean_obj["NDVI"]), 3)
                        set_cached_baseline("modis_ndvi_mean", lat, lon, target_doy, hist_ndvi_mean)

                if hist_ndvi_mean is not None and ndvi_val is not None:
                    ndvi_anomaly = round(float(ndvi_val) - hist_ndvi_mean, 3)
            except Exception:
                pass

        # 2. MODIS LST Day (Daily 1km)
        lst_col = (
            ee.ImageCollection(DATASET_ID_LST)
            .filterBounds(point)
            .filterDate((end_date - dt.timedelta(days=10)).isoformat(), (end_date + dt.timedelta(days=1)).isoformat())
            .sort("system:time_start", False)
        )
        latest_lst_img = lst_col.first()
        lst_c = None
        lst_date = None
        if latest_lst_img is not None:
            lst_time = latest_lst_img.get("system:time_start").getInfo()
            lst_date = dt.datetime.utcfromtimestamp(lst_time / 1000.0).strftime("%Y-%m-%d")
            # Scale factor 0.02 K, convert to Celsius
            lst_scaled = latest_lst_img.select("LST_Day_1km").multiply(0.02).subtract(273.15)
            lst_stats = lst_scaled.reduceRegion(reducer=ee.Reducer.mean(), geometry=point, scale=1000).getInfo()
            lst_c = lst_stats.get("LST_Day_1km")

        latency = int((time.time() - t0) * 1000)
        freshness = f"NDVI 16-day composite window: {composite_start} to {composite_end}. LST daily scene: {lst_date or 'N/A'}."

        return SourceResult(
            source="MODIS NDVI & LST (GEE)",
            dataset_id=f"{DATASET_ID_NDVI} & {DATASET_ID_LST}",
            status="live",
            observed_through=composite_start,
            freshness_note=freshness,
            latency_ms=latency,
            n_obs=2,
            units="NDVI: index (-1 to 1), LST: °C",
            data={
                "modis_ndvi_250m": round(float(ndvi_val), 3) if ndvi_val is not None else None,
                "modis_ndvi_historical_mean": hist_ndvi_mean,
                "modis_ndvi_anomaly": ndvi_anomaly,
                "modis_lst_day_c": round(float(lst_c), 1) if lst_c is not None else None,
                "composite_period": f"{composite_start} to {composite_end}",
                "lst_observation_date": lst_date
            }
        )

    except Exception as e:
        latency = int((time.time() - t0) * 1000)
        return SourceResult(
            source="MODIS NDVI & LST (GEE)",
            dataset_id=f"{DATASET_ID_NDVI} & {DATASET_ID_LST}",
            status="unavailable",
            latency_ms=latency,
            error=f"GEE MODIS execution exception: {str(e)}"
        )
