"""
Crop Stage and Phenology Modeling via Growing Degree Days (GDD).
Calculates accumulated thermal time (GDD) using real observed daily temperatures from NASA POWER:
Daily GDD = max(0.0, (Tmax + Tmin)/2 - Tbase)
Thresholds for terminal heat (Rice 34°C, Wheat 31°C, Maize 35°C) apply specifically
during their critical reproductive/flowering/grain-filling windows.
"""
from datetime import date, datetime
from typing import Dict, Any, List, Optional
import numpy as np

CROP_SPECS = {
    "rice": {
        "t_base": 10.0,
        "critical_heat_threshold_c": 34.0,
        "vegetative_heat_threshold_c": 38.0,
        "min_canopy_gdd": 450.0,
        "max_canopy_gdd": 1850.0,
        "stages": [
            {"name": "Germination & Vegetative (Tillering)", "gdd_min": 0, "gdd_max": 850, "heat_sensitive": False},
            {"name": "Reproductive (Panicle Initiation to Anthesis)", "gdd_min": 850, "gdd_max": 1400, "heat_sensitive": True},
            {"name": "Grain Filling & Milk Stage", "gdd_min": 1400, "gdd_max": 1850, "heat_sensitive": True},
            {"name": "Ripening & Physiological Maturity", "gdd_min": 1850, "gdd_max": 99999, "heat_sensitive": False}
        ],
        "default_sowing": {"kharif": (7, 1), "rabi_boro": (1, 15)}
    },
    "wheat": {
        "t_base": 5.0,
        "critical_heat_threshold_c": 31.0,
        "vegetative_heat_threshold_c": 36.0,
        "min_canopy_gdd": 350.0,
        "max_canopy_gdd": 1450.0,
        "stages": [
            {"name": "Crown Root & Vegetative Tillering", "gdd_min": 0, "gdd_max": 650, "heat_sensitive": False},
            {"name": "Stem Elongation & Booting", "gdd_min": 650, "gdd_max": 1050, "heat_sensitive": False},
            {"name": "Pre-Anthesis & Flowering (Terminal Heat Window)", "gdd_min": 1050, "gdd_max": 1450, "heat_sensitive": True},
            {"name": "Grain Filling & Dough Stage", "gdd_min": 1450, "gdd_max": 99999, "heat_sensitive": True}
        ],
        "default_sowing": {"rabi": (11, 10)}
    },
    "maize": {
        "t_base": 10.0,
        "critical_heat_threshold_c": 35.0,
        "vegetative_heat_threshold_c": 38.0,
        "min_canopy_gdd": 300.0,
        "max_canopy_gdd": 1400.0,
        "stages": [
            {"name": "Emergence & Early Vegetative (V1-V6)", "gdd_min": 0, "gdd_max": 450, "heat_sensitive": False},
            {"name": "Rapid Vegetative Growth (V7-V14)", "gdd_min": 450, "gdd_max": 950, "heat_sensitive": False},
            {"name": "Tasseling & Silking (Reproductive)", "gdd_min": 950, "gdd_max": 1400, "heat_sensitive": True},
            {"name": "Grain Fill & Dent Stage", "gdd_min": 1400, "gdd_max": 99999, "heat_sensitive": False}
        ],
        "default_sowing": {"kharif": (6, 25), "rabi": (10, 20)}
    }
}


def get_default_sowing_date(crop: str, ref_date: date) -> date:
    """
    Returns typical regional sowing date for South Asian agro-ecosystem
    relative to reference observation date.
    """
    crop = crop.lower()
    if crop == "wheat":
        # Rabi crop sown in November
        if ref_date.month < 5:
            # Current winter season started last November
            return date(ref_date.year - 1, 11, 10)
        else:
            return date(ref_date.year, 11, 10)
    elif crop == "rice":
        # Check Kharif vs Boro season
        if 5 <= ref_date.month <= 12:
            return date(ref_date.year, 7, 1)
        else:
            return date(ref_date.year, 1, 15)
    else:  # maize
        if 5 <= ref_date.month <= 10:
            return date(ref_date.year, 6, 25)
        else:
            return date(ref_date.year if ref_date.month >= 10 else ref_date.year - 1, 10, 20)


def compute_crop_phenology(
    crop: str,
    sowing_date: Optional[date],
    dates: List[date],
    tmax_arr: np.ndarray,
    tmin_arr: np.ndarray
) -> Dict[str, Any]:
    """
    Computes accumulated GDD from sowing date to current observation date,
    determines current phenological stage, and checks whether crop is in heat-sensitive window.
    """
    crop_lower = crop.lower()
    spec = CROP_SPECS.get(crop_lower, CROP_SPECS["rice"])
    ref_date = dates[-1]

    is_default_sowing = False
    if sowing_date is None:
        sowing_date = get_default_sowing_date(crop_lower, ref_date)
        is_default_sowing = True

    # Filter observations between sowing_date and ref_date
    accumulated_gdd = 0.0
    gdd_days = 0
    t_base = spec["t_base"]

    for d, tmax, tmin in zip(dates, tmax_arr, tmin_arr):
        if sowing_date <= d <= ref_date:
            if not np.isnan(tmax) and not np.isnan(tmin):
                t_mean = (tmax + tmin) / 2.0
                daily_gdd = max(0.0, t_mean - t_base)
                accumulated_gdd += daily_gdd
                gdd_days += 1

    accumulated_gdd = round(accumulated_gdd, 1)

    # Determine current stage
    current_stage_name = "Mature / Harvesting"
    is_heat_sensitive = False
    for stage in spec["stages"]:
        if stage["gdd_min"] <= accumulated_gdd < stage["gdd_max"]:
            current_stage_name = stage["name"]
            is_heat_sensitive = stage["heat_sensitive"]
            break

    # Check if canopy is developed enough for NDVI vegetation stress assessment
    min_cgdd = spec.get("min_canopy_gdd", 350.0)
    max_cgdd = spec.get("max_canopy_gdd", 1500.0)
    if accumulated_gdd < min_cgdd:
        canopy_status = "not applicable at this stage (early vegetative / emergence)"
        is_canopy_active = False
    elif accumulated_gdd > max_cgdd:
        canopy_status = "not applicable at this stage (crop maturity / senescence)"
        is_canopy_active = False
    else:
        canopy_status = "active canopy"
        is_canopy_active = True

    active_threshold = spec["critical_heat_threshold_c"] if is_heat_sensitive else spec["vegetative_heat_threshold_c"]

    return {
        "crop": crop_lower,
        "sowing_date": sowing_date.isoformat(),
        "is_default_sowing_date": is_default_sowing,
        "days_since_sowing": gdd_days,
        "base_temperature_c": t_base,
        "accumulated_gdd": accumulated_gdd,
        "current_phenological_stage": current_stage_name,
        "in_heat_sensitive_window": is_heat_sensitive,
        "critical_heat_threshold_c": spec["critical_heat_threshold_c"],
        "vegetative_heat_threshold_c": spec["vegetative_heat_threshold_c"],
        "active_heat_threshold_c": active_threshold,
        "canopy_active": is_canopy_active,
        "canopy_status_note": canopy_status
    }

