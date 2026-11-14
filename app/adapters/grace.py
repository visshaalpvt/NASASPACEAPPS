"""
NASA GRACE & GRACE-FO Tellus Land Mass Grid Groundwater Anomaly Adapter (GEE).
Current Active Dataset IDs:
- Primary: NASA/GRACE/MASS_GRIDS_V04/MASCON_CRI (Covers GRACE & GRACE-FO through late 2024)
- Alternative: NASA/GRACE/MASS_GRIDS_V04/LAND (Spherical harmonics)
Band: lwe_thickness (Liquid Water Equivalent thickness in cm).
Computes regional (3x3 degree) monthly anomalies and decadal depletion trend (cm/year).
Resolution Note: ~300 km basin-scale gravimetry; NOT field-scale groundwater.
Freshness constraint: Data observed through 2024-09-30. Restricted strictly to long-term trends.
"""
import time
import datetime as dt
from typing import Optional, Dict, Any

from app.adapters.base import SourceResult
from app.adapters.gee_auth import init_ee

DATASET_ID = "NASA/GRACE/MASS_GRIDS_V04/MASCON_CRI"
FALLBACK_ID = "NASA/GRACE/MASS_GRIDS_V04/LAND"


def fetch_grace(lat: float, lon: float) -> SourceResult:
    """
    Fetch regional (3x3 degree) GRACE-FO groundwater mass anomaly series and calculate linear trend.
    """
    t0 = time.time()
    success, err_msg = init_ee()
    if not success:
        return SourceResult(
            source="NASA GRACE/GRACE-FO (GEE)",
            dataset_id=DATASET_ID,
            status="SKIPPED-no-credentials",
            latency_ms=int((time.time() - t0) * 1000),
            error=err_msg
        )

    try:
        import ee
        # Regional 3x3 degree bounding box for ~300 km gravimetric footprint
        region = ee.Geometry.BBox(lon - 1.5, lat - 1.5, lon + 1.5, lat + 1.5)

        target_id = DATASET_ID
        col = ee.ImageCollection(target_id).select("lwe_thickness").filterBounds(region)
        size = col.size().getInfo()

        if size == 0:
            target_id = FALLBACK_ID
            col = ee.ImageCollection(target_id).select("lwe_thickness").filterBounds(region)
            size = col.size().getInfo()

        if size == 0:
            return SourceResult(
                source="NASA GRACE/GRACE-FO (GEE)",
                dataset_id=target_id,
                status="unavailable",
                latency_ms=int((time.time() - t0) * 1000),
                error="No GRACE mass grid observations found over coordinates in " + target_id
            )

        latest_img = col.sort("system:time_start", False).first()
        time_start = latest_img.get("system:time_start").getInfo()
        obs_date = dt.datetime.utcfromtimestamp(time_start / 1000.0).strftime("%Y-%m-%d")

        latest_val = latest_img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=region,
            scale=25000
        ).getInfo().get("lwe_thickness")

        # Trend estimation over last 10 years using ee.Reducer.linearFit
        def add_time(img):
            time_band = ee.Image.constant(img.date().difference(ee.Date('2000-01-01'), 'year')).toDouble().rename('time')
            return img.addBands(time_band)

        start_trend = (dt.date.today() - dt.timedelta(days=3650)).isoformat()
        trend_col = col.filterDate(start_trend, dt.date.today().isoformat()).map(add_time)
        fit = trend_col.select(['time', 'lwe_thickness']).reduce(ee.Reducer.linearFit())
        trend_stats = fit.reduceRegion(reducer=ee.Reducer.mean(), geometry=region, scale=50000).getInfo()
        slope_cm_yr = trend_stats.get('scale')

        latency = int((time.time() - t0) * 1000)
        return SourceResult(
            source="NASA GRACE/GRACE-FO (GEE)",
            dataset_id=target_id,
            status="live",
            observed_through=obs_date,
            freshness_note="Latest release (2024-09). Regional total water storage trend (~300 km). Restricted strictly to decadal trend analysis; NOT indicative of parcel-scale groundwater table.",
            latency_ms=latency,
            n_obs=size,
            units="trend: cm/year, anomaly: cm LWE",
            data={
                "current_anomaly_cm": round(float(latest_val), 2) if latest_val is not None else None,
                "regional_total_water_storage_trend_cm_per_year": round(float(slope_cm_yr), 2) if slope_cm_yr is not None else None,
                "depletion_trend_cm_per_year": round(float(slope_cm_yr), 2) if slope_cm_yr is not None else None,
                "spatial_resolution": "Regional (~300 km, through 2024-09)",
                "observations_count": size,
                "release_tag": "2024-09 Release"
            }
        )

    except Exception as e:
        latency = int((time.time() - t0) * 1000)
        return SourceResult(
            source="NASA GRACE/GRACE-FO (GEE)",
            dataset_id=DATASET_ID,
            status="unavailable",
            latency_ms=latency,
            error=f"GEE GRACE execution exception: {str(e)}"
        )
