"""
Unit Tests for KisanRadar Analytics Engine (Phases 2 & 3).
Tests:
- Empirical percentile calculation & edge cases
- Multi-year calendar window history extraction
- Crop GDD accumulation & phenology transitions
- Heat threshold sensitivity gating
- Percentile-based risk scoring (drought, heat, flood, vegetation, overall)
- SourceResult schema and provenance contract
"""
import pytest
from datetime import date, timedelta
import numpy as np

from app.adapters.base import SourceResult
from app.analytics.baseline import (
    compute_percentile,
    extract_calendar_window_history,
    compute_decadal_warming_trend
)
from app.analytics.crop_stage import compute_crop_phenology, get_default_sowing_date
from app.analytics.risk import calculate_risk_scores, RISK_WEIGHTS


def test_percentile_calculation():
    history = [10.0, 20.0, 30.0, 40.0, 50.0]
    # Median
    assert compute_percentile(history, 30.0) == 50.0
    # Minimum (1/10 rank = 10%)
    assert compute_percentile(history, 10.0) == 10.0
    # Maximum (4.5/5 rank = 90%)
    assert compute_percentile(history, 50.0) == 90.0
    # Below min
    assert compute_percentile(history, 5.0) == 0.0
    # Above max
    assert compute_percentile(history, 60.0) == 100.0


def test_calendar_window_extraction():
    # Build 4 years of daily series (2020 to 2023)
    start = date(2020, 1, 1)
    dates = [start + timedelta(days=i) for i in range(1461)]
    # Constant 10.0 on all days
    values = np.full(len(dates), 10.0)

    end_date = date(2023, 7, 15)
    samples, n_years = extract_calendar_window_history(dates, values, end_date, window_days=10, agg_fn=np.sum)

    # Years 2020, 2021, 2022 -> exactly 3 complete historical years
    assert n_years == 3
    for s in samples:
        assert s == 100.0  # 10 days * 10.0


def test_decadal_warming_trend():
    # Construct 10 years of known warming (+0.3 C / decade)
    dates = []
    temps = []
    for y in range(2001, 2021):
        for d in range(1, 360):
            dates.append(date(y, 1, 1) + timedelta(days=d-1))
            temps.append(25.0 + (y - 2001) * 0.03)

    trend_info = compute_decadal_warming_trend(dates, np.array(temps))
    assert trend_info["warming_trend_c_per_decade"] == pytest.approx(0.30, abs=0.05)
    assert trend_info["p_value"] < 0.001
    assert trend_info["r_squared"] > 0.95


def test_crop_gdd_and_phenology():
    # 60 days of Rice: Tmax = 32, Tmin = 24 -> Mean = 28 -> Daily GDD = 28 - 10 = 18 GDD/day
    dates = [date(2024, 7, 1) + timedelta(days=i) for i in range(60)]
    tmax = np.full(60, 32.0)
    tmin = np.full(60, 24.0)

    # 1. Vegetative stage at day 20 (GDD = 360 < 850)
    res_veg = compute_crop_phenology("rice", date(2024, 7, 1), dates[:20], tmax[:20], tmin[:20])
    assert res_veg["accumulated_gdd"] == 360.0
    assert "Vegetative" in res_veg["current_phenological_stage"]
    assert res_veg["in_heat_sensitive_window"] is False

    # 2. Reproductive stage at day 60 (GDD = 1080 > 850)
    res_rep = compute_crop_phenology("rice", date(2024, 7, 1), dates, tmax, tmin)
    assert res_rep["accumulated_gdd"] == 1080.0
    assert "Reproductive" in res_rep["current_phenological_stage"]
    assert res_rep["in_heat_sensitive_window"] is True


def test_wheat_heat_threshold_and_stage():
    # Wheat with base temp 5 C
    dates = [date(2023, 11, 15) + timedelta(days=i) for i in range(100)]
    tmax = np.full(100, 22.0)
    tmin = np.full(100, 10.0)

    res = compute_crop_phenology("wheat", date(2023, 11, 15), dates, tmax, tmin)
    assert res["base_temperature_c"] == 5.0
    assert res["critical_heat_threshold_c"] == 31.0


def test_risk_scoring_bounds_and_weights():
    # Verify weights sum to 1.0
    total_weight = sum(RISK_WEIGHTS.values())
    assert total_weight == pytest.approx(1.0, abs=1e-5)

    mock_indicators = {
        "rain_deficit_30d": {"percentile": 20.0},
        "soil_moisture": {"power_gwetroot_percentile": 15.0},
        "dry_spell": {"consecutive_days_under_1mm": 12},
        "heat_stress": {
            "tmax_percentile": 85.0,
            "hot_days_past_14d": 5,
            "hot_days_forecast_7d": 4
        },
        "flood_hazard": {
            "imerg_72h_mm": 20.0,
            "forecast_max_3d_rain_mm": 10.0,
            "local_historical_95th_pct_3d_mm": 120.0
        },
        "vegetation_vigor": {
            "landsat_field_ndvi_30m": 0.35,
            "modis_regional_ndvi_250m": 0.40
        }
    }
    mock_phenology = {"in_heat_sensitive_window": True}
    mock_provenance = [SourceResult(source="test", dataset_id="test", status="live")] * 5

    scores = calculate_risk_scores(mock_indicators, mock_phenology, mock_provenance)

    for k in ["overall", "drought", "heat", "flood", "vegetation"]:
        assert 0 <= scores[k] <= 100

    assert scores["confidence"] == "high"


def test_source_result_provenance_contract():
    sr = SourceResult(
        source="NASA Landsat 8 & 9 (30m)",
        dataset_id="LANDSAT/LC08/C02/T1_L2",
        status="live",
        observed_through="2026-11-14",
        freshness_note="Acquired 2026-11-14 (16-day revisit)",
        latency_ms=120,
        n_obs=400,
        units="NDVI index"
    )
    assert sr.observed_through == "2026-11-14"
    assert "Acquired" in sr.freshness_note
    assert sr.status == "live"


def test_wheat_at_sowing_stage_gating():
    # Wheat sown 4 days ago: GDD = 4 * (22-5) = 68 GDD (<350 min canopy)
    dates = [date(2024, 11, 10) + timedelta(days=i) for i in range(4)]
    tmax = np.full(4, 26.0)
    tmin = np.full(4, 14.0)

    res = compute_crop_phenology("wheat", date(2024, 11, 10), dates, tmax, tmin)
    assert res["in_heat_sensitive_window"] is False
    assert res["canopy_active"] is False
    assert "early vegetative" in res["canopy_status_note"]

    # Verify risk scoring gates heat and vegetation false alarms
    mock_ind = {
        "rain_deficit_30d": {"percentile": 50.0},
        "soil_moisture": {"primary_soil_percentile": 50.0},
        "dry_spell": {"consecutive_days_under_1mm": 20, "dry_spell_percentile": 45.0},
        "heat_stress": {"tmax_percentile": 60.0, "hot_days_past_14d": 0, "hot_days_forecast_7d": 0},
        "flood_hazard": {"imerg_72h_mm": 5.0, "forecast_max_3d_rain_mm": 2.0, "local_historical_95th_pct_3d_mm": 10.0},
        "vegetation_vigor": {"landsat_field_ndvi_30m": 0.25, "modis_regional_ndvi_250m": 0.30}
    }
    mock_prov = [SourceResult(source="test", dataset_id="test", status="live")] * 5
    scores = calculate_risk_scores(mock_ind, res, mock_prov)

    # Heat score must be low (< 25) because crop is at emergence, not anthesis
    assert scores["heat"] <= 25
    # Vegetation stress is not applicable (bare soil / emergence)
    assert scores["vegetation_applicable"] is False
    assert scores["vegetation"] is None
    # Flood score must be 0 due to 20mm absolute floor
    assert scores["flood"] == 0


def test_flood_absolute_rainfall_floor():
    # Even if local 95th percentile is tiny (e.g. 5 mm in arid dry season), 8 mm rain must NOT trigger flood alarm
    mock_ind = {
        "rain_deficit_30d": {"percentile": 50.0},
        "soil_moisture": {"primary_soil_percentile": 50.0},
        "dry_spell": {"consecutive_days_under_1mm": 5, "dry_spell_percentile": 30.0},
        "heat_stress": {"tmax_percentile": 50.0, "hot_days_past_14d": 0, "hot_days_forecast_7d": 0},
        "flood_hazard": {"imerg_72h_mm": 8.0, "forecast_max_3d_rain_mm": 4.0, "local_historical_95th_pct_3d_mm": 5.0},
        "vegetation_vigor": {"modis_ndvi_anomaly": 0.05}
    }
    phenology = {"in_heat_sensitive_window": False, "canopy_active": True}
    prov = [SourceResult(source="test", dataset_id="test", status="live")] * 5
    scores = calculate_risk_scores(mock_ind, phenology, prov)
    assert scores["flood"] == 0


def test_sources_disagreement_downgrade():
    mock_ind = {
        "rain_deficit_30d": {"percentile": 50.0, "sources_disagree": True},
        "soil_moisture": {"primary_soil_percentile": 50.0},
        "dry_spell": {"consecutive_days_under_1mm": 5},
        "heat_stress": {"tmax_percentile": 50.0, "hot_days_past_14d": 0, "hot_days_forecast_7d": 0},
        "flood_hazard": {"imerg_72h_mm": 25.0, "local_historical_95th_pct_3d_mm": 50.0},
        "vegetation_vigor": {"modis_ndvi_anomaly": 0.02}
    }
    phenology = {"in_heat_sensitive_window": False, "canopy_active": True}
    prov = [SourceResult(source="test", dataset_id="test", status="live")] * 6

    scores = calculate_risk_scores(mock_ind, phenology, prov)
    assert scores["sources_disagree"] is True
    # 6 live sources would normally be 'high', but disagreement downgrades to 'medium'
    assert scores["confidence"] == "medium"
    assert "disagree" in scores["confidence_note"]


def test_percentile_to_drought_risk_mapping():
    from app.analytics.risk import percentile_to_drought_risk
    # Above median -> zero drought risk
    assert percentile_to_drought_risk(50.0) == 0.0
    assert percentile_to_drought_risk(80.0) == 0.0
    # Bottom 5% -> maximum drought risk
    assert percentile_to_drought_risk(5.0) == 100.0
    assert percentile_to_drought_risk(2.0) == 100.0
    # Midpoint of (5, 50) is 27.5 -> 50.0 risk
    assert percentile_to_drought_risk(27.5) == pytest.approx(50.0, abs=0.1)


def test_advisory_brief_compliance():
    from app.advisory.engine import SOLUTIONS_DB, generate_advisory

    # 1. Safe AWD: exactly 15-20%
    awd_benefit = SOLUTIONS_DB["safe_awd"]["benefit"]
    assert "15-20%" in awd_benefit
    assert "15-30%" not in awd_benefit

    # 2. Drought rice variety: +0.8 to 1.0 t/ha
    drought_benefit = SOLUTIONS_DB["drought_varieties_rice"]["benefit"]
    assert "+0.8 to 1.0 t/ha" in drought_benefit
    assert "1.2" not in drought_benefit

    # 3. No potassium nitrate spray in terminal heat
    for lang_code, t in SOLUTIONS_DB["terminal_heat_wheat"]["translations"].items():
        assert "potassium nitrate" not in t["action"].lower()
        assert "kno3" not in t.get("note", "").lower()
        assert "पोटैशियम" not in t.get("note", "")

    # 4. Translation disclaimer for non-English
    mock_risk = {"overall": 60, "drought": 50, "heat": 40, "flood": 10, "vegetation": 20}
    mock_pheno = {"current_phenological_stage": "Tillering"}
    adv_hi = generate_advisory("rice", mock_risk, mock_pheno, {}, lang="hi")
    assert "translation_disclaimer" in adv_hi
    assert "Machine-translated" in adv_hi["translation_disclaimer"]

    adv_en = generate_advisory("rice", mock_risk, mock_pheno, {}, lang="en")
    assert "translation_disclaimer" not in adv_en


def test_yield_model_maturity_and_wheat_cap():
    from yield_model import estimate_yield_impact

    # 1. At Ripening / Maturity: yield_applicable is False
    pheno_rip = {"current_phenological_stage": "Ripening & Physiological Maturity"}
    res_rip = estimate_yield_impact("rice", {"in_heat_sensitive_window": False}, {"drought": 60, "heat": 80, "flood": 70}, phenology=pheno_rip)
    assert res_rip["yield_applicable"] is False
    assert "not applicable" in res_rip["note"]
    assert res_rip["yield_loss_unmitigated_pct"] == 0.0

    # 2. Wheat heat loss cap: extreme heat 38C during anthesis capped at 25% (documented range)
    pheno_anth = {"current_phenological_stage": "Pre-Anthesis & Flowering"}
    metrics = {
        "in_heat_sensitive_window": True,
        "tmax_14d_c": 38.0,
        "hot_days_14d": 10,
        "hot_days_forecast": 5
    }
    res_wheat = estimate_yield_impact("wheat", metrics, {"drought": 10, "flood": 0}, phenology=pheno_anth)
    assert res_wheat["yield_applicable"] is True
    assert res_wheat["loss_drivers"]["terminal_heat_pct"] <= 25.0
    assert "10-35%" in res_wheat["documented_range_pct"]
    assert res_wheat["estimation_type"] == "Literature-Based Scenario Estimate"


def test_advisory_stage_awareness():
    from app.advisory.engine import generate_advisory

    # Rice at Ripening: should generate harvest_maturity and NOT safe_awd
    pheno = {"current_phenological_stage": "Ripening & Physiological Maturity"}
    risk = {"overall": 30, "drought": 50, "heat": 20, "flood": 10}
    adv = generate_advisory("rice", risk, pheno, {}, lang="en")

    ids = [r["id"] for r in adv["recommendations"]]
    assert "harvest_maturity" in ids
    assert "safe_awd" not in ids


def test_disagreement_threshold_requires_10mm():
    from app.analytics.indicators import compute_all_indicators
    # IMERG = 1.0 mm, POWER = 2.0 mm -> 50% difference but only 1.0 mm absolute gap (should NOT flag)
    power_mock = {
        "dates": ["2026-11-01", "2026-11-02"] * 15,
        "PRECTOTCORR": [0.067] * 30,  # ~2.0 mm total
        "T2M_MAX": [28.0] * 30,
        "T2M_MIN": [18.0] * 30,
        "T2M": [23.0] * 30,
        "GWETROOT": [0.55] * 30
    }
    gpm_mock = {"rain_30d_mm": 1.0, "imerg_30d_percentile": 50.0}
    res = compute_all_indicators(power_mock, None, None, gpm_mock, None, None, None, crop="rice")
    assert res["indicators"]["rain_deficit_30d"]["sources_disagree"] is False



