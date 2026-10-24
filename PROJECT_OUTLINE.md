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

### Boston 311 Reports
- Report type (pothole, broken light, sidewalk damage, etc.)
- Location (lat/lon, neighborhood, street)
- Date opened / date closed
- Status / resolution time
- Source: [CityOfBoston/OpenContext](https://github.com/CityOfBoston/OpenContext)

### Weather
- Temperature (freeze/thaw cycles → pothole formation)
- Precipitation (rain, snow, ice)
- Seasonal patterns
- Source: NOAA / Open-Meteo API (free)

### Infrastructure Age
- Road last repaved / sidewalk last replaced
- Building age by neighborhood
- Source: Boston city GIS / MassGIS

### Calendar / Time Features
- Month, season
- Day of week (reports spike after weekends)
- Years since last renovation per block

### Socioeconomic / Neighborhood Context
- Population density
- Neighborhood equity index
- Source: US Census ACS

### Traffic / Usage
- High-traffic roads wear faster
- Source: MassDOT traffic counts

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
