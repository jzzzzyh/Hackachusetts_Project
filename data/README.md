# Data Sources Index

Each file in `sources/` documents one dataset: what it is, how to fetch it, its schema, and how we use it.

| File | Dataset | Format | Auth needed |
|------|---------|--------|-------------|
| [01_311_service_requests.md](sources/01_311_service_requests.md) | Boston 311 Reports | CSV (per year) + JSON API | None |
| [02_weather_boston.md](sources/02_weather_boston.md) | Boston Weather History | JSON API | None |
| [03_streets.md](sources/03_streets.md) | Boston Managed Streets | CSV / GeoJSON | None |
| [04_street_trees.md](sources/04_street_trees.md) | BPRD Street Trees | CSV / GeoJSON | None |
| [05_building_permits.md](sources/05_building_permits.md) | Approved Building Permits | CSV | None |
| [06_neighborhood_boundaries.md](sources/06_neighborhood_boundaries.md) | Neighborhood Boundaries | GeoJSON / CSV | None |
| [07_property_violations.md](sources/07_property_violations.md) | Building & Property Violations | CSV | None |
| [08_construction_after_hours.md](sources/08_construction_after_hours.md) | After-Hours Construction | CSV | None |
| [09_public_works_violations.md](sources/09_public_works_violations.md) | Public Works Violations | CSV | None |
| [10_mbta_routes.md](sources/10_mbta_routes.md) | MBTA Bus & Rail Routes (GTFS) | ZIP (GTFS) | None |

## Raw data files go in `data/raw/` (gitignored — too large for GitHub)
## Processed/merged files go in `data/processed/`
