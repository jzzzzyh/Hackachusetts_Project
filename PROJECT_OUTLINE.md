# Civic Issue Predictor — Hackachusetts Project Outline

## Problem
Cities get flooded with 311 reports (potholes, sanitation, streetlights, etc.).
High volume makes it hard to:
- Spot patterns
- Prioritize repairs
- Communicate progress to residents

## Our Solution
A **predictive model** that forecasts where and when civic issues will spike,
so cities can allocate crews and resources before problems compound.

---

## Data Sources

Full dataset profiles with fetch code and schemas are in [`data/sources/`](data/sources/).

### 🟢 Easy — free, direct download, no auth

| Dataset | What it adds | Source | Profile |
|---------|-------------|--------|---------|
| Boston 311 Reports (2011–2026) | Core training data — potholes, sidewalk, lights | [data.boston.gov](https://data.boston.gov/dataset/311-service-requests) | [01](data/sources/01_311_service_requests.md) |
| Boston Historical Weather | Freeze/thaw cycles = #1 pothole driver | [Open-Meteo API](https://open-meteo.com) (free) | [02](data/sources/02_weather_boston.md) |
| Boston Managed Streets | Road type, surface, functional class | [data.boston.gov](https://data.boston.gov/dataset/city-of-boston-managed-streets) | [03](data/sources/03_streets.md) |
| BPRD Street Trees | Root damage = sidewalk heaving | [data.boston.gov](https://data.boston.gov/dataset/bprd-trees) | [04](data/sources/04_street_trees.md) |
| Approved Building Permits | Construction traffic damages roads | [data.boston.gov](https://data.boston.gov/dataset/approved-building-permits) | [05](data/sources/05_building_permits.md) |
| Neighborhood Boundaries | Polygon shapes for grid mapping | [data.boston.gov](https://data.boston.gov/dataset/bpda-neighborhood-boundaries) | [06](data/sources/06_neighborhood_boundaries.md) |
| Building & Property Violations | Neighborhood disinvestment proxy | [data.boston.gov](https://data.boston.gov/dataset/building-and-property-violations1) | [07](data/sources/07_property_violations.md) |
| After-Hours Construction | Heavy construction = road stress | [data.boston.gov](https://data.boston.gov/dataset/after-hours-construction) | [08](data/sources/08_construction_after_hours.md) |
| Public Works Violations | Unpermitted street cuts weaken pavement | [data.boston.gov](https://data.boston.gov/dataset/public-works-violations) | [09](data/sources/09_public_works_violations.md) |
| MBTA Bus & Rail Routes (GTFS) | Bus routes = heaviest road wear | [mbta.com/developers](https://cdn.mbta.com/MBTA_GTFS.zip) | [10](data/sources/10_mbta_routes.md) |

### 🟡 Medium — worth adding if time allows

| Dataset | What it adds | Source |
|---------|-------------|--------|
| Boston neighborhood age | Older infrastructure fails more | MassGIS building footprints (year built) |
| Water/sewer main age | BWSC potholes from pipe breaks | Boston Water & Sewer Commission |
| Traffic volume counts | High-traffic streets degrade faster | MassDOT traffic count database |
| Census block density | More people = more reports filed | US Census ACS |
| Road pavement condition index | Current rating per segment | MassDOT Pavement Management System |

### 🔵 Stretch — mention in demo slides

| Dataset | What it adds | Source |
|---------|-------------|--------|
| Utility dig permits | Street cuts weaken pavement | Dig Safe |
| Property tax assessments | Neighborhood investment proxy | data.boston.gov |
| Bike lane locations | Road surface change signal | data.boston.gov |
| School locations | Pedestrian sidewalk traffic | data.boston.gov |

---

## Predictive Features (model inputs)

| Feature | Why it matters |
|---|---|
| Days since last freeze/thaw | Freeze-thaw cracks pavement |
| Total snowfall this season | Snow plows damage roads |
| Road age (years) | Older roads fail more |
| Days since last repair | Regression to baseline damage |
| Neighborhood density | More foot/car traffic = more wear |
| Month | Seasonal patterns in report volume |
| Prior 30-day report count (same type, same area) | Clustering effect |

---

## Model

**Type:** Gradient Boosted Trees (XGBoost / LightGBM)
- Predicts: expected number of reports per grid cell per week
- Output: risk score map by neighborhood / street segment

### Why not correlation analysis?

| Approach | What it tells you | Good for prediction? |
|---|---|---|
| Correlation | "Freeze days and potholes are linked" | No — describes, doesn't predict |
| Linear regression | Predicts a single number | Weak — misses feature interactions |
| **XGBoost (chosen)** | Predicts + ranks feature importance | Yes — handles interactions and mixed data types |

Correlation is a supporting tool (good for demo slides), not the core predictor.
XGBoost wins because:
1. Features **interact** — old road + freeze + high traffic together are worse than any one alone
2. Handles mixed types (dates, numbers, categorical)
3. Outputs **feature importance** — e.g. "freeze/thaw accounts for 43% of predictions"
4. Trains fast on a laptop, no GPU needed

If time is short, **Random Forest** is a near-equivalent fallback that's simpler to explain.

**Validation:**
- Train on 2018–2022 Boston 311 data
- Test on 2023–2024
- Metric: MAE on report count, precision/recall on "high spike" weeks

---

## Output / Product

1. **Risk Heat Map** — interactive map showing predicted high-risk zones next 30 days
2. **Resource Allocation Recommendation** — suggested crew deployment by zone
3. **Pattern Dashboard** — top recurring issue types by neighborhood + trend lines
4. **(Stretch) Resident Alert** — notify residents when their street is flagged

---

## File Structure

```
Hackachusetts_Project/
├── PROJECT_OUTLINE.md          ← this file
├── data/
│   ├── raw/                    ← downloaded CSVs (311 reports, weather, GIS)
│   └── processed/              ← cleaned, merged datasets
├── notebooks/
│   ├── 01_eda.ipynb            ← explore the 311 data
│   ├── 02_feature_engineering.ipynb
│   └── 03_model_training.ipynb
├── src/
│   ├── fetch_data.py           ← download + cache data sources
│   ├── features.py             ← build feature matrix
│   ├── model.py                ← train + evaluate model
│   └── map_output.py           ← generate risk heat map
├── app/
│   ├── index.html              ← front-end dashboard
│   └── app.py                  ← Flask/FastAPI server (optional)
└── requirements.txt
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Data wrangling | Python, pandas, geopandas |
| Model | XGBoost / LightGBM |
| Maps | Folium / Leaflet.js |
| Weather API | Open-Meteo (free, no key) |
| Boston data | CityOfBoston/OpenContext GitHub |
| Front end | HTML + JS or Streamlit |

---

## Hackathon Milestones

1. [ ] Pull Boston 311 CSV from OpenContext repo
2. [ ] Pull weather data for Boston (2018–2024) via Open-Meteo
3. [ ] Merge datasets by date + neighborhood
4. [ ] Build feature matrix
5. [ ] Train baseline model, check accuracy
6. [ ] Generate risk heat map for next 30 days
7. [ ] Build simple dashboard to display map + recommendations
8. [ ] (Stretch) Add resident alert / equity lens

---

## Key Question We Answer
> "Where should Boston send repair crews next week to fix the most problems
> before residents even have to report them?"
