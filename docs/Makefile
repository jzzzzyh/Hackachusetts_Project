.PHONY: help verify fetch decode all clean test

help:
	@echo "Hackachusetts Step 1: MBTA Bus Shapes"
	@echo ""
	@echo "Available commands:"
	@echo "  make verify    - Verify installation and dependencies"
	@echo "  make fetch     - Fetch bus routes and shapes from MBTA API"
	@echo "  make decode    - Decode polylines to GeoJSON"
	@echo "  make all       - Run verify, fetch, and decode"
	@echo "  make test      - Test polyline decoding functionality"
	@echo "  make clean     - Remove generated data files"
	@echo ""
	@echo "Quick start:"
	@echo "  make all       - Complete Step 1 pipeline"

verify:
	python3 verify_installation.py

fetch:
	python3 fetch_mbta_bus_shapes.py

decode:
	python3 decode_mbta_shapes.py

all: verify fetch decode
	@echo ""
	@echo "✓ Step 1 complete!"
	@echo ""
	@echo "Generated files:"
	@echo "  - data/mbta_bus_routes.csv"
	@echo "  - data/mbta_bus_shapes.json"
	@echo "  - data/mbta_bus_shapes.geojson"

test:
	python3 test_decode_sample.py

clean:
	rm -f data/mbta_bus_routes.csv
	rm -f data/mbta_bus_shapes.json
	rm -f data/mbta_bus_shapes.geojson
	rm -f data/test_geojson.geojson
	@echo "✓ Cleaned generated data files"

.DEFAULT_GOAL := help
