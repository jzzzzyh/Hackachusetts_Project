# Hackachusetts: Boston 311 Service Request Prediction with Equity Analysis

Predictive model for Boston 311 service requests using XGBoost, with geographic equity analysis to identify service delivery disparities across neighborhoods.

---

## 📖 Documentation (Start Here!)

### Quick References
- **[QUICK_START.md](docs/QUICK_START.md)** — Fast setup and common commands (5 min read)
- **[docs/README.md](docs/README.md)** — Full documentation index and navigation (10 min read)

### Project Docs
- **[docs/project/PROJECT_OUTLINE.md](docs/project/PROJECT_OUTLINE.md)** — Goals, scope, architecture
- **[docs/project/IMPLEMENTATION_ROADMAP.md](docs/project/IMPLEMENTATION_ROADMAP.md)** — Phases, timeline, milestones
- **[docs/project/HANDOFF.md](docs/project/HANDOFF.md)** — Current status and blockers

### Step-by-Step Workflows (Pick One)
- **[docs/workflows/WORKFLOW_PERSON1_WEATHER.md](docs/workflows/WORKFLOW_PERSON1_WEATHER.md)** — Weather feature engineering (5 steps)
- **[docs/workflows/WORKFLOW_PERSON2_MBTA.md](docs/workflows/WORKFLOW_PERSON2_MBTA.md)** — MBTA transit features (5 steps)
- **[docs/workflows/WORKFLOW_PERSON4_NEIGHBORHOODS.md](docs/workflows/WORKFLOW_PERSON4_NEIGHBORHOODS.md)** — Geographic equity analysis (5 steps)

---

## 🎯 Quick Overview

### What This Project Does
1. **Downloads** 311 service request data from Boston (306K records)
2. **Engineers** features: weather, transit accessibility, neighborhood metadata
3. **Trains** XGBoost model to predict monthly report counts per neighborhood
4. **Analyzes** equity: identifies neighborhoods with disproportionate service requests
5. **Visualizes** results on interactive dashboard with geographic context

### Current Status
✅ Weather feature integrated (31% importance)  
✅ MBTA transit feature added (39% importance)  
✅ 28 Boston neighborhoods mapped with equity metrics  
✅ Model trained: MAE ~123 reports, geographic data included  
⏳ Dashboard integration in progress  

### Key Results
| Metric | Value |
|--------|-------|
| Model Test MAE | 123.4 reports |
| Top Feature | Bus stops near (39%) |
| Top Request Area | Dorchester (13.5% of all reports) |
| Lowest Service Area | Chestnut Hill (0.03% of reports) |
| Geographic Coverage | 28 neighborhoods, 305K+ reports assigned |

---

## 🚀 Getting Started

### For New Team Members
```bash
# 1. Clone and setup (one time)
cd ~/Documents/Kiro/Hackachusetts_Project
git pull origin dev
pip install -r requirements.txt

# 2. Pick a workflow from docs/workflows/
# 3. Follow the 5 steps in your workflow
# 4. Push changes when done
```

### For Contributors
1. Read [QUICK_START.md](docs/QUICK_START.md) (5 minutes)
2. Choose your workflow from above
3. Follow steps 1-5 (30-120 min)
4. Commit and push

---

## 📁 Project Structure

```
Hackachusetts_Project/
├── README.md (you are here)
├── docs/
│   ├── README.md              ← Full documentation index
│   ├── QUICK_START.md         ← Fast reference
│   ├── project/
│   │   ├── PROJECT_OUTLINE.md
│   │   ├── IMPLEMENTATION_ROADMAP.md
│   │   └── HANDOFF.md
│   └── workflows/
│       ├── WORKFLOW_PERSON1_WEATHER.md
│       ├── WORKFLOW_PERSON2_MBTA.md
│       └── WORKFLOW_PERSON4_NEIGHBORHOODS.md
├── src/                        ← Python scripts
│   ├── prep_data.py           # Download 311 data
│   ├── fetch_weather.py       # Get weather data
│   ├── get_neighborhoods.py   # Create geodata
│   ├── equity_analysis.py     # Spatial join & metrics
│   ├── merge_weather.py       # Combine features
│   └── train_xgboost.py       # Train model
├── app/
│   └── dashboard.py           # Streamlit visualization
├── data/
│   ├── raw/                   # Downloaded data (gitignored)
│   ├── processed/             # Features (gitignored)
│   └── sources/               # Data source docs
└── requirements.txt           # Python dependencies
```

---

## 🔄 Workflow Overview

Each workflow is independent and targets the `dev` branch:

| Workflow | Owner | Focus | Time | Status |
|----------|-------|-------|------|--------|
| **PERSON 1** | Weather Team | Feature importance proof | 45 min | ✅ Complete |
| **PERSON 2** | Transit Team | MBTA feature engineering | 90 min | ✅ Complete |
| **PERSON 3** | Trees Team | Street tree feature | TBD | ⏳ Deferred |
| **PERSON 4** | Equity Team | Geographic analysis | 120 min | ✅ Complete |

---

## 💡 Key Concepts

### The Model
```
Input: Neighborhood + Month + Weather + Transit + Area
  ↓
XGBoost Regressor (300 estimators, depth 4)
  ↓
Output: Predicted 311 reports + Risk level (high/med/low)
  ↓
Success: Low MAE + Interpretable features + Equity-aware
```

### Features Used
- `neighborhood` — Encoded ID (categorical)
- `month` — 1-12 (seasonal patterns)
- `avg_temp_c` — Temperature (weather)
- `total_precip_mm` — Precipitation
- `total_snow_cm` — Snow
- `max_wind_kmh` — Wind speed
- `bus_stops_near` — Transit accessibility (0.5km radius)
- `lat, lon` — Geographic coordinates
- `area_sqm` — Neighborhood area

### Equity Analysis
Identifies service delivery disparities:
```
High Disparity:  Top 3 neighborhoods → 35% of all reports
Low Disparity:   Bottom 5 neighborhoods → 5% of all reports
Gap:             450x difference between max and min
```

---

## 🔧 Quick Commands

```bash
# Setup
git pull origin dev && pip install -r requirements.txt

# Run a workflow step (example: Person 2, Step 2)
python src/get_mbta.py

# Merge features
python src/merge_weather.py

# Train model
python src/train_xgboost.py

# Push changes
git add src/file.py docs/WORKFLOW_X.md
git commit -m "Description"
git push origin dev
```

---

## 📊 Data Sources

All data is public and downloaded automatically:

| Source | Description | Size | Format |
|--------|-------------|------|--------|
| **311 Requests** | Boston service requests 2024 | 180 MB | CSV |
| **Weather** | Boston climate data 2024 | <1 MB | CSV |
| **MBTA** | Transit stops & routes | <1 MB | ZIP (GTFS) |
| **Neighborhoods** | Boston geographic boundaries | <1 MB | Shapefile/GeoJSON |

See `data/sources/` for original URLs and documentation.

---

## ✅ Verification Checklist

After running each workflow:

- [ ] All 5 steps completed
- [ ] Output files created in `data/processed/`
- [ ] No errors in model training
- [ ] Feature importance makes sense
- [ ] Commit message describes changes
- [ ] Changes pushed to `dev` branch
- [ ] Auto-sync detected and committed

---

## 🚀 Next Steps

### For New Contributors
1. Read [QUICK_START.md](docs/QUICK_START.md)
2. Choose a workflow from `docs/workflows/`
3. Follow steps 1-5 in your workflow
4. Push changes
5. Done!

### For Project Leads
1. Review [IMPLEMENTATION_ROADMAP.md](docs/project/IMPLEMENTATION_ROADMAP.md)
2. Check [HANDOFF.md](docs/project/HANDOFF.md) for blockers
3. Coordinate with team members on shared workflows
4. Monitor `dev` branch for auto-synced changes

---

## 📞 Support

| Question | Answer |
|----------|--------|
| How do I start? | Read [QUICK_START.md](docs/QUICK_START.md) |
| What's my task? | Pick a workflow from `docs/workflows/` |
| I'm stuck | Check [HANDOFF.md](docs/project/HANDOFF.md) or workflow FAQ |
| How's the project going? | See [IMPLEMENTATION_ROADMAP.md](docs/project/IMPLEMENTATION_ROADMAP.md) |
| Model questions? | See `src/train_xgboost.py` code comments |

---

## 📈 Results Summary

### Model Performance
- **Test MAE:** 123.4 reports (prediction error)
- **Feature Importance:** Top 3 are neighborhood (34%), bus stops (39%), temperature (12%)
- **Predictions:** 23 neighborhoods with risk levels and predicted volumes

### Equity Findings
- **Disparity Ratio:** 450:1 (Dorchester to Chestnut Hill)
- **Underserved:** West End (410 reports), Waterfront (3K reports)
- **Overserved:** Dorchester (41K reports), South End (35K reports)

### Geographic Coverage
- **Neighborhoods:** 28 with complete metadata
- **Reports Mapped:** 305,523 / 306,756 (99.6%)
- **Coordinates:** All neighborhoods have lat/lon and area

---

## 🤝 Team

**Contributors:** Person 1 (Weather), Person 2 (MBTA), Person 4 (Neighborhoods)  
**Auto-sync:** Enabled (commits pushed frequently during development)  
**Workflow:** All work targets `dev` branch, never `main`  

---

## 📝 License & Attribution

This project uses public data from:
- **Boston Open Data:** 311 Requests, Neighborhoods, Street Trees
- **MBTA:** Transit data (GTFS)
- **Open-Meteo:** Weather data

See `data/sources/` for complete citations.

---

## 🎓 Learning Resources

- **XGBoost Model:** See `src/train_xgboost.py` for hyperparameters and tuning
- **Equity Analysis:** See `src/equity_analysis.py` for methodology
- **Geographic Data:** See `src/get_neighborhoods.py` for GIS operations
- **Feature Engineering:** See all `src/get_*.py` files for examples

---

**Last Updated:** 2026-10-24  
**Project Phase:** Feature Engineering + Model Training  
**Status:** 4 of 5 workflows complete, dashboard integration next
