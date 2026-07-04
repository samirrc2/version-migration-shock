# Paper 2 — Code Architecture

**Version Migration as a Correlated Shock.** This document specifies the code
architecture for Paper 2, designed as a deliberate response to concrete failure
modes ("scars") observed in the Paper 1 codebase. Every design decision below is
traced to (a) the Paper 1 scar it fixes and/or (b) one of the seven planning
upgrades.

---

## 0. The one principle everything else follows from

**A hard wall between the CAPTURE layer and the ANALYSIS layer.**

| | CAPTURE | ANALYSIS |
|---|---|---|
| Talks to | live vendor APIs | frozen CSVs only |
| Determinism | impure, non-reproducible, side-effectful | pure, seeded, byte-identical on re-run |
| Perishability | **time-critical** (endpoints deprecate) | timeless (data is frozen) |
| Spend | costs money | $0 |
| Failure tolerance | must be resumable / quota-aware | must be reproducible |

In Paper 1 these were entangled (`orchestrator.py` wrote `runs.csv`; `analyze.py`
read it — fine — but robustness *captures* and robustness *analyses* were bolted
on together per amendment). For Paper 2 the wall is explicit and the perishable
side is isolated so it can run **first and alone** (Upgrade #1).

---

## 1. Directory layout

```
Paper 2/
├── PREREGISTRATION.md          # frozen day-1; robustness native, not amended (Upgrade #2)
├── ARCHITECTURE.md             # this file
├── README.md
│
├── config/
│   ├── schema.py               # ONE config schema; "condition" is the atom (fixes scar #1)
│   ├── pairs.yaml              # the v_old→v_new migration pairs (from the inventory)
│   ├── grid.yaml               # tickers / dates / sectors  (reuse Paper 1 verbatim)
│   └── models.yaml             # registry: exact snapshot strings + probe receipts
│
├── capture/                    # ── PERISHABLE / IMPURE ──────────────────────
│   ├── orchestrator.py         # refactored from P1: condition-driven, not ensemble-baked
│   ├── agent.py                # provider router (reuse P1)
│   ├── secrets.py              # reuse P1 verbatim
│   ├── probe.py                # promoted probe_models.py: stamps served-model fingerprint
│   └── freeze.py               # per-capture freeze+hash the MOMENT a v_old lands (Upgrade #1)
│
├── data/
│   ├── raw/                    # immutable runs_<pair>_<version>.csv (read-only, hashed)
│   └── frozen/                 # one freeze receipt per capture, minted on landing
│                               # (STANDALONE: no external archive; noise floor = own replicates)
│
├── analysis/                   # ── REPRODUCIBLE / PURE ──────────────────────
│   ├── metrics.py              # flip rate, conviction shift, turnover, boundary distance
│   ├── stats.py                # cluster bootstrap (reuse P1), McNemar, excess-flip CI
│   ├── baseline.py             # within-version flip rate from OWN replicates → Table 1
│   └── run.py                  # SINGLE ENTRYPOINT → emits claims.json (Upgrade #4)
│
├── render/
│   ├── tables.py               # reads claims.json ONLY
│   ├── figures.py              # reads claims.json ONLY
│   └── check_claims.py         # greps manuscript numbers, asserts vs claims.json (Upgrade #4)
│
├── paper/
│   ├── manuscript.tex          # skeleton w/ named empty slots, written day-1 (Upgrade #3)
│   ├── slots.yaml              # every result slot enumerated; unfilled slot = build failure
│   └── sections/
│       └── differentiation.tex # cross-version-vs-noise para, written now (Upgrade #3)
│
├── governance/                 # ── PARALLEL TRACK, off critical path (Upgrade #6) ──
│   └── sr11_7_mapping.md       # provision table; practitioner judgment (yours)
│
├── benchmark/                  # ── BORN AS A RELEASE (Upgrade #7) ──
│   ├── battery/                # curated items + boundary-distance labels, versioned
│   ├── DATASHEET.md
│   └── README.md
│
└── Makefile                    # capture → freeze → analyze → render → check → paper
```

---

## 2. The `condition` abstraction (fixes scar #1: amendment sprawl)

**Scar.** In Paper 1 every reviewer ask spawned a new config file
(`config_control.yaml`, `config_temp.yaml`), a new analysis script
(`control_kappa.py`, `temp_analyze.py`, `reviewer_analysis.py`), a new output dir
(`control/`, `temp_sweep/`), and a new result `.md`. Robustness was *bolted on*.

**Fix.** One atom — a **condition** — fully specifies a capture:

```yaml
# a condition is the complete recipe for one deterministic decision-generator
condition:
  model: gpt-5-nano-2025-08-07      # exact snapshot string
  temperature: 0.0                  # primary regime; subgrid conditions vary this
  seed_policy: cell_parity          # see §3
  n_replicates: 3
```

A **migration pair** is just two conditions sharing everything except `model`:

```yaml
pairs:
  - id: openai_nano
    v_old: {model: gpt-5-nano-2025-08-07}
    v_new: {model: gpt-5.4-nano}          # already frozen in Paper 1 archive
    shutdown: 2026-12-11
```

Temperature subgrid, alternative-statistic robustness, and the dose-response
secondary are **not new scripts** — they are additional conditions/columns that
flow through the *same* capture loop and the *same* `analysis/run.py`. Registering
them all in `PREREGISTRATION.md` on day one (Upgrade #2) costs foresight, not code.

---

## 3. Seed parity across versions (fixes a subtle, easy-to-miss trap)

**Paper 1's seed derivation is excellent and we reuse the SHA-256→int32 mechanism
verbatim** — but its key includes `config` and `agent_idx`:

```python
# Paper 1 (orchestrator.derive_agent_seed)
raw = f"{master}|{run_seed}|{config}|{ticker}|{date}|{agent_idx}"
```

For a *migration* measurement, the seed must be keyed on the **cell and replicate
only**, and must be **independent of the model**, so that `v_old` and `v_new`
receive *identical* seeds at the same `(ticker, date, replicate)`:

```python
# Paper 2
raw = f"{master}|{ticker}|{date}|{replicate}"     # NOT model, NOT version
seed = int(hashlib.sha256(raw.encode()).hexdigest()[:8], 16) & 0x7FFFFFFF
```

This makes the version the **only** thing that differs between the paired calls, so
any decision change is attributable to the migration, not to a different draw. This
is the code-level expression of "distinct from within-version sampling noise."

**Two regimes, both pre-registered:**
- **Primary (version isolation):** `temperature=0` + fixed cell-parity seed. Residual
  cross-version change ≈ pure version effect.
- **Noise floor (subtrahend):** within-version decision variability across seeds,
  measured from **Paper 2's own `n_replicates` captures of each version** (never an
  external archive — the paper is standalone). `analysis/baseline.py` reduces it into
  **Table 1**: how much decisions flip when nothing changes (seeds only) vs when the
  model version changes.

Primary endpoint: **excess flip rate = cross-version flip rate − within-version flip rate.**

---

## 4. `claims.json` as single source of truth (fixes scar #2: prose/table drift)

**Scar.** Paper 1's monotonicity sentence contradicted its own table and survived
three review rounds because the `.tex` prose and the computed numbers lived in
separate universes; `analyze.py` both *computed* and *rendered*, with no contract
between the numbers and the manuscript.

**Fix — a three-stage pipeline with a machine-checked contract:**

```
analysis/run.py   ──emits──▶   claims.json   ──read by──▶   render/{tables,figures}.py
                                    │                              paper/manuscript.tex (\claim{...})
                                    └──────────asserted by────────▶ render/check_claims.py
```

- `claims.json` holds **every headline number** with a stable key, value, CI, and n:
  ```json
  {"excess_flip_rate.openai_nano": {"value": 0.183, "ci": [0.15, 0.22], "n": 1200}}
  ```
- The manuscript references numbers only via `\claim{excess_flip_rate.openai_nano}`
  macros (or, minimally, plain text that `check_claims.py` greps and validates).
- `check_claims.py` fails the build if any manuscript number disagrees with
  `claims.json`, or if any `slots.yaml` slot is unfilled (Upgrade #3). **A sentence
  that contradicts its table becomes a build failure, not a referee catch.**

`make paper` runs `analyze → render → check` and refuses to produce a PDF unless
`check_claims.py` is green.

---

## 5. Proven patterns carried over (re-implemented IN this folder — standalone)

Paper 2 is a standalone submission: it references **no files outside its own
folder** except `keys.env.txt`. The patterns below were validated in prior work and
are re-implemented here from scratch — nothing is imported across folders:

- **`capture/secrets.py`**, spend-cap projection, resumable `load_done()`, per-provider
  key check — self-contained in `capture/`.
- **`capture/agent.py`** provider router (OpenAI / xAI / Gemini / Anthropic), strict-JSON
  `parse_strict`, `PILOT_MOCK` offline mode, one-client-per-provider socket reuse.
- **Prompt + schema:** `prompt_template.txt` and the `{direction, conviction, rationale}`
  STRICT-JSON contract live in this folder.
- **Grid:** the 100-ticker × 12-date × 11-sector grid is enumerated in `config/grid.yaml`
  (this folder), so strata tables are internally consistent.
- **`analysis/stats.py` cluster-bootstrap-over-tickers** (seed 42, 2000 draws,
  percentile CI) for the excess-flip-rate CI.
- **Immutability discipline:** read-only, SHA-256-stamped raw CSVs + freeze receipts
  (`capture/freeze.py`) for byte-identical re-analysis.

---

## 6. What is NEW in `analysis/metrics.py`

The DV changes from agreement (κ) to cross-version change. New, all paired per cell:

- **Decision flip:** `direction(v_new) != direction(v_old)` at matched `(cell, replicate)`.
- **Excess flip rate:** flip rate minus the within-version baseline (§3). **Primary.**
- **Conviction shift:** signed `conviction(v_new) − conviction(v_old)`.
- **Implied turnover:** map `BUY/HOLD/SELL → +1/0/−1`; turnover `= Σ|pos_new − pos_old| / (2N)`.
- **Boundary-distance dose-response** (pre-registered secondary, Upgrade #2): do flips
  concentrate in low-conviction / near-boundary cells? Structure, not just magnitude.
- **McNemar paired test** on the flip contingency — the flip-rate analogue of Paper 1's
  α/AC1 "is the effect robust to the statistic" column.
- **Per-stratum tables:** sector × regime/date, via the reused grid.

---

## 7. Governance & benchmark run in parallel (Upgrades #6, #7)

Both live in their own directories with **no dependency on the numbers**, so they
never sit on the critical path:

- `governance/sr11_7_mapping.md` — a provision-by-provision table tagging which
  SR 11-7 clauses presuppose the institution controls model change/timing. The
  scaffold (pulled provision text + candidate tags) can be machine-prepared; the
  Market-Risk judgment is authored by you.
- `benchmark/` — the parallel-run battery is **built as a release from day one**:
  curated items + boundary-distance labels, versioned, with a `DATASHEET.md`. It is
  framed in the paper as the monitoring instrument the governance section proposes,
  shipped as working code — the durable, citable contribution after the specific
  version pairs age out.

---

## 8. Build targets (`Makefile`)

```
make capture PAIR=openai_nano VERSION=v_old   # perishable; run NOW, resumable, quota-aware
make freeze  PAIR=openai_nano VERSION=v_old   # hash + lock the moment it lands
make analyze                                  # pure; emits claims.json ($0, deterministic)
make render                                   # tables + figures from claims.json
make check                                    # check_claims.py: drift & unfilled slots → fail
make paper                                    # analyze→render→check→PDF (blocks if check red)
```

`capture` is the only target that spends money or depends on wall-clock/endpoints.
Everything downstream of `freeze` is pure and re-runnable forever.

---

## 9. Critical-path summary

1. **This week (perishable):** `config/pairs.yaml` + `models.yaml` from the inventory →
   minimal freeze of `PREREGISTRATION.md` → `make capture VERSION=v_old` for the
   expiring endpoints (Gemini 2.5-flash first, dies Oct 16; then OpenAI nano/4.1-nano).
2. **Same capture, no extra cost:** the within-version noise floor (Table 1) comes
   from the `n_replicates` already collected per version — no separate run.
3. **Parallel, un-gated:** paper skeleton + differentiation section; `check_claims.py`
   harness; governance mapping; benchmark datasheet.
4. **When v_new confirmed:** pair, analyze, render, check, paper.
5. **xAI:** monitor for grok-4.5 public GA; grok-4.3 already frozen in Paper 1.
```
