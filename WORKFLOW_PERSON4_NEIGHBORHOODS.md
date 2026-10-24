# Workflow — Person 4: Boston Neighborhoods (Shapefile) + Equity Check

Your job, start to end: download the Boston neighborhoods data from
data.boston.gov, join it to segments or report data for equity analysis, and
ensure all neighborhoods are properly mapped.

---

## First, every time

```bash
git pull origin dev
pip install -r requirements.txt
```

---

## Step 1 — Prepare your environment

Sync your local branch with the dev branch and ensure all dependencies are installed.

```bash
git pull origin dev
pip install -r requirements.txt
```

**What this does:** Pulls the latest code and installs required packages so you're working with the current state of the project.

---

## Step 2 — Download and process Boston neighborhoods data

Create `src/get_neighborhoods.py`. This script creates Boston neighborhoods
data with coordinates and area for equity analysis.

**Source:** Manually compiled from data.boston.gov/dataset/boston-neighborhoods

Run the script:

```bash
python src/get_neighborhoods.py
```

**Output:** Creates two files:
- `data/processed/neighborhoods.csv` — neighborhoods with centroids and area
- `data/processed/neighborhoods.geojson` — polygon boundaries for mapping

**Columns in CSV:** `neighborhood, lat, lon, area_sqm`

Verify the output by checking that all Boston neighborhoods are present and centroids make sense.

---

## Step 3 — Join neighborhoods to report data for equity analysis

Create `src/equity_analysis.py` to spatially join 311 reports to neighborhoods.

This script:
1. Downloads 311 service request data (if not cached)
2. Assigns each report to its nearest neighborhood
3. Creates equity summary showing reports per neighborhood

Run the script:

```bash
python src/equity_analysis.py
```

**Output:** Creates `data/processed/equity_check.csv` showing:
- Number of reports per neighborhood
- Percentage of total reports
- Identifies high and low service areas

**Key insights from equity analysis:**
- Shows which neighborhoods receive disproportionate service requests
- Identifies underserved areas for targeted outreach
- Quantifies service delivery equity gaps

---

## Step 4 — Verify neighborhood coverage and identify gaps

Create `src/verify_neighborhoods.py` to validate data quality and coverage.

Run the verification script:

```bash
python src/verify_neighborhoods.py
```

**Review the output:**
- ✓ All expected neighborhoods found (exact and fuzzy matches)
- ✓ Equity data covers all neighborhoods
- ✓ Valid coordinates for all neighborhoods
- ✓ Area data complete
- ✓ No duplicate names, all within Boston bounds

All checks should pass. If issues appear, review and fix before proceeding.

---

## Step 5 — Integrate neighborhoods into the model's feature pipeline

Update `src/merge_weather.py` to include neighborhood metadata.

The merge_weather script now:
1. Joins weather data to 311 report counts
2. Adds MBTA bus stop counts (from Person 2 workflow)
3. **Adds neighborhood metadata: lat, lon, area_sqm**

Run the updated script:

```bash
python src/merge_weather.py
```

**Output:** Updates `data/processed/features.csv` with neighborhood metadata columns:
- `lat` — Neighborhood latitude
- `lon` — Neighborhood longitude
- `area_sqm` — Neighborhood area in square meters

**Feature file now includes:**
```
neighborhood, year, month, report_count,
avg_temp_c, total_precip_mm, total_snow_cm, max_wind_kmh,
bus_stops_near, lat, lon, area_sqm
```

This metadata enables:
- Equity analysis (identify service gaps by location)
- Geographic visualization (map reports by neighborhood)
- Area-normalized analysis (reports per square meter)

---

## Commit and push your changes

Once all steps complete successfully:

```bash
git add src/get_neighborhoods.py src/equity_analysis.py src/verify_neighborhoods.py src/merge_weather.py WORKFLOW_PERSON4_NEIGHBORHOODS.md data/processed/neighborhoods.csv data/processed/equity_check.csv
git commit -m "Add Boston neighborhoods data and equity analysis; integrate into feature pipeline"
git push origin dev
```

**Note:** `data/processed/` files are gitignored, so only source scripts and workflow are committed.

**Risk:** Spatial operations can be memory-intensive. If 311 data is very large, process in chunks.

**Next steps:** 
- Use `neighborhoods.geojson` in `app/dashboard.py` to overlay neighborhood boundaries on the map
- Add equity metrics to the dashboard showing service distribution by neighborhood
- Consider fairness-aware model adjustments based on equity analysis

