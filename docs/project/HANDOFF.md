# Hackachusetts Project — Handoff

**Goal:** A model that predicts where Boston civic problems (potholes, sidewalk damage) will happen next, so crews get sent before people complain.

**Repo:** https://github.com/jzzzzyh/Hackachusetts_Project (branch: `dev`)
**Local path:** `C:\Users\jiappini1\Hackachusetts_Project`

---

## What the demo is
One file: `data/processed/risk_map.html`. A map of Boston. Each neighborhood is a dot. Red dot = many reports predicted next month. Green = few. Click a dot to see the name, the predicted count, and the risk level.

---

## What we built (all done)

| Step | What it does | Output |
|------|-------------|--------|
| 1 | Download + clean Boston 311 data | `data/processed/report_counts.csv` |
| 2 | Train a Random Forest model | `data/processed/predictions.csv` |
| 3 | Turn predictions into the map | `data/processed/risk_map.html` |

- **306,756 real 311 rows** from 2024 were pulled from data.boston.gov.
- Cleaned into **268 neighborhood-month counts**.
- Model predicts reports per neighborhood. Top risk: **Dorchester** (~1,370 predicted).
- Map uses a free OpenStreetMap street background — no API key needed.

## The three scripts
- `src/prep_data.py` — gets and cleans the 311 data (Step 1)
- `src/train_model.py` — trains the model, writes predictions + coordinates (Step 2)
- `src/make_map.py` — builds the map HTML (Step 3)

Run them in that order. Each one feeds the next.

---

## How to run it (one person, ~50 min)
```
git pull origin dev
pip install -r requirements.txt
python src/prep_data.py
python src/train_model.py
python src/make_map.py
```
Then open `data/processed/risk_map.html` in a browser.

## How teammates view the map
We are sharing it live with **ngrok** (a temporary public link).
1. Window 1: `cd data\processed` then `python -m http.server 8080 --bind 127.0.0.1`
2. Window 2: `ngrok http 8080`
3. Share the printed `https://...ngrok-free.app/risk_map.html` link.
Both windows must stay open or the link dies.

---

## What's left (after the halfway demo)
From `PROJECT_OUTLINE.md`, Phase 2:
- Add weather data (Open-Meteo API)
- Merge weather with 311 by date + neighborhood
- Swap Random Forest → XGBoost, retrain
- Rebuild the map with better predictions
- Build a Streamlit dashboard

**Required before the hackathon ends:** at least one live data feed that makes the model adaptive. Ideas: a weather API, scraping Facebook groups, or scraping local government / municipal meeting info. Weather is the easiest pick.

---

## Key facts
- Python 3.14
- Grid cell size: 500m
- Teammate: Anita
- Phase: 3 (Civic Action hackathon)
