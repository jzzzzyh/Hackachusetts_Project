# Hackachusetts Road Condition Predictor

## Goal

Predict which Boston road segments will develop potholes or sidewalk damage in the next 90 days.

## Folder Structure

- `data/`      → raw datasets
- `scripts/`   → data cleaning and model scripts  
- `output/`    → predictions and results
- `notebooks/` → analysis and exploration

## Data Sources

- **BPRD Trees** — Boston street trees inventory
- **Boston Neighborhood Boundaries** — 26 neighborhoods
- **311 Service Requests** — potholes + sidewalk damage (to be added)
- **MBTA Bus Routes** — traffic and transit patterns
- **NOAA Weather** — freeze-thaw cycles, rainfall patterns (to be added)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run data scripts
cd scripts/
python3 verify_installation.py
python3 fetch_mbta_bus_shapes.py
python3 decode_mbta_shapes.py
python3 load_trees_data.py
python3 clean_neighborhoods.py
```

## Status

- ✓ Step 1: Data sources ready (MBTA, neighborhoods, trees)
- → Step 2: Spatial feature engineering
- → Step 3: Model building
- → Step 4: Predictions & equity analysis
