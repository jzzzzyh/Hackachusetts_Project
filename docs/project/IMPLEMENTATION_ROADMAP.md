# Implementation Roadmap
*Hackachusetts — Civic Issue Predictor*

---

## Goal
Ship a working MVP first. Then refine. Then demo.

**MVP definition:** A model that takes Boston neighborhood + date → outputs a risk score for potholes/sidewalk damage. Backed by real 311 + weather data. Shown on a map.

---

## Phase 1 — Environment Setup (30 min)
**Goal:** Everyone can run the code.

- [ ] Create `requirements.txt` with all dependencies
- [ ] Create `src/` folder structure
- [ ] Verify Python 3.10+ is available on all team machines
- [ ] Test that the CKAN API and Open-Meteo API are reachable

**Deliverable:** `pip install -r requirements.txt` works on all machines.

**Key files:**
- `requirements.txt`
- `src/__init__.py`

---

## Phase 2 — Data Fetch (45 min)
**Goal:** Pull raw data to disk. No modeling yet.

- [ ] Write `src/fetch_data.py`
  - Fetch 311 reports for 2018–2024 via CKAN API (paginated, saves to `data/raw/311_YYYY.csv`)
  - Fetch Boston weather 2018–2024 from Open-Meteo (saves to `data/raw/weather_boston.csv`)
  - Fetch neighborhood boundaries GeoJSON (saves to `data/raw/boston_neighborhoods.geojson`)
- [ ] Run the script, verify files land in `data/raw/`
- [ ] Quick sanity check: print row counts and column names

**Deliverable:** `data/raw/` has 311 CSVs + weather CSV + neighborhoods GeoJSON.

**Key files:**
- `src/fetch_data.py`

---

## Phase 3 — EDA & Data Cleaning (45 min)
**Goal:** Understand the data before modeling.

- [ ] Open `notebooks/01_eda.ipynb`
- [ ] Load 2024 311 data, filter to potholes + sidewalk + streetlights
- [ ] Plot: report counts by month (should see spring pothole spike)
- [ ] Plot: report counts by neighborhood (heatmap)
- [ ] Plot: freeze/thaw events vs pothole reports (should correlate)
- [ ] Identify any data quality issues (nulls, encoding, outliers)

**Deliverable:** Know the data shape, confirm freeze-thaw signal exists, fix any obvious quality issues.

**Key files:**
- `notebooks/01_eda.ipynb`

---

## Phase 4 — Feature Engineering (60 min)
**Goal:** Build the feature matrix the model trains on.

- [ ] Write `src/features.py`
  - Aggregate 311 reports by `neighborhood` + `week` (weekly counts per issue type)
  - Join weather by date: compute rolling features:
    - `freeze_thaw_days_7d` — count of freeze/thaw days in past 7 days
    - `freeze_thaw_days_30d` — count in past 30 days
    - `snowfall_30d` — rolling 30-day snowfall sum
    - `days_since_last_freeze` — days since last freeze/thaw event
  - Add calendar features: `month`, `is_winter`, `week_of_year`
  - Add neighborhood static features: one-hot encode neighborhood name
- [ ] Output: one row per (neighborhood, week) with all features + target count
- [ ] Run notebook `notebooks/02_feature_engineering.ipynb` to verify

**Deliverable:** `data/processed/feature_matrix.csv` — ready for model training.

**Key files:**
- `src/features.py`
- `notebooks/02_feature_engineering.ipynb`

---

## Phase 5 — MVP Model (60 min)
**Goal:** Train a working XGBoost model. It doesn't need to be great yet.

- [ ] Write `src/model.py`
  - Load `data/processed/feature_matrix.csv`
  - Train/test split: train on 2018–2022, test on 2023–2024
  - Train XGBoost regressor (predict weekly report count per neighborhood)
  - Evaluate: MAE, RMSE, R²
  - Print feature importance (top 10)
  - Save model to `data/processed/model.pkl`
- [ ] Run `notebooks/03_model_training.ipynb`
- [ ] Target: R² > 0.5, MAE < 20 reports/week (adjust as needed)

**Deliverable:** Trained model saved. Feature importance plot showing freeze/thaw is #1.

**Key files:**
- `src/model.py`
- `notebooks/03_model_training.ipynb`

---

## Phase 6 — Risk Map Output (45 min)
**Goal:** Turn model predictions into a visual heat map.

- [ ] Write `src/map_output.py`
  - Load model + neighborhood boundaries GeoJSON
  - Run model on "next 4 weeks" (use current month + weather forecast or historical avg)
  - Output: risk score (0–100) per neighborhood per week
  - Generate Folium choropleth map → save as `app/risk_map.html`
- [ ] Open `app/risk_map.html` in browser — confirm it looks right

**Deliverable:** Interactive HTML map showing predicted risk by neighborhood.

**Key files:**
- `src/map_output.py`
- `app/risk_map.html`

---

## ✅ MVP COMPLETE — everything above = demo-ready

---

## Phase 7 — Refinement (time permitting)

### 7a — Add more data sources (improves accuracy)
- [ ] Add building permits feature (`permit_activity_30d` per neighborhood)
- [ ] Add MBTA bus stop density (`bus_stops_within_500m`)
- [ ] Add population density (normalize reports per 1,000 residents)
- [ ] Re-train model, compare metrics

### 7b — Improve the model
- [ ] Tune XGBoost hyperparameters (learning rate, max depth, n_estimators)
- [ ] Try predicting each issue type separately (potholes vs sidewalk vs lights)
- [ ] Add confidence intervals to predictions
- [ ] Cross-validate across neighborhoods (leave-one-neighborhood-out)

### 7c — Improve the demo UI
- [ ] Add crew deployment recommendation overlay on map
  - "Send 3 crews to Roxbury, 2 to Dorchester this week"
- [ ] Add time slider to show predicted risk by week
- [ ] Add "actual vs predicted" view for a past month (proof it works)
- [ ] Add feature importance chart as a sidebar explanation panel

### 7d — Wrap in a simple app (stretch)
- [ ] `app/app.py` — Streamlit or Flask server
- [ ] Input: select a date range → outputs updated risk map
- [ ] Deploy locally: `streamlit run app/app.py`

---

## Phase 8 — Demo Prep

- [ ] Prepare 3-slide story:
  1. **Problem** — 311 is reactive. Crews show up after residents complain.
  2. **Solution** — We predict where problems will spike before they're reported.
  3. **Evidence** — Show the map + show feature importance (freeze/thaw = #1 driver)
- [ ] Practice the live demo: open the map, point to a neighborhood, explain the risk score
- [ ] Prepare one "wow" stat: e.g. "In March 2024 our model predicted Roxbury would spike 2 weeks before 311 reports confirmed it"

---

## File Structure at Completion

```
Hackachusetts_Project/
├── IMPLEMENTATION_ROADMAP.md   ← this file
├── PROJECT_OUTLINE.md
├── requirements.txt
├── data/
│   ├── README.md
│   ├── sources/               ← 15 dataset profiles (done)
│   ├── raw/                   ← downloaded data (gitignored)
│   └── processed/             ← feature matrix + model (gitignored)
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_feature_engineering.ipynb
│   └── 03_model_training.ipynb
├── src/
│   ├── fetch_data.py
│   ├── features.py
│   ├── model.py
│   └── map_output.py
└── app/
    ├── risk_map.html          ← static output map
    └── app.py                 ← Streamlit app (stretch)
```

---

## Time Budget (rough)

| Phase | Time | Status |
|-------|------|--------|
| 1 — Environment | 30 min | ⬜ not started |
| 2 — Data fetch | 45 min | ⬜ not started |
| 3 — EDA | 45 min | ⬜ not started |
| 4 — Features | 60 min | ⬜ not started |
| 5 — Model | 60 min | ⬜ not started |
| 6 — Risk map | 45 min | ⬜ not started |
| **MVP total** | **~5.5 hours** | |
| 7 — Refinement | 60–90 min | ⬜ optional |
| 8 — Demo prep | 30 min | ⬜ not started |
