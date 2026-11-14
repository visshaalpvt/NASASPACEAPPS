"""
NASA GPM IMERG Precipitation Adapter (GEE).
Dataset ID: NASA/GPM_L3/IMERG_V07
Band: precipitation (calibrated rate in mm/hr, 30-minute intervals).
Computes 24h, 72h, and 30-day accumulation sums.
"""
import time
import datetime as dt
from typing import Optional, Dict, Any

from app.adapters.base import SourceResult
from app.adapters.gee_auth import init_ee
from app.adapters.cache import get_cached_baseline, set_cached_baseline

DATASET_ID = "NASA/GPM_L3/IMERG_V07"
DATASET_MONTHLY_ID = "NASA/GPM_L3/IMERG_MONTHLY_V07"


def fetch_gpm_imerg(lat: float, lon: float, days_back: int = 30, end_date: Optional[dt.date] = None) -> SourceResult:
    """
    Fetch live NASA GPM IMERG precipitation accumulations via Earth Engine.
    Aligned with NASA POWER's calendar window (ending at today - 5d by default).
    """
    t0 = time.time()
    success, err_msg = init_ee()
    if not success:
        return SourceResult(
            source="NASA GPM IMERG (GEE)",
            dataset_id=DATASET_ID,
            status="SKIPPED-no-credentials",
            latency_ms=int((time.time() - t0) * 1000),
            error=err_msg
        )

    try:
        import ee
        point = ee.Geometry.Point([lon, lat])
        if end_date is None:
            # Default to match NASA POWER MERRA-2 lag (today - 5 days)
            end_date = dt.date.today() - dt.timedelta(days=5)

        start_date = end_date - dt.timedelta(days=days_back - 1)
        # GEE filterDate end is exclusive, so add 1 day to include end_date completely
        ee_end_str = (end_date + dt.timedelta(days=1)).isoformat()
        ee_start_str = start_date.isoformat()

        col = (
            ee.ImageCollection(DATASET_ID)
            .filterBounds(point)
            .filterDate(ee_start_str, ee_end_str)
            .select("precipitation")
        )

        size = col.size().getInfo()
        if size == 0:
            return SourceResult(
                source="NASA GPM IMERG (GEE)",
                dataset_id=DATASET_ID,
                status="unavailable",
                latency_ms=int((time.time() - t0) * 1000),
                error=f"No IMERG scenes found in window {ee_start_str} to {ee_end_str}"
            )

        latest_img = col.sort("system:time_start", False).first()
        time_start = latest_img.get("system:time_start").getInfo()
        obs_date = dt.datetime.utcfromtimestamp(time_start / 1000.0).strftime("%Y-%m-%d %H:%M")

        # 30-min rate in mm/hr -> multiply by 0.5 to get mm per 30 min interval
        rain_sum_30d = col.map(lambda img: img.multiply(0.5)).sum().reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=10000
        ).getInfo().get("precipitation", 0.0)

        # 72h accumulation (3 days ending on end_date)
        start_72h = end_date - dt.timedelta(days=2)
        col_72h = col.filterDate(start_72h.isoformat(), ee_end_str)
        rain_sum_72h = col_72h.map(lambda img: img.multiply(0.5)).sum().reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=10000
        ).getInfo().get("precipitation", 0.0)

        # 2001-2024 Multi-Year IMERG Baseline Percentile (Monthly product calibration)
        target_doy = end_date.timetuple().tm_yday
        cached_hist = get_cached_baseline("imerg_30d", lat, lon, target_doy)
        imerg_pct = None
        imerg_hist_mean = None
        n_imerg_years = 0

        if cached_hist is not None:
            hist_vals = cached_hist
            n_imerg_years = len(hist_vals)
        else:
            hist_vals = []
            try:
                monthly_col = ee.ImageCollection(DATASET_MONTHLY_ID).filterBounds(point).select("precipitation")
                # Determine relevant months for 30-day window ending on end_date
                # Month m and previous month m_prev
                m_curr = end_date.month
                m_prev = (end_date - dt.timedelta(days=28)).month
                day_ratio = end_date.day / 30.0

                years = ee.List.sequence(2001, 2024)
                def get_annual_window_rain(y):
                    y = ee.Number(y)
                    img_curr = monthly_col.filter(ee.Filter.calendarRange(y, y, "year")).filter(ee.Filter.calendarRange(m_curr, m_curr, "month")).first()
                    img_prev = monthly_col.filter(ee.Filter.calendarRange(y, y, "year")).filter(ee.Filter.calendarRange(m_prev, m_prev, "month")).first()
                    # Monthly rate is in mm/hr; multiply by hours in month (720h)
                    rain_c = ee.Image(img_curr).multiply(720.0)
                    rain_p = ee.Image(img_prev).multiply(720.0)
                    rain_30d = rain_c.multiply(day_ratio).add(rain_p.multiply(1.0 - day_ratio))
                    return rain_30d.reduceRegion(reducer=ee.Reducer.mean(), geometry=point, scale=10000).get("precipitation")

                raw_vals = years.map(get_annual_window_rain).getInfo()
                hist_vals = [round(float(v), 2) for v in raw_vals if v is not None]
                n_imerg_years = len(hist_vals)
                if hist_vals:
                    set_cached_baseline("imerg_30d", lat, lon, target_doy, hist_vals)
            except Exception as e_hist:
                pass

        if hist_vals and rain_sum_30d is not None:
            imerg_hist_mean = round(sum(hist_vals) / len(hist_vals), 1)
            cur_r = float(rain_sum_30d)
            rank = (sum(1 for x in hist_vals if x < cur_r) + 0.5 * sum(1 for x in hist_vals if abs(x - cur_r) < 1.0)) / len(hist_vals)
            imerg_pct = round(rank * 100.0, 1)

        latency = int((time.time() - t0) * 1000)
        return SourceResult(
            source="NASA GPM IMERG (GEE)",
            dataset_id=DATASET_ID,
            status="live",
            observed_through=obs_date,
            freshness_note=f"30-minute calibrated multi-satellite precipitation rate (observed through {obs_date} UTC, window: {start_date} to {end_date})",
            latency_ms=latency,
            n_obs=size,
            units="precipitation: mm",
            data={
                "rain_30d_mm": round(float(rain_sum_30d), 2),
                "rain_72h_mm": round(float(rain_sum_72h), 2),
                "imerg_30d_percentile": imerg_pct,
                "imerg_historical_mean_mm": imerg_hist_mean,
                "imerg_baseline_years": n_imerg_years,
                "window_start": start_date.isoformat(),
                "window_end": end_date.isoformat(),
                "scenes_processed": size
            }
        )

    except Exception as e:
        latency = int((time.time() - t0) * 1000)
        return SourceResult(
            source="NASA GPM IMERG (GEE)",
            dataset_id=DATASET_ID,
            status="unavailable",
            latency_ms=latency,
            error=f"GEE IMERG execution exception: {str(e)}"
        )
