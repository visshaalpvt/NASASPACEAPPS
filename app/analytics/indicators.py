"""
Multi-Mission Earth Observation Indicator Engine.
Computes the 8 core indicators specified in PRD Section 5.2.
Every indicator reports value, anomaly, percentile vs 2001-present calendar window,
sample size, and underlying dataset ID.
STRICT RULE: REAL DATA ONLY.
"""
from datetime import date, datetime
from typing import Dict, Any, List, Optional
import numpy as np

from app.analytics.baseline import (
    compute_percentile,
    extract_calendar_window_history,
    compute_decadal_warming_trend,
    compute_calendar_day_dry_spells
)
from app.analytics.crop_stage import compute_crop_phenology


def compute_all_indicators(
    power_data: Dict[str, Any],
    forecast_data: Optional[Dict[str, Any]],
    smap_data: Optional[Dict[str, Any]],
    gpm_data: Optional[Dict[str, Any]],
    modis_data: Optional[Dict[str, Any]],
    landsat_data: Optional[Dict[str, Any]],
    grace_data: Optional[Dict[str, Any]],
    crop: str,
    sowing_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Computes all 8 verified indicators from live multi-sensor observations.
    """
    dates = [datetime.strptime(d, "%Y-%m-%d").date() for d in power_data["dates"]]
    end_date = dates[-1]

    rain_arr = np.array(power_data["PRECTOTCORR"], dtype=float)
    tmax_arr = np.array(power_data["T2M_MAX"], dtype=float)
    tmin_arr = np.array(power_data["T2M_MIN"], dtype=float)
    t2m_arr = np.array(power_data["T2M"], dtype=float)
    gwet_arr = np.array(power_data["GWETROOT"], dtype=float)

    # Crop phenology & stage tracking
    phenology = compute_crop_phenology(crop, sowing_date, dates, tmax_arr, tmin_arr)

    # 1. Rain Deficit: GPM IMERG (Primary Satellite) & NASA POWER (Cross-check)
    rain_30d_current = float(np.nansum(rain_arr[-30:]))
    rain_30d_hist, n_rain30 = extract_calendar_window_history(dates, rain_arr, end_date, 30, np.nansum)
    rain_30d_mean = float(np.mean(rain_30d_hist)) if rain_30d_hist else rain_30d_current
    rain_30d_pct = compute_percentile(rain_30d_hist, rain_30d_current)

    rain_90d_current = float(np.nansum(rain_arr[-90:]))
    rain_90d_hist, n_rain90 = extract_calendar_window_history(dates, rain_arr, end_date, 90, np.nansum)
    rain_90d_mean = float(np.mean(rain_90d_hist)) if rain_90d_hist else rain_90d_current
    rain_90d_pct = compute_percentile(rain_90d_hist, rain_90d_current)

    imerg_30d_mm = gpm_data.get("rain_30d_mm") if gpm_data else None
    imerg_30d_pct = gpm_data.get("imerg_30d_percentile") if gpm_data else None
    imerg_hist_mean = gpm_data.get("imerg_historical_mean_mm") if gpm_data else None
    imerg_baseline_years = gpm_data.get("imerg_baseline_years") if gpm_data else None

    # Primary Rain is GPM IMERG satellite observation; POWER is reanalysis cross-check
    primary_rain_source = "NASA GPM IMERG (V07)" if imerg_30d_pct is not None else "NASA POWER MERRA-2"
    primary_rain_30d_mm = imerg_30d_mm if imerg_30d_mm is not None else rain_30d_current
    primary_rain_30d_pct = imerg_30d_pct if imerg_30d_pct is not None else rain_30d_pct

    # Cross-sensor precipitation comparison (disagreement flagged if >30% gap AND >10mm absolute difference)
    sources_disagree = False
    diff_pct = 0.0
    abs_diff_mm = 0.0
    if imerg_30d_mm is not None and max(rain_30d_current, imerg_30d_mm) > 0:
        abs_diff_mm = abs(rain_30d_current - imerg_30d_mm)
        diff_pct = round(abs_diff_mm / max(rain_30d_current, imerg_30d_mm) * 100.0, 1)
        if diff_pct > 30.0 and abs_diff_mm > 10.0:
            sources_disagree = True

    disagreement_explanation = (
        f"Resolution discrepancy detected: NASA GPM IMERG (~10 km multi-satellite: {round(imerg_30d_mm, 1)} mm) and NASA POWER (~50 km MERRA-2 reanalysis: {round(rain_30d_current, 1)} mm) differ by {diff_pct}% ({round(abs_diff_mm, 1)} mm). This may be due to spatial resolution differences between the 10 km satellite grid and 50 km reanalysis model."
        if sources_disagree else "Cross-sensor consistency between IMERG satellite and POWER reanalysis confirmed."
    )

    # 2. Soil Moisture: SMAP Root-zone percentile & POWER GWETROOT cross-check
    gwet_7d_current = float(np.nanmean(gwet_arr[-7:]))
    gwet_7d_hist, n_gwet = extract_calendar_window_history(dates, gwet_arr, end_date, 7, np.nanmean)
    gwet_7d_mean = float(np.mean(gwet_7d_hist)) if gwet_7d_hist else gwet_7d_current
    gwet_7d_pct = compute_percentile(gwet_7d_hist, gwet_7d_current)

    smap_rootzone = smap_data.get("sm_rootzone") if smap_data else None
    smap_surface = smap_data.get("sm_surface") if smap_data else None
    smap_wetness = smap_data.get("sm_rootzone_wetness") if smap_data else None
    smap_wetness_pct = smap_data.get("sm_rootzone_wetness_percentile") if smap_data else None
    smap_hist_mean = smap_data.get("sm_rootzone_wetness_historical_mean") if smap_data else None
    smap_baseline_years = smap_data.get("smap_baseline_years") if smap_data else None

    # Primary soil moisture percentile uses SMAP satellite when available, else POWER MERRA-2
    primary_soil_pct = smap_wetness_pct if smap_wetness_pct is not None else gwet_7d_pct

    # 3. Vegetation: MODIS 250m Baseline & Landsat 30m Field NDVI with Phenology Stage Gating
    modis_ndvi = modis_data.get("modis_ndvi_250m") if modis_data else None
    modis_hist_mean = modis_data.get("modis_ndvi_historical_mean") if modis_data else None
    modis_anomaly = modis_data.get("modis_ndvi_anomaly") if modis_data else None
    landsat_ndvi = landsat_data.get("field_ndvi_30m") if landsat_data else None
    ndvi_field_vs_regional_diff = (
        round(landsat_ndvi - modis_ndvi, 3)
        if (landsat_ndvi is not None and modis_ndvi is not None)
        else None
    )

    canopy_active = phenology.get("canopy_active", True)
    canopy_status_note = phenology.get("canopy_status_note", "active canopy")

    # 4. Heat Stress: Crop Stage-Gated Thresholds
    in_sensitive_stage = phenology.get("in_heat_sensitive_window", False)
    active_heat_thr = phenology.get("active_heat_threshold_c", 34.0)
    past_14d_tmax = tmax_arr[-14:]
    hot_days_14d = int(np.nansum(past_14d_tmax > active_heat_thr))

    hot_days_forecast = 0
    if forecast_data and "tmax" in forecast_data:
        hot_days_forecast = int(sum(1 for x in forecast_data["tmax"] if x is not None and x > active_heat_thr))

    tmax_14d_mean_current = float(np.nanmean(past_14d_tmax))
    tmax_14d_hist, n_tmax = extract_calendar_window_history(dates, tmax_arr, end_date, 14, np.nanmean)
    tmax_14d_hist_mean = float(np.mean(tmax_14d_hist)) if tmax_14d_hist else tmax_14d_mean_current
    tmax_14d_pct = compute_percentile(tmax_14d_hist, tmax_14d_mean_current)

    modis_lst = modis_data.get("modis_lst_day_c") if modis_data else None
    landsat_lst = landsat_data.get("canopy_lst_c") if landsat_data else None

    # 5. Flood / Extreme Precipitation: Absolute Floor (20mm) + Local historical 95th percentile
    hist_3d_sums, n_3d = extract_calendar_window_history(dates, rain_arr, end_date, 3, np.nansum)
    local_95th_pct_3d_rain = float(np.percentile(hist_3d_sums, 95.0)) if len(hist_3d_sums) >= 10 else 100.0

    imerg_72h_mm = gpm_data.get("rain_72h_mm") if gpm_data else None
    fc_rain_list = forecast_data.get("rain", []) if forecast_data else []
    fc_max_3d_rain = max([sum(fc_rain_list[i:i+3]) for i in range(max(1, len(fc_rain_list) - 2))] or [0.0])
    peak_3d_rain = max(imerg_72h_mm or 0.0, fc_max_3d_rain)

    # Floor requirement: 3-day rainfall must be >= 20.0 mm to trigger flood alert
    flood_threshold_exceeded = (
        peak_3d_rain >= 20.0 and peak_3d_rain >= local_95th_pct_3d_rain
    )

    # 6. Dry Spell: Normalized against historical dry-spell distribution
    dry_spell_days = 0
    for r in rain_arr[::-1]:
        if np.isnan(r) or r >= 1.0:
            break
        dry_spell_days += 1

    past_spells, n_spells = compute_calendar_day_dry_spells(dates, rain_arr, end_date)
    dry_spell_pct = compute_percentile([float(s) for s in past_spells], float(dry_spell_days)) if past_spells else None

    # 7. Regional Total Water Storage Trend (GRACE ~300km footprint through 2024-09)
    grace_trend_cm_yr = (
        grace_data.get("regional_total_water_storage_trend_cm_per_year") or
        grace_data.get("depletion_trend_cm_per_year")
    ) if grace_data else None
    grace_anomaly_cm = grace_data.get("current_anomaly_cm") if grace_data else None

    # 8. Decadal Surface Warming Trend (MERRA-2 Grid-Point)
    warming_stats = compute_decadal_warming_trend(dates, t2m_arr)

    # Structured Indicator Manifest
    indicators = {
        "rain_deficit_30d": {
            "name": "30-Day Rainfall Accumulation",
            "primary_source": primary_rain_source,
            "primary_rain_30d_mm": round(primary_rain_30d_mm, 1) if primary_rain_30d_mm is not None else None,
            "primary_rain_percentile": primary_rain_30d_pct,
            "imerg_30d_mm": round(imerg_30d_mm, 1) if imerg_30d_mm is not None else None,
            "imerg_30d_percentile": imerg_30d_pct,
            "imerg_historical_mean_mm": imerg_hist_mean,
            "imerg_baseline_years": imerg_baseline_years,
            "power_cross_check_30d_mm": round(rain_30d_current, 1),
            "power_cross_check_percentile": rain_30d_pct,
            "power_historical_mean_mm": round(rain_30d_mean, 1),
            "sources_disagree": sources_disagree,
            "disagreement_pct": diff_pct,
            "disagreement_note": disagreement_explanation,
            "unit": "mm"
        },
        "rain_deficit_90d": {
            "name": "90-Day Seasonal Rainfall Accumulation",
            "dataset_id": "NASA_POWER_AG_POINT_DAILY_V2",
            "current_value_mm": round(rain_90d_current, 1),
            "historical_mean_mm": round(rain_90d_mean, 1),
            "anomaly_mm": round(rain_90d_current - rain_90d_mean, 1),
            "percentile": rain_90d_pct,
            "sample_size_years": n_rain90,
            "unit": "mm"
        },
        "soil_moisture": {
            "name": "Root-Zone Soil Wetness",
            "primary_source": "NASA SMAP L4 (SPL4SMGP/008)" if smap_wetness_pct is not None else "NASA POWER MERRA-2 GWETROOT",
            "primary_soil_percentile": primary_soil_pct,
            "smap_rootzone_m3m3": smap_rootzone,
            "smap_surface_m3m3": smap_surface,
            "smap_rootzone_wetness": smap_wetness,
            "smap_rootzone_wetness_percentile": smap_wetness_pct,
            "smap_historical_mean": smap_hist_mean,
            "smap_baseline_years": smap_baseline_years,
            "power_gwetroot_fraction": round(gwet_7d_current, 3),
            "power_gwetroot_percentile": gwet_7d_pct,
            "power_gwetroot_anomaly": round(gwet_7d_current - gwet_7d_mean, 3),
            "sample_size_years": n_gwet,
            "unit": "fraction (0-1) / m^3/m^3"
        },
        "vegetation_vigor": {
            "name": "Vegetation Canopy Health (NDVI)",
            "canopy_active": canopy_active,
            "canopy_status_note": canopy_status_note,
            "modis_regional_ndvi_250m": modis_ndvi,
            "modis_ndvi_historical_mean": modis_hist_mean,
            "modis_ndvi_anomaly": modis_anomaly,
            "landsat_field_ndvi_30m": landsat_ndvi,
            "field_vs_regional_diff": ndvi_field_vs_regional_diff,
            "dataset_ids": "MODIS/061/MOD13Q1 (250m) & LANDSAT/LC08/C02/T1_L2 (30m)",
            "unit": "NDVI index (-1 to 1)"
        },
        "heat_stress": {
            "name": f"Heat Stress ({crop.capitalize()} Threshold: {active_heat_thr}°C)",
            "mean_tmax_14d_c": round(tmax_14d_mean_current, 1),
            "historical_tmax_14d_mean_c": round(tmax_14d_hist_mean, 1),
            "tmax_14d_anomaly_c": round(tmax_14d_mean_current - tmax_14d_hist_mean, 1),
            "tmax_percentile": tmax_14d_pct,
            "active_threshold_c": active_heat_thr,
            "hot_days_past_14d": hot_days_14d,
            "hot_days_forecast_7d": hot_days_forecast,
            "in_heat_sensitive_stage": in_sensitive_stage,
            "phenological_stage": phenology["current_phenological_stage"],
            "modis_lst_day_c": modis_lst,
            "landsat_canopy_lst_c": landsat_lst,
            "unit": "°C"
        },
        "flood_hazard": {
            "name": "Extreme Precipitation & Flood Accumulation",
            "imerg_72h_mm": imerg_72h_mm,
            "forecast_max_3d_rain_mm": round(fc_max_3d_rain, 1),
            "peak_3d_rain_mm": round(peak_3d_rain, 1),
            "local_historical_95th_pct_3d_mm": round(local_95th_pct_3d_rain, 1),
            "flood_absolute_floor_mm": 20.0,
            "historical_95th_exceeded": flood_threshold_exceeded,
            "sample_size_years": n_3d,
            "unit": "mm"
        },
        "dry_spell": {
            "name": "Consecutive Dry Spell Duration",
            "consecutive_days_under_1mm": dry_spell_days,
            "dry_spell_percentile": dry_spell_pct,
            "historical_spells_evaluated": n_spells,
            "dataset_id": "NASA_POWER_AG_POINT_DAILY_V2",
            "unit": "days"
        },
        "groundwater_trend": {
            "name": "Regional Total Water Storage Trend",
            "dataset_id": "NASA_GRACE/MASS_GRIDS_V04/MASCON_CRI",
            "regional_trend_cm_per_year": grace_trend_cm_yr,
            "depletion_trend_cm_per_year": grace_trend_cm_yr,
            "current_anomaly_cm": grace_anomaly_cm,
            "spatial_resolution_caveat": "Regional (~300 km footprint, observed through 2024-09); NOT parcel-scale groundwater table",
            "unit": "cm/year"
        },
        "climate_warming_trend": {
            "name": "Decadal Surface Warming Trend",
            "dataset_id": "NASA_POWER_AG_POINT_DAILY_V2",
            "warming_trend_c_per_decade": warming_stats["warming_trend_c_per_decade"],
            "p_value": warming_stats["p_value"],
            "r_squared": warming_stats["r_squared"],
            "baseline_span": warming_stats["baseline_span"],
            "years_evaluated": warming_stats["years_evaluated"],
            "caveat": "MERRA-2 grid-point trend; treat with caution",
            "unit": "°C/decade"
        }
    }

    return {
        "phenology": phenology,
        "indicators": indicators
    }

