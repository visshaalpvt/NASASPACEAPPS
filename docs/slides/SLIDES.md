# KisanRadar: Hyper-Local Multi-Hazard Agricultural Resilience Platform
NASA Space Apps Challenge 2026: *Field Shift: Adapting Farms with NASA Data*

---

<!-- slide -->
# Slide 1: Title & Challenge
### KisanRadar: Hyper-Local Multi-Hazard Resilience for Smallholders
**NASA Space Apps Challenge 2026 | Challenge Track: 'Field Shift: Adapting Farms with NASA Data'**
**Team:** KisanRadar  
*Bridging the last-mile gap from NASA Earth observations to 1-hectare farms.*

- **Multi-Mission NASA Telemetry:** GPM IMERG, SMAP L4, NASA POWER, MODIS, Landsat 8/9, GRACE-FO, GIBS
- **Target Audience:** Smallholder farmers in South Asia (India, Pakistan, Bangladesh)
- **Open Source:** MIT License | Zero Mock Data

---

<!-- slide -->
# Slide 2: The Problem: Trapped Telemetry & False Alarms
### Why Existing Weather Apps Fail Smallholder Farmers

1. **Catastrophic Shocks:**
   - *Terminal Heatwaves:* March 2022 heat shock in Punjab caused 10–35% yield failure.
   - *Flash Floods & Deluges:* August 2022 monsoon deluges in Sindh (>550 mm) drowned standing crops.
   - *Groundwater Depletion:* Severe regional drawdown in Cauvery and Indus basins.
2. **The Scientific Silo:**
   - Constellation telemetry is trapped in complex scientific formats (HDF5, NetCDF, GEE collections).
3. **The False Alarm Crisis:**
   - Fixed thresholds ignore crop biology: alarming a farmer about "low NDVI" on bare soil 4 days after sowing, or applying flowering heat limits to a vegetative crop.

---

<!-- slide -->
# Slide 3: Multi-Mission NASA Earth Observation Pipeline
### Direct Integration of Authentic NASA Satellite Telemetry (Zero Synthetic Data)

| Mission / Sensor | Dataset ID | Resolution | Operational Role |
| :--- | :--- | :--- | :--- |
| **NASA GPM IMERG** | `NASA/GPM_L3/IMERG_V07` | 10 km | Primary 30-day rainfall accumulation & 72h flood risk |
| **NASA SMAP L4** | `NASA/SMAP/SPL4SMGP/008` | 9 km | Daily root-zone soil wetness & historical percentile |
| **NASA POWER** | `NASA_POWER_AG_POINT_DAILY_V2` | 50 km | 25-yr daily baseline (>9,400 pts), GDD thermal time |
| **MODIS Terra** | `MOD13Q1` / `MOD11A1` | 250m / 1km | 2001+ NDVI anomaly & daytime Land Surface Temp (LST) |
| **Landsat 8 & 9** | `LANDSAT/LC08/C02/T1_L2` | 30 m | Parcel-scale field NDVI vs regional baseline |
| **NASA GRACE-FO** | `MASS_GRIDS_V04/MASCON_CRI` | ~300 km | Regional water storage trend through 2024-09 |
| **NASA GIBS** | Global WMTS | NRT | Interactive Leaflet satellite map layers |

---

<!-- slide -->
# Slide 4: The Science Engine: Percentiles & GDD Phenology
### Science-Gated Diagnoses Eliminating False Alarms

- **Empirical Climatological Percentiles:**
  Every observation is evaluated against the 2001–present distribution for the exact calendar window ($P \ge 50 \implies 0$ drought risk; $P \le 5 \implies 100$ extreme drought).
- **Growing Degree Day (GDD) Tracking:**
  Accurately tracks crop developmental stages ($T_{\text{base}} = 10^\circ\text{C}$ rice/maize, $5^\circ\text{C}$ wheat).
- **Stage-Gated Thresholds:**
  Wheat critical $31^\circ\text{C}$ limit is active **only during reproductive flowering/grain-filling**.
- **Canopy Gating:**
  NDVI vegetation stress is suppressed during emergence (bare soil) and ripening (natural senescence).
- **Absolute 20mm Flood Floor:**
  Light dry-season showers never trigger flood alerts.

---

<!-- slide -->
# Slide 5: Archived Telemetry Replays: Verified Historical Shocks
### Real Historical Extreme Events Replayed with Authentic NASA Data

1. **Punjab March 2022 Terminal Heat Shock (Wheat):**
   - Archived NASA POWER Tmax: Exceeded 36–38°C during grain fill.
   - MODIS LST Day: 38.0°C | Heat Risk: 96/100.
   - Scenario Yield Loss: Capped at 25.0% (CIMMYT/ICAR benchmark: 10–35%).
2. **Pakistan Sindh August 2022 Monsoon Deluge (Rice):**
   - NASA GPM IMERG 30d Rain: 563.5 mm (100th percentile).
   - Flood Risk: 100/100 | Swarna-Sub1 submergence resilience activated.
3. **Tamil Nadu December 2023 Cyclone Michaung (Rice):**
   - NASA GPM IMERG 30d Rain: 656.3 mm (Coastal Chennai epicenter).
   - Flood Risk: 100/100 | Field drainage advisory triggered.

---

<!-- slide -->
# Slide 6: Actionable Resilience & STRV Adaptation
### Empirical Solutions Grounded in ICAR, IRRI, and CIMMYT Trials

- **Safe Alternate Wetting and Drying (Safe AWD):**
  Install 30 cm field water tube (*pani pipe*); saves 15–20% irrigation water without yield penalty.
- **Submergence-Tolerant Rice (Swarna-Sub1 / SUB1A):**
  Withstands 14 days of complete underwater submergence (+1.0 to 3.0 t/ha yield recovery, IRRI trials).
- **Drought-Tolerant Cultivars (Sahbhagi Dhan / DRR 42):**
  Provides +0.8 to 1.0 t/ha advantage under drought stress.
- **Terminal Heat Defense (HD 3385 & Residue Mulching):**
  Protects pollen viability and conserves seedbed moisture using Happy Seeder.
- **Maturity Stage Gating:**
  Shifts from in-season irrigation to field drainage, harvest readiness, and next-season variety selection.
- **6 Regional Languages:** English, Hindi, Tamil, Bengali, Punjabi, Telugu.

---

<!-- slide -->
# Slide 7: Sub-Second Architecture & Full Provenance
### Production-Grade Performance and Honesty

- **Sub-Second Performance:**
  0.29s cached response time across South Asia, enabling fluid interactive browsing.
- **Complete Provenance Strip:**
  Every risk score displays the underlying sensor dataset ID, observation date, latency, and status.
- **Cross-Sensor Discrepancy Auditing:**
  Flags and hedges satellite vs reanalysis differences (>30% & >10mm) automatically.
- **Open Source & Fully Verified:**
  - 15/15 automated pytest regression tests passing.
  - Headless Playwright browser test passing with 0 JavaScript errors.
  - Clean repository with secrets excluded via `.gitignore` and MIT License.
