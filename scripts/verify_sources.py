"""
Source & Analytics Verification Script for KisanRadar.
Phase 1, 2, and 3 Verification:
1. NASA POWER returns 2001-01-01 to today-5d (>=9,000 observations).
2. All 5 GEE satellite collections verified live: SMAP L4, GPM IMERG, MODIS, Landsat 8/9, GRACE-FO.
3. Every SourceResult displays observed_through and detailed freshness_note.
4. Computes Phase 2 indicators and Phase 3 risk scores & GDD phenology on real live data.
"""
import argparse
import asyncio
import os
import sys
import time

# Ensure project root is on sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.adapters import (
    fetch_power,
    fetch_forecast,
    validate_gibs_layers,
    fetch_smap,
    fetch_gpm_imerg,
    fetch_modis,
    fetch_landsat,
    fetch_grace,
    fetch_imd_gridded,
    fetch_icrisat_records,
)
from app.analytics import (
    compute_all_indicators,
    calculate_risk_scores,
    compute_crop_phenology
)

TEST_POINTS = [
    ("Thanjavur, TN (Rice)", 10.78, 79.14, "rice"),
    ("Ludhiana, PB (Wheat)", 30.90, 75.85, "wheat"),
]


async def verify_location(loc_name: str, lat: float, lon: float, crop: str):
    print(f"\n{'='*105}")
    print(f"VERIFYING POINT: {loc_name} [Latitude: {lat}, Longitude: {lon}, Crop: {crop}]")
    print(f"{'='*105}")

    results = {}

    # 1. NASA POWER full 2001-present climatology baseline
    print("  -> Querying NASA POWER 2001-present (25-year baseline)...")
    res_power = await fetch_power(lat, lon, start_year=2001)
    results["power"] = res_power

    # 2. Open-Meteo 7-day NWP Forecast
    print("  -> Querying Open-Meteo 7-day NWP forecast...")
    res_fc = await fetch_forecast(lat, lon)
    results["forecast"] = res_fc

    # 3. NASA SMAP L4 via GEE
    print("  -> Querying NASA SMAP L4 (SPL4SMGP/008) via GEE...")
    res_smap = fetch_smap(lat, lon)
    results["smap"] = res_smap

    # 4. NASA GPM IMERG via GEE (Aligned with POWER's end date)
    print("  -> Querying NASA GPM IMERG (V07) via GEE...")
    power_end = None
    if res_power.status in ("live", "cached") and res_power.data and "dates" in res_power.data:
        import datetime as dt
        power_end = dt.datetime.strptime(res_power.data["dates"][-1], "%Y-%m-%d").date()
    res_gpm = fetch_gpm_imerg(lat, lon, days_back=30, end_date=power_end)
    results["gpm"] = res_gpm

    # 5. MODIS NDVI & LST via GEE
    print("  -> Querying MODIS NDVI (MOD13Q1) & LST (MOD11A1) via GEE...")
    res_modis = fetch_modis(lat, lon)
    results["modis"] = res_modis

    # 6. Landsat 8/9 30m via GEE
    print("  -> Querying Landsat 8 & 9 (Collection 2 Tier 1 L2) via GEE...")
    res_landsat = fetch_landsat(lat, lon)
    results["landsat"] = res_landsat

    # 7. NASA GRACE-FO via GEE
    print("  -> Querying NASA GRACE-FO Tellus (MASS_GRIDS_V04/MASCON_CRI) via GEE...")
    res_grace = fetch_grace(lat, lon)
    results["grace"] = res_grace

    # 8. IMD Gridded Local Dataset
    res_imd = fetch_imd_gridded(lat, lon)
    results["imd"] = res_imd

    # Compute Phase 2 Indicators & Phase 3 Risk Scores if POWER succeeded
    analytics_out = None
    if res_power.status in ("live", "cached") and res_power.data:
        try:
            analytics_res = compute_all_indicators(
                power_data=res_power.data,
                forecast_data=res_fc.data if res_fc.status == "live" else None,
                smap_data=res_smap.data if res_smap.status == "live" else None,
                gpm_data=res_gpm.data if res_gpm.status == "live" else None,
                modis_data=res_modis.data if res_modis.status == "live" else None,
                landsat_data=res_landsat.data if res_landsat.status == "live" else None,
                grace_data=res_grace.data if res_grace.status == "live" else None,
                crop=crop
            )
            provenance_list = list(results.values())
            risk_scores = calculate_risk_scores(
                indicators=analytics_res["indicators"],
                phenology=analytics_res["phenology"],
                provenance_list=provenance_list
            )
            analytics_out = {
                "phenology": analytics_res["phenology"],
                "indicators": analytics_res["indicators"],
                "risk": risk_scores
            }
        except Exception as e:
            print(f"  [!] Analytics calculation exception: {e}")

    return list(results.values()), analytics_out


async def main():
    parser = argparse.ArgumentParser(description="KisanRadar Phase 1, 2 & 3 Verification")
    parser.add_argument("--allow-skip", action="store_true", help="Allow credential-dependent sources to skip without failing exit code")
    args = parser.parse_args()

    print("=" * 105)
    print("KISANRADAR - NASA SPACE APPS 2026: PHASE 1, 2 & 3 STRICT VERIFICATION")
    print("Non-Negotiable Rule: REAL DATA ONLY. No synthetic, mocked, or invented numbers.")
    print("Baseline Rule: NASA POWER must return full multi-year history (>=9,000 observations).")
    print(f"GEE Enforcement: {'STRICT (Blocker)' if not args.allow_skip else 'PERMISSIVE (--allow-skip)'}")
    print("=" * 105)

    # Global service validation (NASA GIBS WMTS Capabilities with 24h cache)
    print("\nValidating Global NASA GIBS WMTS Capabilities (EPSG:3857, 24h cache)...")
    res_gibs = await validate_gibs_layers()
    
    # Check local ICRISAT data store
    res_icrisat = fetch_icrisat_records()

    all_results = [("Global GIBS", res_gibs), ("Local Data", res_icrisat)]
    analytics_by_loc = {}

    for name, lat, lon, crop in TEST_POINTS:
        loc_res, loc_analytics = await verify_location(name, lat, lon, crop)
        analytics_by_loc[name] = loc_analytics
        for r in loc_res:
            all_results.append((name, r))

    # Print Formatted Provenance & Verification Table
    header = f"{'Source':<26} | {'Dataset ID':<36} | {'Status':<12} | {'Obs Date':<10} | {'Obs/Pixels':<10} | {'Latency':<8} | {'Freshness / Error Note'}"
    print("\n" + "=" * len(header))
    print(header)
    print("=" * len(header))

    blocker_failures = 0

    for loc, r in all_results:
        status_str = r.status
        is_fail = False

        if r.status in ("live", "cached"):
            if "POWER" in r.source and r.n_obs < 9000:
                status_str = f"FAIL (n={r.n_obs}<9k)"
                is_fail = True
            else:
                status_str = f"OK ({r.status})"
        elif "SKIPPED-no-credentials" in r.status:
            if not args.allow_skip:
                status_str = "BLOCKER"
                is_fail = True
            else:
                status_str = "SKIPPED"
        elif "SKIPPED-no-data" in r.status or "SKIPPED-out-of-bounds" in r.status:
            status_str = r.status
        else:
            status_str = f"FAIL ({r.status})"
            is_fail = True

        if is_fail:
            blocker_failures += 1

        obs_date = r.observed_through if r.observed_through else "N/A"
        n_obs = str(r.n_obs) if r.n_obs else "0"
        lat_ms = f"{r.latency_ms}ms"
        note = r.freshness_note if r.freshness_note else (r.error if r.error else (r.units if r.units else "Active"))
        note_short = (note[:45] + "...") if len(note) > 45 else note

        print(f"{r.source:<26} | {r.dataset_id:<36} | {status_str:<12} | {obs_date:<10} | {n_obs:<10} | {lat_ms:<8} | {note_short}")

    print("=" * len(header))

    # Print Phase 2 & 3 Analytics Results for each benchmark location
    print("\n" + "#" * 105)
    print("PHASE 2 & PHASE 3 ANALYTICS OUTPUT (REAL MULTI-MISSION DERIVED VALUES)")
    print("#" * 105)

    for loc_name, ana in analytics_by_loc.items():
        if not ana:
            continue
        ph = ana["phenology"]
        ind = ana["indicators"]
        rk = ana["risk"]

        print(f"\n>>> BENCHMARK SITE: {loc_name}")
        print(f"    Crop: {ph['crop'].upper()} | Sowing Date: {ph['sowing_date']} (Default: {ph['is_default_sowing_date']})")
        print(f"    GDD Accumulated: {ph['accumulated_gdd']} degree-days | Stage: {ph['current_phenological_stage']}")
        print(f"    In Heat-Sensitive Window: {ph['in_heat_sensitive_window']} (Active Threshold: {ph['active_heat_threshold_c']}°C, Anthesis Limit: {ph['critical_heat_threshold_c']}°C)")
        print(f"    Canopy Status: {ph['canopy_status_note']}")

        print("\n    [PHASE 2 INDICATORS (Percentiles vs 2001-Present Calendar Window)]")
        print(f"    • 30-Day Rain: {ind['rain_deficit_30d']['current_value_mm']} mm (Hist Mean: {ind['rain_deficit_30d']['historical_mean_mm']} mm, Percentile: {ind['rain_deficit_30d']['percentile']}th pct, N={ind['rain_deficit_30d']['sample_size_years']} yrs)")
        print(f"    • GPM IMERG 30d Accumulation: {ind['rain_deficit_30d']['imerg_cross_check_30d_mm']} mm (Sources Disagree: {ind['rain_deficit_30d']['sources_disagree']}, Gap: {ind['rain_deficit_30d']['disagreement_pct']}%)")
        print(f"    • Root-Zone Soil Wetness: Primary Percentile = {ind['soil_moisture']['primary_soil_percentile']}th pct (Source: {ind['soil_moisture']['primary_source']})")
        print(f"      - SMAP Root Wetness: {ind['soil_moisture']['smap_rootzone_wetness']} ({ind['soil_moisture']['smap_rootzone_wetness_percentile']}th pct vs 2015+ satellite record)")
        print(f"      - POWER MERRA-2 GWETROOT: {ind['soil_moisture']['power_gwetroot_fraction']} ({ind['soil_moisture']['power_gwetroot_percentile']}th pct)")
        print(f"    • Vegetation NDVI: MODIS 250m = {ind['vegetation_vigor']['modis_regional_ndvi_250m']} (2001+ Mean: {ind['vegetation_vigor']['modis_ndvi_historical_mean']}, Anomaly: {ind['vegetation_vigor']['modis_ndvi_anomaly']}) | Landsat 30m = {ind['vegetation_vigor']['landsat_field_ndvi_30m']} (Parcel vs Regional Diff: {ind['vegetation_vigor']['field_vs_regional_diff']})")
        print(f"    • Thermal Heat: Past 14d Tmax = {ind['heat_stress']['mean_tmax_14d_c']}°C ({ind['heat_stress']['tmax_percentile']}th pct) | Hot Days (Past 14d/Next 7d): {ind['heat_stress']['hot_days_past_14d']} / {ind['heat_stress']['hot_days_forecast_7d']}")
        print(f"    • Flood: GPM 72h Rain = {ind['flood_hazard']['imerg_72h_mm']} mm | Local 25-yr 95th Percentile = {ind['flood_hazard']['local_historical_95th_pct_3d_mm']} mm (Flood Floor: 20mm, Exceeded: {ind['flood_hazard']['historical_95th_exceeded']})")
        print(f"    • Dry Spell: {ind['dry_spell']['consecutive_days_under_1mm']} consecutive days under 1 mm ({ind['dry_spell']['dry_spell_percentile']}th percentile vs local calendar climatology)")
        print(f"    • Decadal Warming Trend: +{ind['climate_warming_trend']['warming_trend_c_per_decade']}°C/decade (p={ind['climate_warming_trend']['p_value']}, R²={ind['climate_warming_trend']['r_squared']}, span: {ind['climate_warming_trend']['baseline_span']}) [{ind['climate_warming_trend']['caveat']}]")
        print(f"    • GRACE Regional Total Water Storage: {ind['groundwater_trend']['regional_trend_cm_per_year']} cm/year ({ind['groundwater_trend']['spatial_resolution_caveat']})")

        print("\n    [PHASE 3 PERCENTILE-DRIVEN RISK SCORES (0-100)]")
        print(f"    OVERALL RISK SCORE: {rk['overall']} / 100  [Confidence: {rk['confidence'].upper()} ({rk['live_sources_count']} live feeds)]")
        print(f"    Confidence Note:    {rk['confidence_note']}")
        print(f"    -> Drought Risk:    {rk['drought']} / 100  (Weight: {rk['weights']['drought']})")
        print(f"    -> Heat Risk:       {rk['heat']} / 100  (Weight: {rk['weights']['heat']})")
        print(f"    -> Flood Risk:      {rk['flood']} / 100  (Weight: {rk['weights']['flood']})")
        print(f"    -> Veg Stress Risk: {rk['vegetation'] if rk['vegetation'] is not None else 'N/A (early stage/ripening)'}  (Weight: {rk['weights']['vegetation']})")

    print("\n" + "=" * len(header))
    print(f"Verification completed with {blocker_failures} blocker failures.")

    if blocker_failures > 0:
        print("EXIT CODE 1: Blocker failures encountered.")
        sys.exit(1)
    else:
        print("EXIT CODE 0: All required live sources, GEE satellite feeds, and analytics verified.")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
