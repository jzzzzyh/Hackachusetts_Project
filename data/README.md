# Data Sources Index

Each file in `sources/` documents one dataset: what it is, how to fetch it, its schema, and how we use it.

### 🟢 Easy — direct download, no auth

| File | Dataset | Format |
|------|---------|--------|
| [01_311_service_requests.md](sources/01_311_service_requests.md) | Boston 311 Reports | CSV + JSON API |
| [02_weather_boston.md](sources/02_weather_boston.md) | Boston Weather History | JSON API |
| [03_streets.md](sources/03_streets.md) | Boston Managed Streets | CSV / GeoJSON |
| [04_street_trees.md](sources/04_street_trees.md) | BPRD Street Trees | CSV / GeoJSON |
| [05_building_permits.md](sources/05_building_permits.md) | Approved Building Permits | CSV |
| [06_neighborhood_boundaries.md](sources/06_neighborhood_boundaries.md) | Neighborhood Boundaries | GeoJSON |
| [07_property_violations.md](sources/07_property_violations.md) | Building & Property Violations | CSV |
| [08_construction_after_hours.md](sources/08_construction_after_hours.md) | After-Hours Construction | CSV |
| [09_public_works_violations.md](sources/09_public_works_violations.md) | Public Works Violations | CSV |
| [10_mbta_routes.md](sources/10_mbta_routes.md) | MBTA Bus & Rail Routes (GTFS) | ZIP |

### 🟡 Medium — needs some wrangling

| File | Dataset | Format |
|------|---------|--------|
| [11_neighborhood_age.md](sources/11_neighborhood_age.md) | Neighborhood Age (Property Assessment `YR_BUILT`) | CSV |
| [12_water_sewer_mains.md](sources/12_water_sewer_mains.md) | Water & Sewer Main Age (BWSC) | GeoJSON / SHP |
| [13_traffic_volume.md](sources/13_traffic_volume.md) | Traffic Volume Counts / AADT (MassDOT) | GeoJSON |
| [14_census_population.md](sources/14_census_population.md) | Census Population Density | CSV |
| [15_pavement_condition.md](sources/15_pavement_condition.md) | Pavement Condition Index / PSI (MassDOT) | GeoJSON |

## Raw data files go in `data/raw/` (gitignored — too large for GitHub)
## Processed/merged files go in `data/processed/`
