# 🚀 KisanRadar: NASA Space Apps Challenge 2026 Submission Document

> **Challenge:** *Field Shift: Adapting Farms with NASA Data*  
> **Challenge Track:** Climate Resilience & Agricultural Adaptation  
> **Team:** KisanRadar  
> **Submission Deadline:** Sunday 15 November 2026, 11:59 PM Local Event Time  

---

## 1. Official Space Apps Submission Portal Fields

### Project Name
**KisanRadar: Hyper-Local Multi-Hazard Agricultural Resilience Platform**

### High-Level Summary (Short Description)
KisanRadar transforms multi-mission NASA Earth observations (GPM IMERG, SMAP, POWER, MODIS, Landsat 8/9, GRACE-FO) into hyper-local, stage-gated climate risk assessments and empirical adaptation advisories for smallholder farmers across South Asia. By evaluating live telemetry against localized 2001–present empirical baselines and crop Growing Degree Days (GDD), KisanRadar diagnoses drought, terminal heat, flood, and vegetation stress with complete data provenance and zero synthetic data. Actionable advisories (Safe AWD, Swarna-Sub1, Sahbhagi Dhan, Happy Seeder mulching) are delivered in 6 regional languages alongside interactive historical shock replays.

### Link to Demo
- **Slide Deck (7 Slides):** `docs/slides/kisanradar_deck.pdf` / `docs/slides/SLIDES.md`
- **30-Second Video Demo:** `https://youtu.be/example-kisanradar-30s` *(30-second screen capture with English subtitles)*

### Link to Final Project
- **Public GitHub Repository:** `https://github.com/visshaalpvt/NASASPACEAPPS` *(Contains complete verified codebase, tests, Dockerfile, documentation, and precomputed real telemetry)*
- **Live Interactive Demo:** `https://kisanradar.org` *(or Hugging Face Spaces Docker)*

---

### Detailed Description

#### The Problem: The Last-Mile NASA Data Gap for Smallholders
Over 400 million smallholder farmers across South Asia manage holdings under 2 hectares while bearing the brunt of accelerating climate extremes:
- **Terminal heatwaves in Punjab:** March 2022 saw daytime temperatures surge above 36–38°C during wheat grain filling, triggering extensive pollen sterility and 10–35% yield losses.
- **Flash floods in the Indus Basin and Bengal Delta:** August 2022 monsoon deluges in Sindh (>550 mm) submerged millions of hectares of kharif paddy for weeks.
- **Groundwater depletion in the Cauvery Delta:** Intensive tubewell pumping depletes regional aquifers without farmers having visibility into regional storage trends.

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
   - Thermal accumulation (GDD with $T_{\text{base}} = 10^\circ\text{C}$ for rice/maize, $5^\circ\text{C}$ for wheat) models biological stage.
   - **Terminal Heat Gating:** Wheat's critical $31^\circ\text{C}$ threshold is strictly active during the reproductive anthesis window ($1050 \le \text{GDD} \le 1450$). During vegetative tillering, extreme vegetative thresholds ($36\text{--}38^\circ\text{C}$) prevent false alarms.
   - **Canopy Gating:** NDVI vegetation stress is suppressed during emergence (bare soil) and ripening (natural senescence).
   - **Flood Floor:** A strict 20 mm rainfall floor ensures dry-season showers never trigger flood false alarms.

3. **Literature-Derived Scenario Impact & STRV Adaptation:**
   - Yield penalties are modeled via literature-derived damage functions (ICAR-NICRA, IPCC AR6, IRRI field trials) and labeled as **scenario estimates**.
   - Wheat terminal heat losses are calibrated against the March 2022 benchmark ($25\%$ cap within the documented $10\text{--}35\%$ range).
   - Crops at maturity are gated out ($0.0\%$ unmitigated loss) to reflect post-season completion.
   - Grounded adaptation packages: Safe Alternate Wetting and Drying (Safe AWD, saving 15–20% water), Submergence-Tolerant Rice (Swarna-Sub1, withstanding 14 days underwater with $+1.8\text{ t/ha}$ recovery), Drought-Tolerant Cultivars (Sahbhagi Dhan, $+0.8\text{ to }1.0\text{ t/ha}$), and Happy Seeder in-situ residue mulching.
   - Multilingual accessibility in **English, Hindi, Tamil, Bengali, Punjabi, and Telugu**.

4. **Archived NASA Telemetry Replays:**
   Interactive replays allow judges and users to examine authentic NASA telemetry during landmark historical shocks:
   - **Punjab March 2022 Heat Shock:** MODIS LST Day ($38.0^\circ\text{C}$), POWER Tmax ($38.3^\circ\text{C}$), Heat Risk 96/100, Yield Loss 25.0%.
   - **Pakistan Sindh August 2022 Deluge:** GPM IMERG 30d rain ($563.5\text{ mm}$, 100th percentile), Flood Risk 100/100.
   - **Tamil Nadu December 2023 Cyclone Michaung:** GPM IMERG 30d rain ($656.3\text{ mm}$), Flood Risk 100/100.

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
- **Open-Meteo Numerical Weather Prediction (NWP):** `OPEN_METEO_SEAMLESS_DAILY_V1` (~11 km resolution) provides 7-day forward forecasts for maximum temperature and precipitation accumulation (explicitly labeled as non-NASA NWP).
- **OpenStreetMap:** Standard base tile cartography (`https://{s}.tile.openstreetmap.org`).
- **ICAR-NICRA & IRRI Field Documentation:** Agronomic thresholds, Stress-Tolerant Variety (STRV) yield buffers (Swarna-Sub1, Sahbhagi Dhan, HD 3385), and Safe AWD water savings percentages.
- **Python Libraries:** FastAPI, Uvicorn, Google Earth Engine Python API (`earthengine-api`), NumPy, SciPy, Requests, Pydantic, Dotenv, Playwright, Pytest.
- **Frontend Libraries:** Leaflet.js (v1.9.4), Chart.js (v4.4.1).

---

### Use of Artificial Intelligence
In accordance with the 2026 Space Apps Challenge rules on AI disclosure:
- **LLM Usage:** Claude Sonnet 4.6 and Gemini 3.8 Flash were utilized as development assistants for code structure, drafting multilingual translations (Hindi, Tamil, Bengali, Punjabi, Telugu), and generating unit test assertions.
- **No Synthetic Earth Observation Data:** No generative AI, synthetic models, or simulated fallbacks were used to produce, invent, or interpolate NASA satellite observations. Every number in KisanRadar is retrieved directly from NASA APIs or Google Earth Engine.
- **Machine Translation Disclaimer:** All non-English advisory text generated in the application is explicitly labeled with the disclaimer: *"Machine-translated, verify with local extension / Krishi Vigyan Kendra (KVK)."*

---

## 2. Seven-Slide Demo Deck (Strict 7-Slide Limit)

```
================================================================================
SLIDE 1: TITLE & CHALLENGE
--------------------------------------------------------------------------------
Title: KisanRadar: Hyper-Local Multi-Hazard Resilience for Smallholders
Subtitle: NASA Space Apps Challenge 2026 | Track: 'Field Shift: Adapting Farms with NASA Data'
Team: KisanRadar
Visual: Satellite constellation diagram connecting to a smallholder farm in South Asia.
Core Tagline: "Bridging the last-mile gap from NASA Earth observations to 1-hectare farms."
================================================================================

================================================================================
SLIDE 2: THE PROBLEM: TRAPPED TELEMETRY & FALSE ALARMS
--------------------------------------------------------------------------------
- 400M+ smallholders across South Asia face compound climate shocks: terminal heat, flash droughts, deluge.
- NASA operates premier satellite missions (GPM, SMAP, MODIS, Landsat, GRACE), but telemetry is trapped in scientific archives.
- Generic weather apps fail farmers: they ignore crop stage, generating false alarms (e.g. warning of "vegetation stress" on bare soil 4 days after sowing).
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
- Percentiles over Fixed Limits: Every observation is benchmarked against the historical distribution of its exact calendar window.
- Phenology Stage Gating: GDD models biological stage ($T_{\text{base}} = 10^\circ\text{C}$ rice, $5^\circ\text{C}$ wheat).
- Anthesis Gating: Critical $31^\circ\text{C}$ wheat threshold is active ONLY during flowering.
- Canopy Gating: NDVI stress is suppressed during emergence and ripening.
- 20mm Flood Floor: Prevents light showers from triggering false flood alerts.
================================================================================

================================================================================
SLIDE 5: ARCHIVED TELEMETRY REPLAYS: VERIFIED CLIMATE SHOCKS
--------------------------------------------------------------------------------
- Punjab March 2022 Terminal Heat Shock:
  * NASA POWER Tmax 38.3°C, MODIS LST Day 38.0°C.
  * Heat Risk: 96/100 | Scenario Yield Loss: 25.0% (CIMMYT benchmark 10-35%).
- Pakistan Sindh August 2022 Monsoon Deluge:
  * GPM IMERG: 563.5 mm (100th percentile) | Flood Risk: 100/100.
- Tamil Nadu December 2023 Cyclone Michaung:
  * GPM IMERG: 656.3 mm | Flood Risk: 100/100.
================================================================================

================================================================================
SLIDE 6: GROUNDED ACTIONABLE ADVISORIES & STRV BUFFERS
--------------------------------------------------------------------------------
- Safe AWD (Field Water Tube): Saves 15-20% irrigation water without yield penalty.
- Swarna-Sub1: Withstands 14 days of complete underwater submergence (+1.8 t/ha protected).
- Sahbhagi Dhan: Drought-tolerant rice (+0.8 to 1.0 t/ha advantage under water stress).
- HD 3385 & Residue Mulch: Protects wheat pollen viability and conserves seedbed moisture.
- Multilingual in 6 Regional Languages: English, Hindi, Tamil, Bengali, Punjabi, Telugu.
================================================================================

================================================================================
SLIDE 7: OPEN SOURCE, PROVENANCE & SUB-SECOND ARCHITECTURE
--------------------------------------------------------------------------------
- Complete Transparency: Every score is accompanied by sensor dataset ID, observation timestamp, latency, and caveat notes.
- Sub-Second Response: 0.29s cached response time for seamless live farmer interaction.
- Cross-Sensor Integrity: Automatically flags and explains satellite-reanalysis discrepancies (>30% & >10mm).
- Open Source: MIT Licensed, Dockerized for cloud deployment, 15/15 passing automated tests.
================================================================================
```

---

## 3. Thirty-Second Video Demo Script (Strict 30-Second Limit)

| Time | Video Screen Action | Spoken Voiceover (or On-Screen Captions) | English Subtitles |
| :--- | :--- | :--- | :--- |
| **0:00 - 0:06** | Browser opens to KisanRadar map. User clicks **Thanjavur, Tamil Nadu**. Multi-hazard gauges appear. | *"Smallholder farmers face compound climate risks, but NASA telemetry remains out of reach. Welcome to KisanRadar."* | `Smallholder farmers face compound climate risks, but NASA telemetry remains out of reach. Welcome to KisanRadar.` |
| **0:06 - 0:13** | Zoom into gauges: Drought, Heat, Flood, Veg. Point to **Stage Gated: Ripening** and **Harvest Readiness Advisory** in Tamil. | *"KisanRadar queries live GPM, SMAP, and POWER feeds, evaluating real percentiles and crop phenology."* | `KisanRadar queries live GPM, SMAP, and POWER feeds, evaluating real percentiles and crop phenology.` |
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
