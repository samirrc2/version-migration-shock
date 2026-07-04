PY ?= python3
PAIR ?= openai_nano
SUBGRID ?= pilot

.PHONY: all status pilot-mock inputs docs outcomes tempsweep figures paper capture freeze analyze render check clean clean-derived keys

all:
	SUBGRID=$(SUBGRID) CONC=$(CONC) bash run_all.sh

status:
	$(PY) status.py --subgrid $(SUBGRID) --watch

docs:
	$(PY) capture/build_docs.py --subgrid $(SUBGRID)

outcomes:
	$(PY) capture/build_outcomes.py --subgrid $(SUBGRID)

tempsweep:
	PAIR=$(PAIR) CONC=$(CONC) bash run_tempsweep.sh

figures:
	$(PY) render/figures.py

paper:
	$(PY) render/fill_manuscript.py

inputs:
	$(PY) capture/build_inputs.py --subgrid $(SUBGRID)

pilot-mock:
	PILOT_MOCK=1 $(PY) capture/orchestrator.py --pair $(PAIR) --version v_old --subgrid $(SUBGRID)
	PILOT_MOCK=1 $(PY) capture/orchestrator.py --pair $(PAIR) --version v_new --subgrid $(SUBGRID)
	$(PY) capture/freeze.py --pair $(PAIR) --version v_old
	$(PY) capture/freeze.py --pair $(PAIR) --version v_new
	$(PY) analysis/run.py --pair $(PAIR)
	$(PY) render/report.py
	$(PY) render/check_claims.py

capture:
	$(PY) capture/orchestrator.py --pair $(PAIR) --version $(VERSION) --subgrid $(SUBGRID) $(if $(CONC),--concurrency $(CONC),)

freeze:
	$(PY) capture/freeze.py --pair $(PAIR) --version $(VERSION)

analyze:
	$(PY) analysis/run.py --pair $(PAIR)

render:
	$(PY) render/report.py

check:
	$(PY) render/check_claims.py

keys:
	$(PY) capture/secrets.py

clean-derived:
	-rm -f claims.json claims_*.json PILOT_RESULTS.md results_*.md tempsweep_*.json
	-rm -f paper/manuscript_filled.md figures/*.png
	@echo "[clean-derived] removed analysis outputs; kept data/raw, inputs, outcomes"

clean: clean-derived
	-chmod -R u+w data 2>/dev/null || true
	-rm -f data/raw/*.csv data/frozen/*.json
	@echo "[clean] also removed captured model data (kept inputs/ and data/outcomes/)"
