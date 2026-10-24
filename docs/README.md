# Hackachusetts Project Documentation

Complete documentation for the Boston 311 service request prediction model with equity analysis.

---

## 📋 Quick Navigation

### Project Overview
- **[PROJECT_OUTLINE.md](project/PROJECT_OUTLINE.md)** — High-level project goals, scope, and architecture
- **[IMPLEMENTATION_ROADMAP.md](project/IMPLEMENTATION_ROADMAP.md)** — Phases, milestones, and timeline
- **[HANDOFF.md](project/HANDOFF.md)** — Status summary and known issues

### Workflows (Step-by-Step Guides)
Each workflow is a complete, independent task for a team member to execute:

| Workflow | Owner | Focus | Key Output |
|----------|-------|-------|-----------|
| **[WORKFLOW_PERSON1_WEATHER.md](workflows/WORKFLOW_PERSON1_WEATHER.md)** | Person 1 | Weather data integration & proof | Feature importance chart |
| **[WORKFLOW_PERSON2_MBTA.md](workflows/WORKFLOW_PERSON2_MBTA.md)** | Person 2 | MBTA transit feature engineering | Bus stop proximity feature |
| **[WORKFLOW_PERSON4_NEIGHBORHOODS.md](workflows/WORKFLOW_PERSON4_NEIGHBORHOODS.md)** | Person 4 | Neighborhoods & equity analysis | Geographic metadata + equity metrics |

---

## 🚀 Getting Started

### For New Team Members
1. Read [PROJECT_OUTLINE.md](project/PROJECT_OUTLINE.md) for context (5 min)
2. Check [IMPLEMENTATION_ROADMAP.md](project/IMPLEMENTATION_ROADMAP.md) for current phase (5 min)
3. Find your assigned workflow above and follow it step-by-step (30-120 min depending on workflow)
4. Reference [HANDOFF.md](project/HANDOFF.md) if you hit blockers

### For Existing Contributors
- Review the workflow corresponding to your role
- Check [DEV_BRANCH_AUTO_SYNC.md](../DEV_BRANCH_AUTO_SYNC.md) for automatic syncing info
- Pull latest: `git pull origin dev`
- Follow your workflow's current step

---

## 📚 Documentation Structure

```
docs/
├── README.md (you are here)
├── project/
│   ├── PROJECT_OUTLINE.md       — What we're building and why
│   ├── IMPLEMENTATION_ROADMAP.md — How we're building it
│   └── HANDOFF.md               — Current status & blockers
└── workflows/
    ├── WORKFLOW_PERSON1_WEATHER.md        — Weather feature engineering
    ├── WORKFLOW_PERSON2_MBTA.md           — Transit feature engineering
    └── WORKFLOW_PERSON4_NEIGHBORHOODS.md  — Geographic equity analysis
```

---

## 🎯 Current Project Status

### Completed
✅ **Step 1 (Person 1):** Weather data fetched and integrated  
✅ **Step 2 (Person 2):** MBTA bus stop data processed and added to features  
✅ **Step 3-5 (Person 2):** Model trained with MBTA feature (38.9% importance)  
✅ **Step 1-5 (Person 4):** Neighborhoods mapped and equity analysis complete  

### In Progress / Next
- Dashboard integration with equity metrics
- Geographic visualizations (neighborhood boundaries)
- Model fairness improvements based on equity data
- Additional feature engineering (Person 3 placeholder)

---

## 💡 Key Concepts

### The Model
- **Input:** 311 service requests by neighborhood, month, weather
- **Output:** Predicted report counts and risk levels by neighborhood
- **Method:** XGBoost regression on engineered features
- **Success Metric:** Lower MAE (mean absolute error) with human-interpretable features

### Features
Currently using:
- **neighborhood_encoded:** Which neighborhood (categorical)
- **month:** Seasonal patterns (1-12)
- **weather:** Temperature, precipitation, snow, wind
- **bus_stops_near:** Transit accessibility (Person 2)
- **lat, lon, area_sqm:** Geographic metadata (Person 4)

### Equity Analysis
- Identifies neighborhoods with disproportionate service requests
- Compares actual vs. expected distribution
- Flags high-disparity areas for targeted investigation
- Integrates into model for fairness-aware predictions

---

## 🔧 For Developers

### Running Workflows
Each workflow consists of 5 steps:

```bash
# Step 1: Prepare environment
git pull origin dev
pip install -r requirements.txt

# Steps 2-5: Run scripts (see your workflow for details)
python src/get_[feature].py
python src/merge_weather.py
python src/train_xgboost.py

# Final: Commit and push
git add src/[files] WORKFLOW_PERSON[X]_[NAME].md
git commit -m "Description of changes"
git push origin dev
```

### Data Files
- **Raw:** `data/raw/` — Downloaded data (large, cached locally)
- **Processed:** `data/processed/` — Cleaned, engineered features (gitignored)
- **Sources:** `data/sources/` — Data source documentation

### Key Scripts
- `src/prep_data.py` — Download and clean 311 data
- `src/fetch_weather.py` — Download Boston weather
- `src/get_neighborhoods.py` — Create neighborhood geodata
- `src/equity_analysis.py` — Spatial join & equity metrics
- `src/merge_weather.py` — Combine all features
- `src/train_xgboost.py` — Train and evaluate model

---

## ⚠️ Important Notes

### Git Workflow
- Always work on `dev` branch, never `main`
- Create feature branches if needed: `git checkout -b feature/[name]`
- Auto-sync enabled — changes pushed frequently during development
- Push after each workflow step completes

### Data & Performance
- 311 data: ~306K records, ~180MB CSV (cached in `data/raw/`)
- Spatial joins can be slow (300K+ points) — patience required
- Only one person should train the model at a time (memory constraints)

### Blocked by Missing Data
- Person 3 (Street Trees) — trees.csv not yet available
  - Workflow deferred, tree_count will be 0 for now
  - Doesn't block model training, tree feature optional

---

## 📞 Contact & Questions

See [HANDOFF.md](project/HANDOFF.md) for current blockers and points of contact.

---

## 📖 Additional Resources

- **Data sources:** See `data/sources/` directory for original URLs and documentation
- **Model details:** Check src/train_xgboost.py for hyperparameters and feature importance
- **Dashboard:** `app/dashboard.py` for visualization code
- **Equity metrics:** `src/equity_analysis.py` for methodology

---

**Last updated:** 2026-10-24  
**Project phase:** Feature engineering + Model training  
**Team members:** Person 1 (Weather), Person 2 (MBTA), Person 4 (Neighborhoods)
