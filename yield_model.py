"""
Literature-derived damage functions (ICAR-NICRA, IPCC AR6, IRRI trials).
Estimates potential yield impact and Stress-Tolerant Variety (STRV) buffer benefits
under documented climate shocks across South Asian agro-ecosystems:
- Terminal heatwave response (Rice >34°C, Wheat >31°C, Maize >35°C in reproductive window)
- Dry-spell and root-zone moisture deficit penalties
- Submergence / flash-flood impact curves
- Stress-Tolerant Variety (STRV) buffer advantages (Swarna-Sub1, Sahbhagi Dhan, HD 3385, BRRI Dhan 47/67)
NOTE: Literature-derived estimation models, not machine learning trained on proprietary farm datasets.
"""
from typing import Optional, Dict, Any

CROP_BASELINES = {
    "rice": {
        "normal_yield_t_ha": 3.8,
        "heat_threshold_c": 34.0,
        "heat_loss_pct_per_deg": 10.0,
        "heat_loss_cap_pct": 40.0,
        "drought_resilient_variety": "Sahbhagi Dhan / BRRI Dhan 56",
        "drought_buffer_t_ha": 0.9,      # +0.8 to 1.0 t/ha advantage under drought
        "submergence_resilient_variety": "Swarna-Sub1",
        "submergence_buffer_t_ha": 1.8,  # +1.0 to 3.0 t/ha advantage under flash floods
        "saline_resilient_variety": "BRRI Dhan 47 / CSR 36",
        "documented_range_pct": "15-45% (IRRI/ICAR flood+drought trials)",
    },
    "wheat": {
        "normal_yield_t_ha": 3.4,
        "heat_threshold_c": 31.0,
        "heat_loss_pct_per_deg": 5.0,    # Pre-anthesis pollen sterility & grain shriveling (2022 heatwave benchmark)
        "heat_loss_cap_pct": 25.0,       # Documented Punjab 2022 state avg ~10-15%, hot-spots up to 25-35%
        "drought_resilient_variety": "HD 3385 (Heat & Drought Tolerant)",
        "drought_buffer_t_ha": 0.6,
        "submergence_resilient_variety": "N/A (Rabi crop)",
        "submergence_buffer_t_ha": 0.0,
        "saline_resilient_variety": "KRL 210",
        "documented_range_pct": "10-35% (CIMMYT/ICAR 2022 benchmark)",
    },
    "maize": {
        "normal_yield_t_ha": 4.2,
        "heat_threshold_c": 35.0,
        "heat_loss_pct_per_deg": 7.0,
        "heat_loss_cap_pct": 35.0,
        "drought_resilient_variety": "DHM 117 / Drought-Tolerant Hybrid",
        "drought_buffer_t_ha": 0.7,
        "submergence_resilient_variety": "N/A",
        "submergence_buffer_t_ha": 0.0,
        "saline_resilient_variety": "N/A",
        "documented_range_pct": "10-30% (ICAR-IARI trials)",
    }
}

def estimate_yield_impact(crop: str, metrics: dict, risk: dict, phenology: Optional[Dict[str, Any]] = None) -> dict:
    """
    Computes expected yield penalty (%) and t/ha under standard conventional farming,
    along with the protected yield buffer achieved by deploying Stress-Tolerant Varieties (STRVs)
    and Climate-Smart Agronomy (Safe AWD / micro-irrigation).
    """
    crop_info = CROP_BASELINES.get(crop.lower(), CROP_BASELINES["rice"])
    base_yield = crop_info["normal_yield_t_ha"]
    
    # Gate: if crop is at maturity/ripening/harvest, yield impact is not applicable
    if phenology:
        stage = phenology.get("current_phenological_stage", "")
        stage_lower = stage.lower()
        if any(kw in stage_lower for kw in ["ripening", "maturity", "mature", "harvesting", "harvest"]):
            return {
                "yield_applicable": False,
                "note": f"Yield impact estimation not applicable at current crop stage ({stage}).",
                "estimation_type": "Literature-Based Scenario Estimate",
                "documented_range_pct": crop_info["documented_range_pct"],
                "baseline_yield_t_ha": base_yield,
                "predicted_yield_conventional_t_ha": base_yield,
                "predicted_yield_with_strv_t_ha": base_yield,
                "yield_loss_unmitigated_pct": 0.0,
                "yield_protected_by_adaptation_t_ha": 0.0,
                "loss_drivers": {
                    "terminal_heat_pct": 0.0,
                    "drought_moisture_pct": 0.0,
                    "flood_excess_pct": 0.0
                },
                "recommended_interventions": []
            }
    
    # 1. Heat Shock Penalty (Gated strictly by reproductive/flowering phenological window)
    in_sensitive = metrics.get("in_heat_sensitive_window", False)
    if in_sensitive:
        tmax_14d = metrics.get("tmax_14d_c", 30.0)
        thr = crop_info["heat_threshold_c"]
        heat_excess = max(0.0, tmax_14d - thr)
        hot_days = metrics.get("hot_days_14d", 0) + metrics.get("hot_days_forecast", 0)
        raw_heat_loss = heat_excess * crop_info["heat_loss_pct_per_deg"] * (1.0 + 0.1 * min(hot_days, 10))
        heat_loss_pct = min(crop_info["heat_loss_cap_pct"], raw_heat_loss)
    else:
        heat_loss_pct = 0.0  # At sowing or vegetative stage, reproductive heat penalty does not apply
    
    # 2. Drought / Moisture Stress Penalty
    drought_score = risk.get("drought", 20)
    drought_loss_pct = 0.0
    if drought_score >= 55:
        severity = (drought_score / 100.0)
        drought_loss_pct = min(50.0, (severity - 0.50) * 80.0)
        
    # 3. Flood / Excessive Rainfall Penalty
    flood_score = risk.get("flood", 10)
    flood_loss_pct = 0.0
    if flood_score >= 40:
        flood_loss_pct = min(60.0, (flood_score / 100.0) * 55.0)
        
    # Combined non-linear compound loss (compound hydro-thermal stress)
    # Yield penalty = 1 - (1 - heat_loss)*(1 - drought_loss)*(1 - flood_loss)
    combined_loss_factor = (1.0 - heat_loss_pct / 100.0) * (1.0 - drought_loss_pct / 100.0) * (1.0 - flood_loss_pct / 100.0)
    total_loss_pct = round((1.0 - combined_loss_factor) * 100.0, 1)
    
    expected_yield_conventional = round(base_yield * (1.0 - total_loss_pct / 100.0), 2)
    
    # STRV Intervention Benefit Calculation
    buffered_yield = expected_yield_conventional
    recommended_interventions = []
    
    if drought_score >= 45 and crop_info["drought_buffer_t_ha"] > 0:
        benefit = min(crop_info["drought_buffer_t_ha"], base_yield - expected_yield_conventional)
        buffered_yield += benefit
        recommended_interventions.append({
            "type": "Drought Adaptation",
            "variety": crop_info["drought_resilient_variety"],
            "protection": f"+{crop_info['drought_buffer_t_ha']} t/ha yield resilience under water stress",
            "agronomy": "Safe AWD (re-flood at -15cm depth) + mulching to conserve root-zone moisture"
        })
        
    if flood_score >= 40 and crop_info["submergence_buffer_t_ha"] > 0:
        benefit = min(crop_info["submergence_buffer_t_ha"], base_yield - expected_yield_conventional)
        buffered_yield += benefit
        recommended_interventions.append({
            "type": "Flash Flood Adaptation",
            "variety": crop_info["submergence_resilient_variety"],
            "protection": f"+{crop_info['submergence_buffer_t_ha']} t/ha protected through SUB1 submergence tolerance (up to 14 days)",
            "agronomy": "Pre-clear drainage channels, postpone fertilizer top-dressing until waters recede"
        })
        
    if heat_loss_pct >= 15:
        recommended_interventions.append({
            "type": "Terminal Heat Defense",
            "variety": "HD 3385 (Wheat) / Heat-tolerant lines",
            "protection": "Buffers pollen viability against >31-34°C terminal heat",
            "agronomy": "Evening irrigation to lower microclimate canopy temperature by 1.5-2.0°C; shift spraying away from peak noon hours"
        })
        
    buffered_yield = min(base_yield, round(buffered_yield, 2))
    yield_saved_t_ha = round(max(0.0, buffered_yield - expected_yield_conventional), 2)
    
    return {
        "yield_applicable": True,
        "estimation_type": "Literature-Based Scenario Estimate",
        "documented_range_pct": crop_info["documented_range_pct"],
        "baseline_yield_t_ha": base_yield,
        "predicted_yield_conventional_t_ha": expected_yield_conventional,
        "predicted_yield_with_strv_t_ha": buffered_yield,
        "yield_loss_unmitigated_pct": total_loss_pct,
        "yield_protected_by_adaptation_t_ha": yield_saved_t_ha,
        "loss_drivers": {
            "terminal_heat_pct": round(heat_loss_pct, 1),
            "drought_moisture_pct": round(drought_loss_pct, 1),
            "flood_excess_pct": round(flood_loss_pct, 1)
        },
        "recommended_interventions": recommended_interventions
    }
