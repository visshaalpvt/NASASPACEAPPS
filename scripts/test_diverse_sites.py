"""
Runs full live multi-sensor analysis across three diverse test locations:
1. Dhaka Delta, Bangladesh (22.5, 89.5, rice)
2. Sindh, Pakistan (26.0, 68.5, wheat)
3. Guwahati, Assam (26.1, 91.7, rice)
"""
import asyncio
import json
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.main import analyze_point

test_sites = [
    ("Dhaka Delta, Bangladesh", 22.5, 89.5, "rice", "2026-07-01"),
    ("Sindh, Pakistan", 26.0, 68.5, "wheat", "2026-11-10"),
    ("Guwahati, Assam", 26.1, 91.7, "rice", "2026-06-15"),
]


async def run_tests():
    for name, lat, lon, crop, sowing in test_sites:
        t0 = time.time()
        print("=" * 60)
        print(f"Testing Site: {name} ({lat}, {lon}) | Crop: {crop} | Sowing: {sowing}")
        print("=" * 60)
        res = await analyze_point(lat=lat, lon=lon, crop=crop, sowing_date=sowing, lang="en")
        elapsed = round(time.time() - t0, 2)
        print(f"Total Response Time: {elapsed}s")
        print(f"Phenology: stage={res['phenology']['current_phenological_stage']}, accumulated_gdd={res['phenology']['accumulated_gdd']}")
        print(f"Risk Scores:")
        for k in ["overall", "drought", "heat", "flood", "vegetation"]:
            print(f"  - {k}: {res['risk_scores'][k]}")
        print(f"Drought Score Arithmetic:")
        print(f"  {json.dumps(res['risk_scores']['score_arithmetic']['drought'], indent=4)}")
        
        rd = res['indicators']['rain_deficit_30d']
        sm = res['indicators']['soil_moisture']
        vg = res['indicators']['vegetation_vigor']
        ht = res['indicators']['heat_stress']
        
        print(f"Rainfall Indicators:")
        print(f"  - Primary (GPM IMERG 30d): {rd.get('primary_rain_30d_mm')} mm (pct: {rd.get('primary_rain_percentile')})")
        print(f"  - Cross-check (POWER 30d): {rd.get('power_cross_check_30d_mm')} mm (pct: {rd.get('power_cross_check_percentile')})")
        print(f"  - Disagreement Flag: {rd.get('sources_disagree')} ({rd.get('disagreement_pct')}%)")
        print(f"Soil Moisture Indicators:")
        print(f"  - SMAP root-zone wetness: {sm.get('smap_rootzone_wetness')} (pct: {sm.get('smap_rootzone_wetness_percentile')})")
        print(f"  - POWER root-zone fraction: {sm.get('power_gwetroot_fraction')} (pct: {sm.get('power_gwetroot_percentile')})")
        print(f"Vegetation Indicators:")
        print(f"  - MODIS NDVI: {vg.get('modis_regional_ndvi_250m')} (anomaly: {vg.get('modis_ndvi_anomaly')})")
        print(f"  - Canopy active: {vg.get('canopy_active')} ({vg.get('canopy_status_note')})")
        print(f"Heat Indicators:")
        print(f"  - MODIS LST Day: {ht.get('modis_lst_day_c')} °C")
        print(f"  - POWER 14d mean Tmax: {ht.get('mean_tmax_14d_c')} °C (pct: {ht.get('tmax_percentile')})")
        print(f"Yield Impact:")
        print(f"  - Unmitigated Loss: {res['yield_impact']['yield_loss_unmitigated_pct']}%")
        print(f"  - Conventional Yield: {res['yield_impact']['predicted_yield_conventional_t_ha']} t/ha")
        print(f"  - STRV Buffered Yield: {res['yield_impact']['predicted_yield_with_strv_t_ha']} t/ha")
        print(f"Advisory Recommendations:")
        for r in res['advisory']['recommendations']:
            print(f"  - {r['title']}: {r['quantified_benefit']}")
        print(f"Data Sources Provenance:")
        for p in res['provenance']:
            print(f"  - {p['source']} [{p['dataset_id']}]: status={p['status']}, latency={p['latency_ms']}ms, observed_through={p['observed_through']}")
        print()

if __name__ == "__main__":
    asyncio.run(run_tests())
