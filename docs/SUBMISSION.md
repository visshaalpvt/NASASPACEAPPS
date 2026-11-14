# 🚀 KisanRadar: NASA Space Apps Challenge 2026 Submission Document

> **Challenge:** *Field Shift: Adapting Farms with NASA Data*  
> **Team:** TODO: Team Name  
> **Members:** TODO: List member names  
> **Submission Deadline:** Sunday 15 November 2026, 11:59 PM Local Event Time  

---

## 1. Official Space Apps Submission Portal Fields

### Project Name
**KisanRadar: Hyper-Local Multi-Hazard Agricultural Resilience Platform**

### High-Level Summary (Short Description)
KisanRadar transforms multi-mission NASA Earth observations (GPM IMERG, SMAP, POWER, MODIS, Landsat 8/9, GRACE-FO) into hyper-local, stage-gated climate risk assessments and empirical adaptation advisories for smallholder farmers across South Asia. By evaluating live telemetry against localized 2001–present empirical baselines and crop Growing Degree Days (GDD), KisanRadar diagnoses drought, terminal heat, flood, and vegetation stress with complete data provenance and zero synthetic data. Actionable advisories (Safe AWD, Swarna-Sub1, Sahbhagi Dhan, Happy Seeder mulching) are delivered in 6 regional languages alongside interactive historical shock replays.

### Link to Demo
- **Slide Deck (7 Slides):** `TODO: Insert slide deck PDF link` / `docs/slides/SLIDES.md`
- **30-Second Video Demo:** `TODO: Insert YouTube link` *(30-second screen capture with English subtitles)*

### Link to Final Project
- **Public GitHub Repository:** `https://github.com/visshaalpvt/NASASPACEAPPS` *(Contains complete verified codebase, tests, Dockerfile, documentation, and precomputed real telemetry)*
- **Live Interactive Demo:** `TODO: Insert live demo URL` *(or Hugging Face Spaces Docker)*

---

### Detailed Description

#### The Problem: The Last-Mile NASA Data Gap for Smallholders
Across South Asia, 86% of India's farmers cultivate holdings under 2 hectares, bearing the brunt of accelerating climate extremes:
- **Terminal heatwaves in Punjab:** In March 2022, temperatures reached 40°C by mid-March during wheat grain filling, triggering extensive pollen sterility and 10–35% yield losses.
- **Flash floods in the Indus Basin and Bengal Delta:** In August 2022, about one-third of Pakistan was inundated, with over 8 million acres of crops lost to monsoon deluges.

While NASA operates constellation-grade Earth observation missions, raw files (HDF5, NetCDF, GEE collections) are trapped in scientific silos. Furthermore, generic weather apps provide regional forecasts without crop phenology context, generating false alarms (e.g., alarming a farmer about low NDVI on a field that was sown 4 days ago, or applying flowering heat thresholds to a vegetative crop).

#### The Solution: KisanRadar Multi-Mission Earth Observation Engine
KisanRadar bridges the gap from space to soil:
1. **Zero-Mock, Multi-Mission Live Data Integration:**
   - **Precipitation:** NASA GPM IMERG (V07) at 10 km provides 30-day and 72-hour rainfall accumulation, cross-checked against NASA POWER MERRA-2 (50 km).
   - **Soil Moisture:** NASA SMAP Level-4 SPL4SMGP assimilation provides 9 km daily root-zone soil wetness, compared against 2015–present calendar-window historical records using Weibull plotting positions.
   - **Thermal Climatology:** NASA POWER daily surface meteorology spanning 2001 to present (>9,400 daily records per point) establishes local percentiles and GDD thermal time.
   - **Vegetation & Land Surface Temperature:** MODIS Terra (MOD13Q1 250m NDVI and MOD11A1 1km LST) yields 25-year historical anomaly distributions, paired with 30m Landsat 8/9 parcel imagery.
   - **Regional Hydrology:** NASA GRACE/GRACE-FO mascon CRI provides decadal total water storage trends (~300 km regional footprint through 2024-09).
   - **NWP Forecast:** Open-Meteo 7-day numerical weather predictions provide forward-looking precipitation and temperature trajectory.

2. **Crop Phenology & Scientific Stage Gating:**
   - Thermal accumulation (GDD with Tbase = 10°C for rice/maize, 5°C for wheat) models biological stage.
   - **Terminal Heat Gating:** Wheat's critical 31°C threshold is strictly active during the reproductive anthesis window (GDD 1050 to 1450). During vegetative tillering, extreme vegetative thresholds (36–38°C) prevent false alarms.
   - **Canopy Gating:** NDVI vegetation stress is suppressed during emergence (bare soil) and ripening (natural senescence).
   - **Flood Floor:** A strict 20 mm rainfall floor ensures dry-season showers never trigger flood false alarms.

3. **Literature-Derived Scenario Impact & STRV Adaptation:**
   - Yield penalties are modeled via literature-derived damage functions (ICAR-NICRA, IPCC AR6, IRRI field trials) and labeled as **scenario estimates**.
   - Wheat terminal heat losses are calibrated against the March 2022 benchmark (25% cap within the documented 10–35% range; model at upper cap).
   - Crops at maturity are gated out (0.0% unmitigated loss) to reflect post-season completion.
   - Grounded adaptation packages: Safe Alternate Wetting and Drying (Safe AWD, saving 15–20% water), Submergence-Tolerant Rice (Swarna-Sub1, +1.0 to 3.0 t/ha recovery, IRRI trials; not effective under stagnant flooding deeper than 20 cm for over 20 days), Drought-Tolerant Cultivars (Sahbhagi Dhan, +0.8 to 1.0 t/ha), and Happy Seeder in-situ residue mulching (common practice).
   - Multilingual accessibility in **English, Hindi, Tamil, Bengali, Punjabi, and Telugu**.

4. **Archived NASA Telemetry Replays:**
   Interactive replays allow judges and users to examine authentic NASA telemetry during landmark historical shocks:
   - **Punjab March 2022 Heat Shock:** Temperatures reached 40°C by mid-March. Replay measured: MODIS LST Day 38.0°C, POWER Tmax 38.3°C, Heat Risk 96/100, Yield Loss 25.0% (model at upper cap).
   - **Pakistan Sindh August 2022 Deluge:** About one-third of Pakistan inundated, over 8 million acres of crops lost. Replay measured: GPM IMERG 30d rain 563.5 mm (100th percentile), Flood Risk 100/100.
   - **Tamil Nadu December 2023 Cyclone Michaung:** GPM IMERG 30d rain 656.2 mm (95.8th percentile), NASA POWER cross-check 556.7 mm (90.9th percentile, 15.2% gap — below 30% flag threshold), Flood Risk 100/100.

---

### NASA Data
The following authentic NASA datasets are queried and computed live in KisanRadar:
1. **NASA GPM IMERG (Global Precipitation Measurement Integrated Multi-satellitE Retrievals for GPM):**
   - *Dataset ID:* `NASA/GPM_L3/IMERG_V07` (Late Run, 0.1° / ~10 km spatial resolution).
   - *Usage:* Primary 30-day rainfall accumulation and 72-hour extreme flood accumulation.
2. **NASA SMAP (Soil Moisture Active Passive):**
   - *Dataset ID:* `NASA/SMAP/SPL4SMGP/008` (Level-4 Global Daily 9 km Surface and Root-Zone Soil Moisture).
   - *Usage:* Root-zone soil wetness fraction and multi-year calendar window percentile.
3. **NASA POWER (Prediction of Worldwide Energy Resources):**
   - *Dataset ID:* `NASA_POWER_AG_POINT_DAILY_V2` (MERRA-2 daily agroclimatology from 2001 to present, ~50 km).
   - *Usage:* 25-year climatological temperature and precipitation baseline (>9,400 points), decadal surface warming trend, Growing Degree Day (GDD) accumulation, and reanalysis precipitation cross-check.
4. **NASA MODIS Terra (Moderate Resolution Imaging Spectroradiometer):**
   - *Dataset IDs:* `MODIS/061/MOD13Q1` (250m 16-day Vegetation Indices NDVI) and `MODIS/061/MOD11A1` (1km Daily Land Surface Temperature).
   - *Usage:* Multi-year regional NDVI baseline anomaly and day-time land surface skin temperature.
5. **NASA / USGS Landsat 8 & 9:**
   - *Dataset ID:* `LANDSAT/LC08/C02/T1_L2` and `LANDSAT/LC09/C02/T1_L2` (Collection 2 Tier 1 Level-2 Surface Reflectance, 30m).
   - *Usage:* Parcel-scale field NDVI calculation compared to 250m regional MODIS baseline.
6. **NASA GRACE / GRACE-FO (Gravity Recovery and Climate Experiment Follow-On):**
   - *Dataset ID:* `NASA/GRACE/MASS_GRIDS_V04/MASCON_CRI` (JPL RL06M.1 v04 Mascon CRI, ~300 km gravimetric footprint).
   - *Usage:* Decadal regional total water storage anomaly trend through September 2024.
7. **NASA GIBS (Global Imagery Browse Services):**
   - *Dataset IDs:* `MODIS_Terra_CorrectedReflectance_TrueColor`, `MODIS_Terra_Land_Surface_Temp_Day`, `IMERG_Precipitation_Rate`, `MODIS_Terra_L3_NDVI_Monthly`.
   - *Usage:* Interactive WMTS satellite map overlays with 24-hour cached XML capabilities.

---

### Space Agency Partner & Other Data
- **Google Earth Engine (GEE):** Cloud geospatial analysis platform used to query MODIS, Landsat, SMAP, GRACE-FO, and GPM IMERG image collections.
- **Open-Meteo Numerical Weather Prediction (NWP):** `OPEN_METEO_SEAMLESS_DAILY_V1` (~11 km resolution) provides 7-day forward forecasts for maximum temperature and precipitation accumulation (explicitly labeled as non-NASA NWP).
- **OpenStreetMap:** Standard base tile cartography (`https://{s}.tile.openstreetmap.org`).
- **ICAR-NICRA & IRRI Field Documentation:** Agronomic thresholds and adaptation package references (Swarna-Sub1, Sahbhagi Dhan, Happy Seeder, Safe AWD).
- **Python Libraries:** FastAPI, Uvicorn, Google Earth Engine Python API (`earthengine-api`), NumPy, SciPy, Requests, Pydantic, Dotenv, Playwright, Pytest.
- **Frontend Libraries:** Leaflet.js (v1.9.4), Chart.js (v4.4.1).

---

### Use of Artificial Intelligence
In accordance with the 2026 Space Apps Challenge rules on AI disclosure:
- **LLM Usage:** ChatGPT, Claude, and a Gemini-based coding agent were used as development assistants for code structure, drafting multilingual translations (Hindi, Tamil, Bengali, Punjabi, Telugu), and generating unit test assertions. An AI-compiled research brief was used to collate published field-trial data and agronomic thresholds.
- **No Synthetic Earth Observation Data:** No AI tools were used to generate, invent, or interpolate NASA satellite observation values. Every number in KisanRadar is retrieved directly from NASA APIs or Google Earth Engine.
- **Machine Translation Disclaimer:** All non-English advisory text generated in the application is explicitly labeled with the disclaimer: *"Machine-translated, verify with local extension / Krishi Vigyan Kendra (KVK)."*

---

## 2. Seven-Slide Demo Deck (Strict 7-Slide Limit)

```
================================================================================
SLIDE 1: TITLE & CHALLENGE
--------------------------------------------------------------------------------
Title: KisanRadar: Hyper-Local Multi-Hazard Resilience for Smallholders
Subtitle: NASA Space Apps Challenge 2026 | 'Field Shift: Adapting Farms with NASA Data'
Team: TODO: Team Name | Members: TODO: List member names
Core Tagline: "Bridging the last-mile gap from NASA Earth observations to 1-hectare farms."
Open Source: MIT License | Zero Mock Data
================================================================================

================================================================================
SLIDE 2: THE PROBLEM: TRAPPED TELEMETRY & FALSE ALARMS
--------------------------------------------------------------------------------
- 86% of India's farmers cultivate holdings under 2 hectares.
- Terminal Heat: March 2022 reached 40°C by mid-March in Punjab (10–35% wheat yield loss).
- Flash Floods: August 2022 inundated 1/3 of Pakistan; over 8M crop acres lost.
- Trapped Data: NASA constellation telemetry is siloed in HDF5/NetCDF/GEE archives.
- False Alarms: Generic weather apps ignore crop stage (e.g. low NDVI alarm on bare soil).
================================================================================

================================================================================
SLIDE 3: MULTI-MISSION NASA DATA PIPELINE (ZERO MOCK DATA)
--------------------------------------------------------------------------------
- GPM IMERG (10 km): 30-day rain & 72-hour extreme precipitation.
- SMAP L4 (9 km): Root-zone soil wetness percentile vs 2015-present records.
- NASA POWER (50 km): 25-year climatological baseline (>9,400 daily points) & GDD thermal time.
- MODIS (250m) & Landsat 8/9 (30m): Parcel NDVI anomaly vs 2001+ baseline.
- GRACE-FO (~300 km): Regional total water storage trend through 2024-09.
- GIBS: Interactive real-time satellite imagery overlays.
================================================================================

================================================================================
SLIDE 4: THE SCIENCE ENGINE: PERCENTILES & GDD PHENOLOGY
--------------------------------------------------------------------------------
- Percentiles over Fixed Limits: Every reading vs 2001-present window distribution.
- GDD Phenology: Tracks crop stage (Tbase 10°C rice/maize, 5°C wheat).
- Stage Gating: Wheat 31°C limit active only during flowering/grain-fill.
- Canopy Gating: NDVI stress suppressed during emergence and ripening.
- 20 mm Flood Floor: Light showers never trigger flood alerts.
================================================================================

================================================================================
SLIDE 5: ARCHIVED TELEMETRY REPLAYS: VERIFIED CLIMATE SHOCKS
--------------------------------------------------------------------------------
- Punjab March 2022 Terminal Heat (Wheat):
  * Temperatures reached 40°C by mid-March. Replay measured: POWER 38.3°C, MODIS 38.0°C.
  * Heat Risk 96/100 | Yield Loss: documented 10–35%; model at upper cap (25%).
- Sindh August 2022 Deluge (Rice):
  * 1/3 of Pakistan inundated; >8M acres lost. IMERG 30d: 563.5 mm (100th pctl). Flood Risk 100/100.
- Tamil Nadu December 2023 Cyclone Michaung (Rice):
  * IMERG 30d: 656.2 mm (95.8th pctl); POWER cross-check: 556.7 mm (90.9th pctl, 15.2% gap).
  * Flood Risk 100/100.
================================================================================

================================================================================
SLIDE 6: GROUNDED ACTIONABLE ADVISORIES & STRV BUFFERS
--------------------------------------------------------------------------------
- Safe AWD: Field water tube saves 15–20% irrigation water without yield penalty.
- Swarna-Sub1: Submergence-tolerant rice (+1.0 to 3.0 t/ha). Not effective under stagnant flooding >20 cm for >20 days.
- Sahbhagi Dhan: Drought-tolerant rice (+0.8 to 1.0 t/ha under water stress).
- Heat Defense (common practice): HD 3385, PBW 826, Happy Seeder mulching protect pollen viability.
- 6 Languages: English, Hindi, Tamil, Bengali, Punjabi, Telugu.
================================================================================

================================================================================
SLIDE 7: OPEN SOURCE, PROVENANCE & HIGH-PERFORMANCE ARCHITECTURE
--------------------------------------------------------------------------------
- Full Transparency: Dataset ID, observation date, latency, and caveats displayed.
- Performance: Cached presets 0.3 s; live analysis ~19 s cold.
- Cross-Sensor Audit: Flags satellite vs reanalysis discrepancies (>30% & >10mm).
- Open Source: MIT License, Dockerized, 15/15 passing automated regression tests.
- Zero Mock Telemetry: All observations queried from NASA APIs / Earth Engine.
================================================================================
```
```

---

## 3. Thirty-Second Video Demo Script (Strict 30-Second Limit)

| Time | Video Screen Action | Spoken Voiceover (or On-Screen Captions) | English Subtitles |
| :--- | :--- | :--- | :--- |
| **0:00 - 0:06** | Browser opens to KisanRadar centered on **Ludhiana, Punjab (Wheat)**. Green gauges appear with HIGH confidence (7 live feeds). | *"Smallholder farmers face compound climate risks, but NASA telemetry remains out of reach. Welcome to KisanRadar."* | `Smallholder farmers face compound climate risks, but NASA telemetry remains out of reach. Welcome to KisanRadar.` |
| **0:06 - 0:13** | Point to **Stage Gated: Emergence** (0% loss, no false alarms) and **Happy Seeder Mulch Advisory**. User clicks **Thanjavur, Tamil Nadu**. | *"KisanRadar queries live GPM, SMAP, and POWER feeds, evaluating real percentiles and crop phenology."* | `KisanRadar queries live GPM, SMAP, and POWER feeds, evaluating real percentiles and crop phenology.` |
| **0:13 - 0:21** | User clicks **Replay: Punjab 2022 Heat Shock**. Map flies to Punjab. Heat score spikes to 96, MODIS LST Day shows 38°C, and yield impact shows -25%. | *"In historical replay mode, experience the Punjab 2022 heat shock: archived NASA telemetry diagnoses 96 Heat Risk and triggers STRV buffers."* | `Historical replay mode: archived NASA telemetry diagnoses 96 Heat Risk and triggers STRV buffers.` |
| **0:21 - 0:30** | Scroll to **Live Data Feeds Provenance Strip** and 25-Year Climatological Warming Chart. Language toggle shifts to Punjabi and Hindi. | *"With complete data provenance, zero mock data, and 6 languages, KisanRadar puts NASA Earth observations into farmers' hands."* | `Complete provenance, zero mock data, and 6 languages: NASA Earth observations in farmers' hands.` |

---

## 4. Verification Check Before Final Submission

- [x] **Strict Time Limits Respected:** Slide deck is exactly 7 slides; video demo script is exactly 30 seconds.
- [x] **No Mock or Synthetic Data:** 100% of telemetry comes from authentic NASA APIs and Google Earth Engine.
- [x] **Data Integrity & Honesty:** Yield impacts labeled as scenario estimates; GRACE labeled as 300 km regional trend ending 2024-09.
- [x] **Multi-Language Accessibility:** 6 South Asian languages with machine-translation disclaimer.
- [x] **Automated Test Suite:** 15/15 pytest analytics tests passing; Playwright browser test passing with 0 JS errors.
- [x] **Repo Free of Secrets:** `.gitignore` excludes `.env`, `data/cache`, and credentials.
