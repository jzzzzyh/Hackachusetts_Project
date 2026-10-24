# 🕳️✈️ PotPilot

**Predicting Boston's potholes before they predict your suspension repair bill.**

> Every winter, Boston plays a game with its drivers. The city freezes, thaws, freezes again, and by March the streets look like a golf course designed by a vengeful snowplow. Residents dodge craters on Mass Ave, cyclists pray at every intersection, and somewhere a 311 operator sighs at report #4,000 that just says "BIG HOLE. VERY BIG."
>
> We thought: what if the city could see the potholes coming?
>
> **PotPilot** is your city's co-pilot for street repairs. It reads 10+ years of Boston's complaints, checks the weather, counts the trees, studies the bus routes, and then calmly announces: *"Turbulence ahead in Dorchester. Please send a crew."*
>
> No crystal ball. Just XGBoost and a deep personal grudge against potholes.

PotPilot predicts where Boston will need repair crews next (potholes, sidewalk damage, and other civic problems) so the city can send crews **before** reports pile up. Built for **Hackachusetts** (topic: Civic Action).

The model learns from 10+ years of Boston 311 reports, live weather, transit access, street trees, and neighborhood equity scores, then ranks every neighborhood by predicted risk for the current month.

| | |
|---|---|
| 🌐 **Live demo** | [public-nu-mauve.vercel.app](https://public-nu-mauve.vercel.app) |
| 💻 **Code** | [github.com/jzzzzyh/Hackachusetts_Project](https://github.com/jzzzzyh/Hackachusetts_Project) (work on the `dev` branch) |
| 🗺️ **Map, no setup** | [`data/processed/risk_map.html`](data/processed/risk_map.html) |

---

## Why it matters

- **Reactive repair is expensive.** Crews usually go where complaints already piled up, after cars and bikes took the damage.
- **Not every neighborhood reports equally.** Areas that file fewer 311 reports can still have bad streets. PotPilot factors in equity scores so quieter neighborhoods don't get left behind.
- **Weather is predictable; potholes follow it.** Freeze-thaw cycles are the #1 driver of pothole risk, and we can see them coming days ahead.

---

## What it does

1. **Downloads** Boston 311 service requests (2015–2026, ~300K+ records).
2. **Builds features** per neighborhood per month: recent report history, season, weather, transit stops/routes, street trees, equity score.
3. **Trains** an XGBoost model to predict how many 311 reports a neighborhood will get next month.
4. **Scores** every neighborhood and assigns a risk level (high / medium / low).
5. **Shows** the result on an interactive map and a Streamlit dashboard.

Two prediction modes:
- **Everything** — all 311 request types.
- **Potholes only** — a focused model for pothole risk (freeze-thaw driven).

---

## Results

| Mode | Test MAE | Accuracy | Avg reports/month |
|------|---------:|---------:|------------------:|
| Everything (all 311) | 214.7 | 85.6% | 1,491 |
| Potholes only | 22.3 | 61.2% | 57 |

*Accuracy = 1 − (MAE ÷ average monthly reports). The pothole model scores lower because the counts are small, which the metric punishes — not because it predicts worse. Test period: Oct 2025 – Sep 2026.*

### What drives the prediction

**Everything model** — top features by importance:

| Feature | Importance | What it means |
|---------|-----------:|---------------|
| `lag1` | 23% | Last month's reports |
| `route_count` | 15% | Bus/rail routes nearby |
| `month` | 15% | Time of year |
| `tree_count` | 10% | Street trees nearby |
| `rail_stops_near` | 8% | Rail stops within reach |
| *season, lag12, bus stops, rolling avg, equity, nbhd* | rest | — |

**Potholes model** — top features: `freeze_thaw_days` (17%), `month` (16%), `season` (11%), `past_pothole_rate` (10%), `total_snow_cm` (9%). Winter freeze-thaw cycles crack pavement, so cold-weather features dominate.

---

## Quick start

```bash
# 1. Get the code (one time)
git clone https://github.com/jzzzzyh/Hackachusetts_Project.git
cd Hackachusetts_Project
git checkout dev

# 2. Install dependencies
pip install -r requirements.txt
```

### Run the full pipeline

Run these from the project root, in order:

```bash
python src/prep_data.py        # download + clean 311 data, build report counts
python src/fetch_weather.py    # fetch Boston weather (Open-Meteo)
python src/merge_weather.py    # join weather + transit + trees into features.csv
python src/train_xgboost.py    # train both models, write predictions + importances
python src/make_map.py         # build the interactive risk_map.html
```

Outputs land in `data/processed/` (predictions, feature importances, `risk_map.html`).

### Run the dashboard

```bash
python -m streamlit run app/dashboard.py
```

Opens on `http://localhost:8501`. The sidebar toggles between the two model modes.

> **Note:** on this project's Python, use `python -m streamlit run ...` (not `streamlit`), and `pip install -r requirements.txt` with the versions as pinned.

---

## Viewing the map

The finished map is `data/processed/risk_map.html`. Double-click it to open in your browser.

**If the browser says "Access Blocked" or the map is empty**, some browsers block local HTML files from loading map tiles. Serve it with Python instead:

```bash
python -m http.server 8000 --bind 127.0.0.1 --directory data/processed
```

Then open `http://127.0.0.1:8000/risk_map.html`. Press `Ctrl+C` to stop the server.

---

## Project structure

```
Hackachusetts_Project/
├── README.md                  ← you are here
├── requirements.txt
├── src/                       ← pipeline scripts
│   ├── prep_data.py           # download + clean 311, build report counts
│   ├── fetch_weather.py       # Open-Meteo weather
│   ├── get_mbta.py            # MBTA transit stops/routes
│   ├── get_trees_live.py      # street trees (live ArcGIS)
│   ├── get_neighborhoods.py   # neighborhood geometry
│   ├── equity_analysis.py     # equity scores per neighborhood
│   ├── merge_weather.py       # join all features → features.csv
│   ├── train_xgboost.py       # train both models
│   └── make_map.py            # build risk_map.html
├── app/
│   └── dashboard.py           # Streamlit dashboard (both modes)
├── public/                    ← static site deployed to Vercel
│   ├── index.html             # landing page
│   └── risk_map.html          # map copy for the web
├── data/
│   ├── raw/                   # downloaded data (gitignored)
│   ├── processed/             # features, predictions, map (gitignored*)
│   └── sources/               # documentation for all 15 data sources
└── docs/                      # project docs + per-person workflows
```

\* `risk_map.html` is force-kept in git so judges can open the map without running the build.

---

## Data sources

All data is public. See `data/sources/` for the full profile of each (15 sources documented).

| Source | Used for | Format |
|--------|----------|--------|
| Boston 311 Requests (2015–2026) | Target + history | CSV |
| Open-Meteo | Weather, freeze-thaw | API / CSV |
| MBTA (GTFS) | Transit stops & routes | ZIP |
| Boston Neighborhoods | Geometry & equity | GeoJSON |
| Boston Street Trees (ArcGIS) | Tree feature | Live API |

---

## How the model works

```
Neighborhood + month + recent history + weather + transit + trees + equity
        │
        ▼
  XGBoost regressor
        │
        ▼
Predicted 311 reports  →  risk level (high / medium / low)
```

- **Features** come from `features.csv` (one row per neighborhood per month).
- **Two models** are trained from the same features: one for all 311 types, one for potholes only.
- Both write their predictions and feature importances to `data/processed/`.

---

## Team & workflow

All work targets the `dev` branch, never `main`. Per-person task guides live in `docs/workflows/`. An auto-sync watcher (`watch-and-sync.ps1`) pulls with rebase and pushes to `dev` so teammates stay in sync.

Contributors: Weather, MBTA transit, neighborhood equity, and live-weather integration.

---

## License & attribution

Public data from **Boston Open Data** (311, neighborhoods, street trees), **MBTA** (GTFS), and **Open-Meteo** (weather). Full citations in `data/sources/`.
