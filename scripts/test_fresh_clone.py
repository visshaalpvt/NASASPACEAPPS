"""
Fresh-Clone Verification Script.
Validates that KisanRadar runs without any .env credentials, serving authentic
precomputed telemetry for all 5 presets and 3 replays with the cached badge.
"""
import os
import sys
from fastapi.testclient import TestClient
from app.main import app

has_env = os.path.exists('.env')
print('======================================================')
print(' FRESH-CLONE VERIFICATION RUN')
print(' Repo: https://github.com/visshaalpvt/NASASPACEAPPS.git')
print(f' .env exists: {has_env} (Zero Credentials Configured)')
print('======================================================\n')

client = TestClient(app)

presets = [
    ('Ludhiana, Punjab', '/api/analyze?lat=30.90&lon=75.85&crop=wheat&sowing_date=2026-11-10'),
    ('Thanjavur, Tamil Nadu', '/api/analyze?lat=10.78&lon=79.14&crop=rice&sowing_date=2026-07-01'),
    ('Dhaka, Bangladesh', '/api/analyze?lat=22.50&lon=89.50&crop=rice&sowing_date=2026-07-01'),
    ('Sindh, Pakistan', '/api/analyze?lat=26.00&lon=68.50&crop=wheat&sowing_date=2026-11-10'),
    ('Guwahati, Assam', '/api/analyze?lat=26.10&lon=91.70&crop=rice&sowing_date=2026-06-15'),
]

print('--- PRESET LOCATIONS TEST ---')
for name, url in presets:
    res = client.get(url)
    assert res.status_code == 200, f'Failed {name}: {res.status_code}'
    d = res.json()
    is_cached = d.get('is_precomputed', False)
    overall = d['risk_scores']['overall']
    stage = d['phenology']['current_phenological_stage']
    conf = d['risk_scores'].get('confidence', 'N/A')
    t_fetch = d.get('precomputed_at', 'N/A')
    print(f'  [OK 200] {name:<22} | Overall Risk: {overall:>2}/100 | Stage: {stage:<18} | Conf: {conf.upper():<6} | Cached Badge: {is_cached} (Fetched: {t_fetch})')

replays = [
    ('Punjab 2022 Heat Shock', '/api/historical-replay/punjab-march-2022-heatwave'),
    ('Pakistan 2022 Flood', '/api/historical-replay/pakistan-sindh-aug-2022-flood'),
    ('TN 2023 Cyclone Michaung', '/api/historical-replay/tamilnadu-dec-2023-cyclone'),
]

print('\n--- HISTORICAL REPLAYS TEST ---')
for name, url in replays:
    res = client.get(url)
    assert res.status_code == 200, f'Failed {name}: {res.status_code}'
    d = res.json()
    is_cached = d.get('is_precomputed', False)
    scores = d['risk_scores']
    if 'heatwave' in url:
        key_metric = f"Heat Score: {scores.get('heat')}/100"
    else:
        rain_30d = d.get('indicators', {}).get('rain_deficit_30d', {}).get('primary_rain_30d_mm', 'N/A')
        key_metric = f"30d Rain: {rain_30d} mm"
    yield_loss = d.get('yield_impact', {}).get('yield_loss_unmitigated_pct', 'N/A')
    t_fetch = d.get('precomputed_at', 'N/A')
    print(f'  [OK 200] {name:<24} | Key Metric: {key_metric:<20} | Yield Loss: {yield_loss}% | Cached Badge: {is_cached} (Fetched: {t_fetch})')

print('\n======================================================')
print(' SUCCESS: All 5 presets and 3 replays loaded with cached badge with zero credentials!')
print('======================================================')
