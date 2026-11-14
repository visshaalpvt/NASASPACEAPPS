# KisanRadar: Hyper-Local Multi-Hazard Agricultural Resilience Platform
NASA Space Apps Challenge 2026: *Field Shift: Adapting Farms with NASA Data*

---

<!-- slide -->
# Slide 1: Title & Challenge
### KisanRadar: Hyper-Local Multi-Hazard Resilience for Smallholders
**NASA Space Apps Challenge 2026 | 'Field Shift: Adapting Farms with NASA Data'**
**Team:** TODO: Team Name | **Members:** TODO: List member names
- Multi-Mission NASA Feeds: GPM IMERG, SMAP, POWER, MODIS, Landsat 8/9, GRACE-FO
- Zero mock telemetry: authentic satellite observations for smallholder farms
- Open source (MIT License) with 6 South Asian regional languages

---

<!-- slide -->
# Slide 2: The Problem: Trapped Telemetry & False Alarms
### Why Generic Weather Apps Fail Smallholders
- 86% of India's farmers cultivate holdings under 2 hectares.
- Terminal Heat: Temperatures reached 40°C by mid-March in Punjab (10–35% wheat loss).
- Flash Floods: August 2022 inundated 1/3 of Pakistan; >8M crop acres lost.
- Telemetry Siloed: Constellation data trapped in scientific HDF5/NetCDF/GEE archives.
- False Alarms: Generic apps ignore crop stage (e.g. low NDVI alarm on bare soil).

---

<!-- slide -->
# Slide 3: Multi-Mission NASA Earth Observation Pipeline
### Direct Integration of Authentic NASA Satellite Telemetry (Zero Mock Data)
- GPM IMERG (10 km): 30-day rain accumulation & 72-hour extreme precipitation.
- SMAP L4 (9 km): Daily root-zone soil wetness percentile vs 2015+ record.
- NASA POWER (50 km): 25-year daily baseline (>9,400 points) & GDD thermal time.
- MODIS (250m) & Landsat 8/9 (30m): Parcel NDVI anomaly vs 2001+ baseline.
- GRACE-FO (~300 km): Regional total water storage trend through 2024-09.

---

<!-- slide -->
# Slide 4: The Science Engine: Percentiles & GDD Phenology
### Science-Gated Diagnoses Eliminating False Alarms
- Percentiles over Fixed Limits: Every observation ranked against calendar-window baseline.
- GDD Phenology: Tracks biological crop stage (Tbase 10°C rice/maize, 5°C wheat).
- Anthesis Stage Gating: Wheat 31°C threshold active only during flowering/grain-fill.
- Canopy Gating: NDVI vegetation stress suppressed during emergence and ripening.
- 20 mm Flood Floor: Dry-season showers never trigger flood alerts.

---

<!-- slide -->
# Slide 5: Archived Telemetry Replays: Verified Historical Shocks
### Real Historical Extreme Events Replayed with Authentic NASA Data
- Punjab March 2022 Heat: Replay measured POWER 38.3°C, MODIS 38.0°C; loss capped at 25%.
- Sindh August 2022 Flood: 1/3 of Pakistan inundated; IMERG 30d 563.5 mm (100th pctl).
- Tamil Nadu Dec 2023 Cyclone: IMERG 656.2 mm vs POWER 556.7 mm (15.2% gap); Flood 100/100.
- Stage Sensitivity: Same weather produces different risk depending on sowing date.
- Complete Integrity: All historical shock replays computed from archived NASA data.

---

<!-- slide -->
# Slide 6: Actionable Resilience & STRV Adaptation
### Empirical Solutions Grounded in Published Field Trials
- Safe AWD: Field water tube saves 15–20% irrigation water without yield penalty.
- Swarna-Sub1: Submergence-tolerant rice (+1.0 to 3.0 t/ha, IRRI trials; depth/duration gated).
- Sahbhagi Dhan: Drought-tolerant rice (+0.8 to 1.0 t/ha under moisture stress).
- Heat Defense (common practice): HD 3385, PBW 826, Happy Seeder residue mulching.
- 6 Regional Languages: English, Hindi, Tamil, Bengali, Punjabi, Telugu.

---

<!-- slide -->
# Slide 7: Production Architecture & Full Provenance
### Transparent, Scalable and Rigorously Tested
- Provenance Strip: Live dataset ID, observation date, latency, and caveats displayed.
- Sensor Audit: Flags satellite vs reanalysis precipitation gaps (>30% & >10mm).
- Performance: Cached presets 0.3 s; live analysis ~19 s cold.
- Test Coverage: 15/15 passing pytest analytics tests; 0 Playwright browser errors.
- Open Source: MIT License, Dockerized for cloud deployment, zero secret leaks.