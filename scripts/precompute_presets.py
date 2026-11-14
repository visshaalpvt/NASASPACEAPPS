"""
Precomputes real live analyses for all 5 preset benchmark hotspots and 3 historical replays.
Stores full real responses in data/cache/precomputed_*.json.
Strictly authentic NASA telemetry, zero synthetic data.
"""
import sys
import os
import asyncio
import json
import datetime as dt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import analyze_point, historical_replay

PRESETS = [
    {"name": "thanjavur", "lat": 10.78, "lon": 79.14, "crop": "rice", "sowing": "2026-07-01"},
    {"name": "ludhiana", "lat": 30.90, "lon": 75.85, "crop": "wheat", "sowing": "2026-11-10"},
    {"name": "dhaka", "lat": 22.50, "lon": 89.50, "crop": "rice", "sowing": "2026-07-01"},
    {"name": "sindh", "lat": 26.00, "lon": 68.50, "crop": "wheat", "sowing": "2026-11-10"},
    {"name": "guwahati", "lat": 26.10, "lon": 91.70, "crop": "rice", "sowing": "2026-06-15"},
]

REPLAYS = [
    "punjab-march-2022-heatwave",
    "pakistan-sindh-aug-2022-flood",
    "tamilnadu-dec-2023-cyclone"
]

async def precompute_all():
    cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "cache"))
    os.makedirs(cache_dir, exist_ok=True)

    print("=== Precomputing Real Analyses for 5 Preset Hotspots ===")
    for p in PRESETS:
        print(f"Precomputing {p['name']} ({p['lat']}, {p['lon']})...")
        t0 = dt.datetime.utcnow()
        res = await analyze_point(lat=p["lat"], lon=p["lon"], crop=p["crop"], sowing_date=p["sowing"], lang="en")
        res["precomputed_at"] = t0.isoformat() + "Z"
        res["is_precomputed"] = True

        out_path = os.path.join(cache_dir, f"preset_{p['name']}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2)
        print(f"  -> Saved {out_path} (Risk: {res['risk_scores']['overall']}/100)")

    print("\n=== Precomputing 3 Historical Replays ===")
    for r_id in REPLAYS:
        print(f"Precomputing replay {r_id}...")
        t0 = dt.datetime.utcnow()
        res_r = await historical_replay(r_id, lang="en")
        res_r["precomputed_at"] = t0.isoformat() + "Z"
        res_r["is_precomputed"] = True

        out_path = os.path.join(cache_dir, f"replay_{r_id}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(res_r, f, indent=2)
        print(f"  -> Saved {out_path} (Yield Loss: {res_r['yield_impact']['yield_loss_unmitigated_pct']}%)")

    print("\nAll 5 presets and 3 replays precomputed successfully!")

if __name__ == "__main__":
    asyncio.run(precompute_all())
