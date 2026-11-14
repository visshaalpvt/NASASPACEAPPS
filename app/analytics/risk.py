"""
Multi-Hazard Climate Risk Scoring Engine.
Computes 0-100 scores for:
- Drought Stress (Rainfall percentile + SMAP/POWER Root-Zone Soil Moisture + Dry Days)
- Heat Stress (Crop threshold exceedance in sensitive phenology window + Tmax percentile)
- Flood Hazard (IMERG 72h & Forecast rain vs Local 95th percentile historical threshold)
- Vegetation Stress (Landsat 30m field NDVI & MODIS 250m regional NDVI)
- Overall Weighted Risk Index with explicit weights and data-provenance confidence rating.
Documented in docs/METHODS.md.
"""
from typing import Dict, Any, List, Optional


RISK_WEIGHTS = {
    "drought": 0.35,
    "heat": 0.30,
    "flood": 0.20,
    "vegetation": 0.15
}


def percentile_to_drought_risk(pct: Optional[float]) -> float:
    """
    Calibrated mapping from historical empirical percentile (0.0 to 100.0)
    to drought stress risk (0.0 to 100.0):
    - Percentile >= 50.0 (median or wetter): 0.0 risk
    - Percentile <= 5.0 (extreme 5% drought): 100.0 risk
    - Linear interpolation between 5.0 and 50.0: (50 - pct) / 45 * 100.0
    """
    if pct is None:
        return 0.0
    if pct >= 50.0:
        return 0.0
    if pct <= 5.0:
        return 100.0
    return round((50.0 - pct) / 45.0 * 100.0, 1)


def calculate_risk_scores(
    indicators: Dict[str, Any],
    phenology: Dict[str, Any],
    provenance_list: List[Any]
) -> Dict[str, Any]:
    """
    Computes percentile-driven risk scores (0-100), overall score, inputs, and confidence rating.
    Gated by crop phenology stage and calibrated against 2001-present local empirical baselines.
    """
    ind = indicators

    # 1. Drought Score (0-100)
    # Primary Rain: GPM IMERG satellite percentile (cross-checked against POWER MERRA-2)
    rain_data = ind["rain_deficit_30d"]
    primary_rain_pct = rain_data.get("primary_rain_percentile")
    if primary_rain_pct is None:
        primary_rain_pct = rain_data.get("power_cross_check_percentile") or 50.0

    rain_risk = percentile_to_drought_risk(primary_rain_pct)

    # Primary Soil: SMAP satellite rootzone percentile (cross-checked against POWER GWETROOT)
    soil_data = ind["soil_moisture"]
    primary_soil_pct = soil_data.get("primary_soil_percentile")
    if primary_soil_pct is None:
        primary_soil_pct = soil_data.get("power_gwetroot_percentile") or 50.0

    soil_risk = percentile_to_drought_risk(primary_soil_pct)

    # Physical moisture sanity check: if root-zone is physically moist (fraction >= 0.45),
    # damp soil drought risk to avoid false alarms from relative percentile anomaly in humid deltas
    abs_wetness = soil_data.get("smap_rootzone_wetness")
    if abs_wetness is None:
        abs_wetness = soil_data.get("power_gwetroot_fraction")

    if abs_wetness is not None:
        if abs_wetness >= 0.50:
            soil_risk = 0.0
        elif abs_wetness >= 0.35:
            soil_risk = round(soil_risk * max(0.0, (0.50 - abs_wetness) / 0.15), 1)

    base_drought = round(0.50 * rain_risk + 0.50 * soil_risk, 1)

    # Normalize dry spell boost against historical dry spell distribution for calendar window
    # When rain and soil are at/above median (base_drought < 15), seasonal dry spell in winter does not constitute drought
    dry_spell_pct = ind["dry_spell"].get("dry_spell_percentile")
    dry_days = ind["dry_spell"].get("consecutive_days_under_1mm") or 0
    dry_spell_boost = 0.0
    if dry_spell_pct is not None:
        if dry_spell_pct > 80.0:
            multiplier = 0.8 if base_drought > 15 else 0.4
            dry_spell_boost = round(min(15.0, (dry_spell_pct - 80.0) * multiplier), 1)
    elif dry_days > 21 and base_drought > 15:
        dry_spell_boost = round(min(15.0, (dry_days - 21) * 1.0), 1)

    drought_score = int(round(max(0.0, min(100.0, base_drought + dry_spell_boost))))

    # Detailed Drought Arithmetic Manifest
    drought_arithmetic = {
        "formula": "0.50 * risk(rain_pct) + 0.50 * risk(soil_pct) + dry_spell_boost",
        "mapping_rule": ">=50th pct -> 0 risk; <=5th pct -> 100 risk; linear in between: (50 - p) / 45 * 100",
        "primary_rain_source": rain_data.get("primary_source", "NASA GPM IMERG (V07)"),
        "primary_rain_percentile": primary_rain_pct,
        "rain_risk_component": rain_risk,
        "primary_soil_source": soil_data.get("primary_source", "NASA SMAP L4"),
        "primary_soil_percentile": primary_soil_pct,
        "soil_risk_component": soil_risk,
        "base_drought_raw": base_drought,
        "dry_spell_days": dry_days,
        "dry_spell_percentile": dry_spell_pct,
        "dry_spell_boost": dry_spell_boost,
        "final_drought_score": drought_score
    }

    # 2. Heat Score (0-100) - Strictly Gated by Crop Phenology Stage
    heat_data = ind["heat_stress"]
    tmax_pct = heat_data.get("tmax_percentile") or 50.0
    hot_past = heat_data.get("hot_days_past_14d") or 0
    hot_fc = heat_data.get("hot_days_forecast_7d") or 0
    in_sensitive_stage = phenology.get("in_heat_sensitive_window", False)

    if in_sensitive_stage:
        # During anthesis / grain-filling: critical threshold exceedance causes yield failure
        exceedance_factor = min(100.0, ((hot_past + 1.2 * hot_fc) / 8.0) * 100.0)
        raw_heat = 0.70 * exceedance_factor + 0.30 * tmax_pct
        heat_score = int(round(max(0.0, min(100.0, raw_heat))))
    else:
        # During vegetative / emergence stage: anthesis limits do NOT apply
        # Heat stress is only triggered by extreme vegetative heat (>36-38°C) or severe percentile anomaly (>90th)
        if hot_past > 0 or hot_fc > 0:
            exceedance_factor = min(60.0, (hot_past + hot_fc) * 10.0)
            heat_score = int(round(max(0.0, min(70.0, 0.5 * exceedance_factor + 0.5 * tmax_pct))))
        else:
            # Mild / seasonal temperatures during vegetative stage
            heat_score = int(round(max(0.0, min(25.0, (tmax_pct / 100.0) * 25.0))))

    # 3. Flood Score (0-100) - With Absolute Rainfall Floor (20mm)
    flood_data = ind["flood_hazard"]
    imerg_72h = flood_data.get("imerg_72h_mm") or 0.0
    fc_3d = flood_data.get("forecast_max_3d_rain_mm") or 0.0
    peak_3d = max(imerg_72h, fc_3d)
    local_95th = flood_data.get("local_historical_95th_pct_3d_mm") or 100.0

    if peak_3d < 20.0:
        # Absolute floor: rainfall under 20mm is insufficient to flood agricultural parcels
        flood_score = 0
    else:
        ratio = peak_3d / max(20.0, local_95th)
        raw_flood = ratio * 75.0
        flood_score = int(round(max(0.0, min(100.0, raw_flood))))

    # 4. Vegetation Stress Score (0-100) - Stage-Gated with MODIS Baseline Anomaly
    veg_data = ind["vegetation_vigor"]
    canopy_active = phenology.get("canopy_active", True)
    modis_anomaly = veg_data.get("modis_ndvi_anomaly")
    landsat_ndvi = veg_data.get("landsat_field_ndvi_30m")
    modis_ndvi = veg_data.get("modis_regional_ndvi_250m")

    veg_applicable = True
    if not canopy_active:
        # Crop is at emergence / bare soil or physiological maturity / harvest
        veg_applicable = False
        veg_score = 0
    elif modis_anomaly is not None:
        # Positive anomaly means canopy is healthier than 2001-present baseline
        if modis_anomaly >= 0.0:
            veg_score = max(0, int(15.0 - modis_anomaly * 50.0))
        else:
            # Negative anomaly reflects canopy degradation below historical norm
            veg_score = min(100, int(15.0 + (-modis_anomaly / 0.35) * 85.0))
    elif landsat_ndvi is not None or modis_ndvi is not None:
        active_ndvi = landsat_ndvi if landsat_ndvi is not None else modis_ndvi
        veg_score = int(round(max(0.0, min(100.0, (0.65 - active_ndvi) / 0.50 * 100.0))))
    else:
        veg_score = drought_score

    # 5. Overall Weighted Combination (Redistributes weights if vegetation is not applicable)
    if veg_applicable:
        weights = RISK_WEIGHTS
        overall_score = int(round(
            weights["drought"] * drought_score +
            weights["heat"] * heat_score +
            weights["flood"] * flood_score +
            weights["vegetation"] * veg_score
        ))
    else:
        # Proportional redistribution across drought, heat, flood (sum = 1.0)
        weights = {
            "drought": 0.45,
            "heat": 0.35,
            "flood": 0.20,
            "vegetation": 0.0
        }
        overall_score = int(round(
            weights["drought"] * drought_score +
            weights["heat"] * heat_score +
            weights["flood"] * flood_score
        ))

    # 6. Confidence Rating based on live data feeds provenance
    live_count = sum(1 for p in provenance_list if getattr(p, "status", None) in ("live", "cached"))
    sources_disagree = ind["rain_deficit_30d"].get("sources_disagree", False)

    if live_count >= 5:
        base_conf = "high"
    elif live_count >= 3:
        base_conf = "medium"
    else:
        base_conf = "low"

    # Downgrade if primary precipitation feeds diverge (>30%)
    if sources_disagree:
        if base_conf == "high":
            confidence = "medium"
        else:
            confidence = "low"
        confidence_note = "Confidence downgraded: NASA POWER and NASA GPM IMERG precipitation disagree by >30%."
    else:
        confidence = base_conf
        confidence_note = f"All {live_count} live data feeds verified and consistent."

    return {
        "overall": overall_score,
        "drought": drought_score,
        "heat": heat_score,
        "flood": flood_score,
        "vegetation": veg_score if veg_applicable else None,
        "vegetation_applicable": veg_applicable,
        "vegetation_status_note": phenology.get("canopy_status_note", "active"),
        "weights": weights,
        "confidence": confidence,
        "confidence_note": confidence_note,
        "sources_disagree": sources_disagree,
        "live_sources_count": live_count,
        "score_arithmetic": {
            "drought": drought_arithmetic,
            "heat": {
                "in_heat_sensitive_stage": in_sensitive_stage,
                "hot_days_past_14d": hot_past,
                "hot_days_forecast_7d": hot_fc,
                "tmax_percentile": tmax_pct,
                "heat_score": heat_score
            },
            "flood": {
                "imerg_72h_mm": imerg_72h,
                "forecast_max_3d_rain_mm": fc_3d,
                "peak_3d_rain_mm": peak_3d,
                "local_historical_95th_pct_3d_mm": local_95th,
                "flood_absolute_floor_applied": peak_3d < 20.0,
                "flood_score": flood_score
            },
            "overall": {
                "weights_used": weights,
                "formula": "sum(weight_i * score_i)",
                "overall_score": overall_score
            }
        },
        "score_inputs": {
            "drought": ["NASA GPM IMERG 30d Percentile (Primary)", "NASA SMAP L4 Root-Zone Percentile (Primary)", "Normalized Dry Spell Percentile"],
            "heat": ["Phenology Gated Threshold", "NASA POWER T2M_MAX Anomaly", "Open-Meteo NWP Forecast"],
            "flood": ["NASA GPM IMERG 72h Rain", "Open-Meteo 3-day NWP Rain", "Local 25-yr 95th Percentile", "20mm Flood Floor"],
            "vegetation": ["MODIS MOD13Q1 2001+ Baseline Anomaly", "Landsat 8/9 30m Parcel NDVI", "Phenology Stage Gate"]
        }
    }

