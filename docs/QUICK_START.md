# Quick Start Guide

Fast reference for running the Hackachusetts project.

---

## 🚀 Setup (First Time Only)

```bash
cd ~/Documents/Kiro/Hackachusetts_Project

# Pull latest code
git pull origin dev

# Install dependencies
pip install -r requirements.txt

# Verify setup
python src/train_xgboost.py  # Should run without errors
```

---

## 📊 Running a Workflow

### 1. Choose Your Workflow
- **Weather (Person 1):** `docs/workflows/WORKFLOW_PERSON1_WEATHER.md`
- **MBTA (Person 2):** `docs/workflows/WORKFLOW_PERSON2_MBTA.md`
- **Neighborhoods (Person 4):** `docs/workflows/WORKFLOW_PERSON4_NEIGHBORHOODS.md`

### 2. Follow Each Step

Example (Person 2 - MBTA):

```bash
# Step 1: Prepare environment
git pull origin dev
pip install -r requirements.txt

# Step 2: Download MBTA data
python src/get_mbta.py

# Step 3: Add to features
python src/merge_weather.py

# Step 4: Update model
# (Edit src/train_xgboost.py as per workflow)

# Step 5: Train & verify
python src/train_xgboost.py
# Check output for feature importance

# Commit & push
git add src/get_mbta.py src/merge_weather.py src/train_xgboost.py
git commit -m "Add MBTA feature"
git push origin dev
```

---

## 🔍 Key Commands

### Data Processing
```bash
# Download & clean 311 data
python src/prep_data.py

# Fetch weather
python src/fetch_weather.py

# Process neighborhoods
python src/get_neighborhoods.py

# Run equity analysis
python src/equity_analysis.py

# Verify neighborhoods
python src/verify_neighborhoods.py

# Merge all features
python src/merge_weather.py
```

### Model Training
```bash
# Train model & see feature importance
python src/train_xgboost.py

# Check output:
# - Test MAE: lower is better
# - Feature importance: which inputs matter most
# - Predictions saved to data/processed/predictions.csv
```

### Git Commands
```bash
# Check status
git status

# See recent commits
git log --oneline -5

# Pull latest changes
git pull origin dev

# Stage files
git add src/file.py docs/WORKFLOW_X.md

# Commit
git commit -m "Descriptive message"

# Push to dev branch
git push origin dev
```

---

## 📁 Key Directories

| Path | Contents |
|------|----------|
| `src/` | Python scripts for data processing & modeling |
| `data/raw/` | Raw downloaded data (gitignored, cached) |
| `data/processed/` | Cleaned features (gitignored) |
| `data/sources/` | Data source documentation |
| `app/` | Dashboard code (Streamlit) |
| `docs/` | Documentation & workflows |
| `docs/workflows/` | Step-by-step task guides |
| `docs/project/` | Project overview & roadmap |

---

## 📊 Data Flow

```
Raw Data (data.boston.gov)
    ↓
src/prep_data.py, src/fetch_weather.py, src/get_neighborhoods.py
    ↓
data/processed/report_counts.csv, weather_monthly.csv, neighborhoods.csv
    ↓
src/merge_weather.py, src/equity_analysis.py
    ↓
data/processed/features.csv, equity_check.csv
    ↓
src/train_xgboost.py
    ↓
data/processed/predictions.csv, feature_importance.csv
    ↓
app/dashboard.py (visualization)
```

---

## 🎯 Success Criteria

| Step | Success Looks Like |
|------|-------------------|
| Data download | Files created in `data/raw/` |
| Processing | Files created in `data/processed/` |
| Merge | `features.csv` has 12+ columns |
| Training | Model trains, MAE printed, features show importance |
| Equity | `equity_check.csv` shows distribution by neighborhood |
| Verification | All 5 checks pass in verify_neighborhoods.py |

---

## ⚠️ Common Issues

### "ModuleNotFoundError: No module named..."
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt
```

### "FileNotFoundError: data/processed/..."
```bash
# Solution: Run data processing scripts first
python src/prep_data.py
python src/fetch_weather.py
python src/get_neighborhoods.py
```

### "git push origin dev" fails
```bash
# Solution: Pull latest changes first
git pull origin dev
git push origin dev
```

### Model training is very slow
```bash
# Normal: ~30 seconds for 300K+ records
# But only one person can train at a time
# Wait your turn or check if someone else is running it
```

---

## 📞 Quick Help

- **Workflow questions:** See `docs/workflows/WORKFLOW_PERSONX_[NAME].md`
- **Project overview:** See `docs/project/PROJECT_OUTLINE.md`
- **Current blockers:** See `docs/project/HANDOFF.md`
- **Model details:** See code comments in `src/train_xgboost.py`

---

## 💾 Branching Strategy

```
main (production)
  ↑
  ├── Merge when feature complete
  └── Pull requests reviewed
  
dev (development)
  ↑
  ├← Your feature work
  ├← Automatic syncs
  └← All workflows target here
```

**Rule:** Always work on `dev`, never directly on `main`.

---

## 🚀 Next Steps

1. Pick your workflow: `docs/workflows/WORKFLOW_PERSONX_[NAME].md`
2. Follow steps 1-5
3. Push changes: `git push origin dev`
4. Done! Auto-sync will commit and push changes

**Estimated time per workflow:** 30-120 minutes depending on data size and complexity.
