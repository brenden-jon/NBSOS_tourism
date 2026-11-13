# Panama Tourism-Nature Opportunity Scan - reproducible pipeline
# Override to use your own interpreter, e.g.  make analyse PY=python3
PY ?= .venv/bin/python

.PHONY: all setup fetch analyse web clean
all: fetch analyse

## one-off environment setup (needs Python 3.11+)
setup:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

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
	$(PY) pipeline/17_feasibility.py
	$(PY) pipeline/18_flood.py
	$(PY) pipeline/19_nbs.py
	$(PY) pipeline/30_indicators.py
	$(PY) pipeline/40_classify.py
	$(PY) pipeline/50_opportunities.py
	$(PY) pipeline/52_zones.py
	$(PY) pipeline/55_narratives.py
	$(PY) pipeline/60_export.py

web:
	cd web && npm install && npm run build

clean:
	rm -rf data/processed/* web/dist
