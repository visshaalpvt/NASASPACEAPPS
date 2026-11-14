"""
Baseline & Multi-Year Anomaly Analytics Module.
Calculates localized historical percentiles and anomalies for the exact calendar window
across all years in the baseline record (2001 to present).
STRICT RULE: REAL DATA ONLY. No synthetic or hardcoded distributions.
"""
from datetime import date, datetime
from typing import List, Callable, Tuple, Dict, Any, Optional
import numpy as np
from scipy import stats


def compute_percentile(history: List[float], current_val: float) -> Optional[float]:
    """
    Computes empirical percentile rank (0.0 to 100.0) of current_val relative to history.
    Uses Weibull plotting position / mid-point rank: (count(x < v) + 0.5*count(x == v)) / N * 100.
    """
    valid = np.array([x for x in history if not np.isnan(x)], dtype=float)
    if len(valid) == 0 or np.isnan(current_val):
        return None
    rank = (np.sum(valid < current_val) + 0.5 * np.sum(valid == current_val)) / float(len(valid))
    return round(float(rank * 100.0), 1)


def extract_calendar_window_history(
    dates: List[date],
    series: np.ndarray,
    end_date: date,
    window_days: int,
    agg_fn: Callable[[np.ndarray], float]
) -> Tuple[List[float], int]:
    """
    Extracts the aggregated stat over the same calendar window (window_days ending on end_date)
    for every past historical year in the series (excludes current ongoing year).
    Returns (historical_samples, sample_count).
    """
    date_to_idx = {d: i for i, d in enumerate(dates)}
    samples = []

    # Iterate over past complete years
    start_year = dates[0].year
    for y in range(start_year, end_date.year):
        # Match calendar day, accounting for leap years
        try:
            target_end = end_date.replace(year=y)
        except ValueError:
            target_end = end_date.replace(year=y, day=28)

        idx = date_to_idx.get(target_end)
        if idx is not None and idx >= window_days - 1:
            window_slice = series[idx - window_days + 1 : idx + 1]
            # Verify slice has sufficient valid data (>70% non-nan)
            valid_slice = window_slice[~np.isnan(window_slice)]
            if len(valid_slice) >= int(window_days * 0.7):
                agg_val = agg_fn(valid_slice)
                if not np.isnan(agg_val):
                    samples.append(float(agg_val))

    return samples, len(samples)


def compute_calendar_day_dry_spells(
    dates: List[date],
    rain_series: np.ndarray,
    end_date: date,
    threshold_mm: float = 1.0
) -> Tuple[List[int], int]:
    """
    Computes consecutive dry spell length (< threshold_mm) ending on the target calendar day
    for every past historical year (2001 to present).
    Used to normalize dry spell anomalies against local climatology.
    """
    date_to_idx = {d: i for i, d in enumerate(dates)}
    past_spells = []
    start_year = dates[0].year
    for y in range(start_year, end_date.year):
        try:
            target_d = end_date.replace(year=y)
        except ValueError:
            target_d = end_date.replace(year=y, day=28)
        idx = date_to_idx.get(target_d)
        if idx is not None:
            spell = 0
            curr = idx
            while curr >= 0 and not np.isnan(rain_series[curr]) and rain_series[curr] < threshold_mm:
                spell += 1
                curr -= 1
            past_spells.append(spell)
    return past_spells, len(past_spells)


def compute_decadal_warming_trend(dates: List[date], t2m_series: np.ndarray) -> Dict[str, Any]:
    """
    Calculates linear trend of annual mean surface temperature since 2001 in °C/decade
    with its statistical two-sided p-value using ordinary least squares.
    """
    yearly_temps: Dict[int, List[float]] = {}
    for d, t in zip(dates, t2m_series):
        if not np.isnan(t):
            yearly_temps.setdefault(d.year, []).append(float(t))

    # Only include complete or near-complete years (>330 days observed)
    current_year = dates[-1].year
    complete_years = [y for y, vals in yearly_temps.items() if y < current_year and len(vals) >= 330]
    complete_years.sort()

    if len(complete_years) < 5:
        return {
            "warming_trend_c_per_decade": None,
            "p_value": None,
            "r_squared": None,
            "years_evaluated": len(complete_years),
            "baseline_span": f"{complete_years[0]}-{complete_years[-1]}" if complete_years else "N/A"
        }

    means = [np.mean(yearly_temps[y]) for y in complete_years]
    res = stats.linregress(complete_years, means)

    trend_per_decade = float(res.slope * 10.0)
    return {
        "warming_trend_c_per_decade": round(trend_per_decade, 3),
        "p_value": round(float(res.pvalue), 4),
        "r_squared": round(float(res.rvalue ** 2), 3),
        "years_evaluated": len(complete_years),
        "baseline_span": f"{complete_years[0]}-{complete_years[-1]}"
    }

