# Panama Tourism-Nature Opportunity Scan - reproducible pipeline
PY := .venv/bin/python

.PHONY: all fetch analyse web clean
all: fetch analyse

fetch:
	$(PY) pipeline/10_fetch_national.py
	$(PY) pipeline/11_fetch_osm.py
	$(PY) pipeline/12_gov_strategy.py

analyse:
	$(PY) pipeline/20_grid.py
	$(PY) pipeline/13_rasters.py
	$(PY) pipeline/14_gbif.py
	$(PY) pipeline/15_access.py
	$(PY) pipeline/16_vectors.py
	$(PY) pipeline/30_indicators.py
	$(PY) pipeline/40_classify.py
	$(PY) pipeline/50_opportunities.py
	$(PY) pipeline/55_narratives.py
	$(PY) pipeline/60_export.py

web:
	cd web && npm install && npm run build

clean:
	rm -rf data/processed/* web/dist
