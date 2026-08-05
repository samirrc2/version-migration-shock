PY ?= python3
PAIR ?= openai_nano
SUBGRID ?= pilot
# Repository root (parent of this Makefile's directory)
ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)

.PHONY: all status pilot-mock inputs docs outcomes tempsweep capture freeze analyze render check clean clean-derived keys

all:
	cd $(ROOT) && SUBGRID=$(SUBGRID) CONC=$(CONC) bash code/run_all.sh

status:
	cd $(ROOT) && $(PY) code/status.py --subgrid $(SUBGRID) --watch

docs:
	cd $(ROOT) && $(PY) code/capture/build_docs.py --subgrid $(SUBGRID)

outcomes:
	cd $(ROOT) && $(PY) code/capture/build_outcomes.py --subgrid $(SUBGRID)

tempsweep:
	cd $(ROOT) && PAIR=$(PAIR) CONC=$(CONC) bash code/run_tempsweep.sh

inputs:
	cd $(ROOT) && $(PY) code/capture/build_inputs.py --subgrid $(SUBGRID)

pilot-mock:
	cd $(ROOT) && PILOT_MOCK=1 $(PY) code/capture/orchestrator.py --pair $(PAIR) --version v_old --subgrid $(SUBGRID)
	cd $(ROOT) && PILOT_MOCK=1 $(PY) code/capture/orchestrator.py --pair $(PAIR) --version v_new --subgrid $(SUBGRID)
	cd $(ROOT) && $(PY) code/capture/freeze.py --pair $(PAIR) --version v_old
	cd $(ROOT) && $(PY) code/capture/freeze.py --pair $(PAIR) --version v_new
	cd $(ROOT) && $(PY) code/analysis/run.py --pair $(PAIR)
	cd $(ROOT) && $(PY) code/render/report.py
	cd $(ROOT) && $(PY) code/render/check_claims.py

capture:
	cd $(ROOT) && $(PY) code/capture/orchestrator.py --pair $(PAIR) --version $(VERSION) --subgrid $(SUBGRID) $(if $(CONC),--concurrency $(CONC),)

freeze:
	cd $(ROOT) && $(PY) code/capture/freeze.py --pair $(PAIR) --version $(VERSION)

analyze:
	cd $(ROOT) && $(PY) code/analysis/run.py --pair $(PAIR)

render:
	cd $(ROOT) && $(PY) code/render/report.py

check:
	cd $(ROOT) && $(PY) code/render/check_claims.py

keys:
	cd $(ROOT) && $(PY) code/capture/secrets.py

clean-derived:
	cd $(ROOT) && rm -f results/claims.json results/claims_*.json results/PILOT_RESULTS.md results/results_*.md results/tempsweep_*.json
	cd $(ROOT) && rm -f claims.json claims_*.json PILOT_RESULTS.md results_*.md tempsweep_*.json
	@echo "[clean-derived] removed analysis outputs under results/; kept data/raw, outcomes"

clean: clean-derived
	cd $(ROOT) && chmod -R u+w data 2>/dev/null || true
	cd $(ROOT) && rm -f data/raw/*.csv data/frozen/*.json
	@echo "[clean] also removed captured model data (kept inputs/ and data/outcomes/)"
