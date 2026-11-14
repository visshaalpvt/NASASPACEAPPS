# KisanRadar: Scientific Analytics & Indicator Methodology
NASA Space Apps Challenge 2026: *Field Shift: Adapting Farms with NASA Data*

## 1. Climatological Baseline & Empirical Percentile Engine
Rather than relying on arbitrary fixed meteorological thresholds, KisanRadar compares every incoming observation against the historical distribution of the exact calendar window across all available years in the 2001–present baseline.

### 1.1 Calendar Window Extraction
For a target observation date $D = (\text{month } m, \text{day } d)$ and window length $W$ days:
$$\mathcal{S}_W = \{ \mathcal{A}(X_{y, m, d, W}) \mid y \in [2001, Y_{\text{current}} - 1] \}$$
Where $\mathcal{A}$ is the aggregation operator:
- **Sum** for precipitation accumulations ($W = 3, 30, 90\text{ days}$).
- **Mean** for maximum temperature ($W = 14\text{ days}$) and root-zone soil wetness ($W = 7\text{ days}$).

### 1.2 Empirical Percentile Formulation
Percentile rankings ($0.0 - 100.0$) are calculated using the Weibull mid-point plotting position to avoid boundary singularities in finite multi-year samples:
$$P(v) = \frac{\sum \mathbf{1}(x < v) + 0.5 \sum \mathbf{1}(x = v) + 0.5}{N + 1.0} \times 100$$
Where $N$ is the sample count of valid complete historical windows ($N \ge 10\text{ years}$ for SMAP, $N \ge 24\text{ years}$ for NASA POWER).

---

## 2. Crop Phenology & Growing Degree Day (GDD) Tracking
Crop vulnerability to thermal and moisture shocks is strictly phenology-dependent. Daily thermal time is computed from NASA POWER surface meteorology:
$$\text{GDD}_i = \max\left(0, \frac{T_{\max, i} + T_{\min, i}}{2} - T_{\text{base}}\right)$$

### Base Temperatures & Critical Heat Shock Windows
| Crop | $T_{\text{base}}$ | Critical Physiological Window | Critical Threshold | Documented Empirical Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Rice** | $10^\circ\text{C}$ | Panicle Initiation to Anthesis ($850 \le \text{GDD} \le 1850$) | $34.0^\circ\text{C}$ | $-10\%$ yield loss per $1^\circ\text{C}$ above $34^\circ\text{C}$ (spikelet sterility) |
| **Wheat** | $5^\circ\text{C}$ | Pre-Anthesis & Flowering ($1050 \le \text{GDD} \le 1450$) | $31.0^\circ\text{C}$ | Pollen sterility; 10–35% yield reduction under terminal heat |
| **Maize** | $10^\circ\text{C}$ | Tasseling & Silking ($950 \le \text{GDD} \le 1400$) | $35.0^\circ\text{C}$ | Tassel blasting & reduced kernel set |

Outside the critical reproductive window (e.g. at sowing and early tillering), anthesis limits do NOT apply; heat stress is evaluated against extreme vegetative heat thresholds ($36\text{--}38^\circ\text{C}$) to prevent false alarms.

---

## 3. Multi-Hazard Risk Scoring Formulations (0–100)

### 3.1 Drought Risk
Mapped via a piecewise drought function:
$$\text{Risk}(P) = \begin{cases} 0.0 & P \ge 50.0 \\ 100.0 & P \le 5.0 \\ \frac{50.0 - P}{45.0} \times 100.0 & 5.0 < P < 50.0 \end{cases}$$

- **Primary Rainfall:** GPM IMERG satellite percentile $P_{\text{rain}}$ (cross-checked with POWER MERRA-2).
- **Primary Soil Moisture:** SMAP L4 satellite root-zone percentile $P_{\text{soil}}$ (cross-checked with POWER GWETROOT).
- **Physical Soil Moisture Sanity Check (Heuristic Rule):** If absolute root-zone wetness fraction is $\theta_{\text{root}} \ge 0.50$ (soils near field capacity / saturation), soil drought risk is zeroed out regardless of multi-year percentile rank. Between $0.35$ and $0.50$, soil risk is damped linearly: $\text{Risk}_{\text{soil}} \times \frac{0.50 - \theta_{\text{root}}}{0.15}$. This physical heuristic prevents false drought alarms in humid deltas (e.g. Cauvery, Bengal Delta) where a season may rank in the lower quartile of multi-year records simply because prior years were hyper-saturated, despite current root-zone moisture being entirely adequate for crop water demand.
- **Dry-Spell Normalization:** Consecutive dry days are normalized against the historical distribution of dry spells for that exact calendar day. A normal winter dry spell (e.g. November in Punjab) does not add drought risk when soil and rainfall are at/above median.
$$\text{Base Drought} = 0.50 \times \text{Risk}(P_{\text{rain}}) + 0.50 \times \text{Risk}(P_{\text{soil}})$$
$$\text{Drought Score} = \min(100, \text{Base Drought} + \delta_{\text{dry}})$$

### 3.2 Heat Risk (Phenology Stage-Gated)
- **During Sensitive Anthesis / Grain-Filling Stage:**
  $$\text{Exceedance} = \min\left(100, \frac{\text{hot\_days}_{14\text{d}} + 1.2 \times \text{hot\_days}_{\text{fc}}}{8} \times 100\right)$$
  $$\text{Heat Score} = \min(100, \text{round}(0.70 \times \text{Exceedance} + 0.30 \times P_{T_{\max}}))$$
- **During Vegetative / Emergence Stage:**
  Anthesis thresholds do not apply. Heat score reflects seasonal temperature percentiles ($0\text{--}25$), preventing false alarms at sowing.

### 3.3 Flood Hazard (with Absolute 20mm Floor)
Compares 72-hour precipitation (NASA GPM IMERG and numerical forecast) against the **local 95th percentile of 3-day rainfall** ($R_{95}$) derived from 25 years of NASA POWER daily observations:
- If $\max(\text{IMERG}_{72\text{h}}, \text{Forecast}_{3\text{d}}) < 20.0\text{ mm}$: $\text{Flood Score} = 0$.
- Otherwise:
  $$\text{Flood Score} = \min\left(100, \text{round}\left(\frac{\max(\text{IMERG}_{72\text{h}}, \text{Forecast}_{3\text{d}})}{R_{95}} \times 75\right)\right)$$

### 3.4 Vegetation Stress (Canopy & Anomaly Aware)
- **Early Vegetative ($\text{GDD} < \text{GDD}_{\text{min\_canopy}}$) or Ripening ($\text{GDD} > \text{GDD}_{\text{max\_canopy}}$):**
  Marked as `not applicable at this stage` (bare soil or natural senescence). Score is `None`.
- **Active Canopy:**
  Evaluated against the multi-year (2001-present) MODIS 16-day composite baseline anomaly ($\Delta\text{NDVI} = \text{NDVI}_{\text{observed}} - \overline{\text{NDVI}}_{\text{hist}}$):
  - If $\Delta\text{NDVI} \ge 0$: Stress score is $0\text{--}15$ (healthy canopy).
  - If $\Delta\text{NDVI} < 0$: Stress score scales with degradation below historical norm.
  - Landsat 8/9 (30m) parcel NDVI is compared to MODIS (250m) for field-vs-regional context.

### 3.5 Overall Weighted Risk Index & Confidence Rating
- When vegetation is applicable:
  $$\text{Overall} = 0.35 \times \text{Drought} + 0.30 \times \text{Heat} + 0.20 \times \text{Flood} + 0.15 \times \text{Vegetation}$$
- When vegetation is stage-gated out, weights redistribute proportionally:
  $$\text{Overall} = 0.45 \times \text{Drought} + 0.35 \times \text{Heat} + 0.20 \times \text{Flood}$$
- **Data Confidence Rating:**
  - Evaluated on live feeds count (HIGH for $\ge 5$, MEDIUM for $3\text{--}4$, LOW for $<3$).
  - **Precipitation Disagreement Flag:** If NASA POWER (MERRA-2 reanalysis) and NASA GPM IMERG (satellite) differ by $>30\%$ **AND** the absolute gap exceeds $10.0\text{ mm}$, confidence rating is downgraded by one tier with an explicit notice.

---

## 4. Literature-Derived Yield Impact & STRV Buffers
- **Estimation Paradigm:** Literature-based scenario estimate (ICAR-NICRA, IPCC AR6, IRRI trials), **not machine learning on proprietary farm datasets**.
- **Assumed Regional Baseline Yields:** Assumed baseline yields (Rice: 3.8 t/ha, Wheat: 3.4 t/ha, Maize: 4.2 t/ha) are regional district averages sourced from the Directorate of Economics and Statistics (DES), Ministry of Agriculture & Farmers Welfare, Government of India (2018–2022 multi-year district crop harvest reports).
- **Phenology Stage Gating:** 
  - *Maturity/Harvesting:* When a crop reaches **Ripening / Physiological Maturity / Harvest**, yield impact estimation is gated out (`yield_applicable: False`, unmitigated loss $0.0\%$), because the crop cycle is complete.
  - *Emergence/Newly Sown:* When a crop is newly sown ($<14\text{ days}$ or $\text{GDD} < 150$), yield loss is gated out (`yield_applicable: False`, unmitigated loss $0.0\%$), because no harvestable biomass is at risk during germination/emergence.
- **Wheat Terminal Heat Cap:** Heat loss during reproductive grain-filling is capped at $25.0\%$ (matching the documented $10\text{--}35\%$ range from the March 2022 heatwave benchmark, labeled as model upper cap).
- **STRV Resilience Buffers:**
  - *Swarna-Sub1:* Protects +1.0 to 3.0 t/ha against flash flood submergence (IRRI trials; not effective under stagnant flooding deeper than 20 cm for over 20 days).
  - *Sahbhagi Dhan:* Protects +0.8 to 1.0 t/ha under drought stress.
  - *Safe Alternate Wetting and Drying (Safe AWD):* Conserves 15–20% irrigation water (IRRI guidelines; referenced in research brief).

---

## 5. Spatial Resolution Caveats & Provenance
- **NASA GRACE / GRACE-FO Tellus MASCON CRI:** Regional gravimetric footprint (~300 km, through 2024-09). Represents regional total water storage trends; **never parcel-scale groundwater tables**.
- **NASA POWER:** ~0.5° x 0.5° (~50 km) MERRA-2 assimilation grid.
- **NASA SMAP L4:** 9 km global land model assimilation.
- **NASA GPM IMERG (V07):** ~10 km multi-satellite precipitation.
- **MODIS (MOD13Q1 / MOD11A1):** 250 m (NDVI) / 1 km (LST).
- **Landsat 8/9 (Collection 2 Tier 1 L2):** 30 m field parcel level.
- **Open-Meteo NWP:** ~11 km numerical forecast (explicitly labeled as non-NASA NWP).

---

## 6. Heuristics & Record Length Caveats
- **Saturated-Soil Drought Override (Heuristic):** When absolute root-zone wetness fraction $\theta_{\text{root}} \ge 0.50$ (near field capacity), soil drought risk is zeroed out regardless of historical percentile. This is a physical heuristic, not a statistical model, and is documented as such.
- **SMAP Short Record:** SMAP L4 data begins in 2015, providing ~10–12 years of historical comparison. Percentiles computed from this short record are less stable than the 24-year NASA POWER baseline. The UI labels SMAP as "(short record 2015+)".
- **Safe AWD Water Savings (15–20%):** Referenced from IRRI Safe AWD guidelines and research brief; exact savings vary by soil type, season, and water management.
