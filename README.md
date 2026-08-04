# Version Migration as a Correlated Shock

Computational artifact for the IEEE Access article:

**Version Migration as a Correlated Shock: Model Updates as an Unmanaged Risk Channel in LLM-Based Financial Systems**

### Paper summary

Financial institutions deploying LLM agents inherit a risk absent from classical model governance: when the vendor updates the model, every deployment pinned to that version shifts behavior at once, involuntarily, and in a correlated direction. This article runs an identical, deterministic decision pipeline across **two real vendor migrations** on a credit-health classification task (SAFE / WATCH / DISTRESS, graded against Altman *Z''* bands) over **100 companies × 12 as-of dates × 3 replicates per version** (14,400 model calls), and measures the decision discontinuity induced purely by the update, net of within-version sampling noise.

**Main findings:**

- Both migrations produce a large, highly significant shock, but of **opposite character**. OpenAI (`gpt-5-nano-2025-08-07`→`gpt-5.4-nano`) flips **0.112** of assessments above the noise floor (95% CI [0.077, 0.150]) as genuine per-company reconsideration toward DISTRESS. Gemini (`gemini-2.5-flash`→`gemini-3.5-flash`) flips **0.381** (95% CI [0.303, 0.458]) as a wholesale distributional shift toward SAFE.
- The result survives the conservative max-of-both-versions noise floor (OpenAI 0.097 [0.06, 0.13]; Gemini 0.372 [0.30, 0.45]).
- Neither migration improves class-balanced accuracy; the Gemini shift **degrades** it toward chance (macro-F1 0.46→0.32). Both incumbents clear the 0.36 majority-class baseline (models are competent).
- The character of a migration shock does not generalize across vendors — an idiosyncratic, synchronized channel current model-risk guidance does not address (SR 26-2 places generative AI out of scope).

This repository is the frozen dataset and deterministic analysis pipeline that regenerates those numerical results, tables, and figures.

---

## 1. Artifact Identification

| Field | Value |
|-------|--------|
| **Article title** | Version Migration as a Correlated Shock: Model Updates as an Unmanaged Risk Channel in LLM-Based Financial Systems |
| **Authors** | Samir Chincholikar, Robin Chawla |
| **Affiliations** | Independent researchers |
| **Code repository** | https://github.com/samirrc2/version-migration-shock |
| **Persistent DOI** | Code Ocean capsule / Zenodo deposit pending (public DOI to be inserted here when minted). Until then, use this GitHub repository. |
| **Contact** | Samir Chincholikar: samir.chincholikar@gmail.com; Robin Chawla: robin.chawla.cse14@iitbhu.ac.in |
| **ORCID** | Samir Chincholikar: https://orcid.org/0009-0007-2779-3492; Robin Chawla: https://orcid.org/0009-0007-2807-3948 |

### Abstract and role of the artifact

This artifact accompanies a **pre-registered** study of vendor version-migration decision instability on a credit-health screening task. The confirmatory experiment comprises **14,400 independent model calls** (100 companies × 12 dates × 3 replicates × 2 versions × 2 migration pairs) using models from OpenAI and Google.

The artifact enables independent reproduction of the article's computational results. Specifically, it provides:

1. The frozen confirmatory dataset (`data/raw/runs_<pair>_v_{old,new}.csv`, each row carrying the model's raw response) with SHA-256 receipts (`data/frozen/`, aggregated in `DATA_MANIFEST.md`), the Altman ground-truth labels (`data/outcomes/ground_truth.json`), the reported-financials context (`docs/*.json`), and the study configuration (`config/`).
2. A deterministic analysis pipeline that regenerates the excess-flip-rate primary endpoint with cluster-bootstrap CIs, the prevalence/churn decomposition, three chance-corrected agreement statistics, class-balanced accuracy against the Altman ground truth, and the noise-floor and temperature sensitivities, into `claims_<pair>.json` and `results_<pair>.md`.
3. Pre-registration, its cryptographic freeze receipt, and the amendments log.
4. The capture and monitoring harness (the pre-migration parallel-run metric).

**Default workflow (this README):** regenerate all analysis outputs from the frozen dataset. This path requires **no API keys** and incurs **no inference cost**. Re-collecting the 14,400 API calls is optional, incurs cost, and is **not required** to verify the numerical claims in the article.

---

## Code Ocean

A [Code Ocean](https://codeocean.com/) compute capsule for this artifact is prepared for submission; a persistent DOI will be assigned after Code Ocean's reproducibility verification.

| Status | Detail |
|--------|--------|
| Capsule | Prepared (keys-free Reproducible Run via `run` → `reproduce.sh`) |
| Environment | `environment/Dockerfile` (Python 3.12 + PyYAML) |
| Public link / DOI | Not yet issued — will be added to this README and the manuscript when available |
| Until then | Reproduce from this GitHub repository (`bash reproduce.sh`) |

The frozen dataset is committed to the repository, so the capsule reproduces every number with **no external download, no API keys, and no inference cost**. After publication, replace the **Persistent DOI** placeholder in Section 1 with the minted DOI.

---

## 2. Dependencies and Requirements

### Hardware

| Resource | Requirement |
|----------|-------------|
| CPU | Standard laptop or workstation (analysis is CPU-bound, single process) |
| RAM | ≥ 4 GB |
| Disk | ≥ 1 GB free (committed dataset ≈ 14 MB) |
| GPU | Not required |

### Operating system

- macOS, Linux, or Windows with WSL2
- `bash` required for `reproduce.sh` and `run`
- Containerized review environments (e.g., Code Ocean): Linux

### Software

| Component | Requirement |
|-----------|-------------|
| Python | ≥ 3.10 (3.10–3.13 accepted) |
| Shell | `bash` |
| Network | Not required for the default keys-free workflow |

### Software libraries

Dependencies are in `requirements.txt`. The **default reproduction path uses only PyYAML** — the analysis is otherwise pure Python standard library (verified in a clean PyYAML-only environment). The remaining packages are for optional figure rebuild and live re-collection:

- `pyyaml>=6.0` — configuration (required for reproduction)
- `matplotlib>=3.6` — optional, figure regeneration only
- `openai>=1.40`, `google-genai>=0.3` — optional, live re-collection only
- `requests` (via provider SDKs) — optional, live re-collection only

### Input data included with the artifact

| Path | Description | Approx. size |
|------|-------------|--------------|
| `data/raw/runs_<pair>_v_{old,new}.csv` | Frozen confirmatory call logs (incl. raw response) — 4 files | 8.7 MB |
| `data/raw/runs_<pair>_v_*_T{00,07,10}.csv` | Temperature-robustness subgrids — 12 files | included |
| `data/outcomes/ground_truth.json` | Altman *Z''* band labels the analysis grades against | < 1 MB |
| `docs/*.json` | Reported quarterly financials (no-lookahead context, 1,200 cells) | 4.7 MB |
| `data/frozen/*.freeze.json` | Per-capture SHA-256 receipts | < 1 MB |
| `config/` | Frozen task, model, pair, and grid configuration | < 1 MB |

**Integrity (frozen confirmatory captures):** SHA-256 of every CSV is recorded in `DATA_MANIFEST.md` and in the per-file receipts under `data/frozen/`. Example:

```
data/raw/runs_openai_nano_v_old.csv SHA-256 =
af1ace99c938a23ddba948d7df092763...   (full hash in DATA_MANIFEST.md)
```

### Optional dependencies (live re-collection only)

API credentials for OpenAI, Google Gemini, and Financial Modeling Prep are required **only** for live re-collection (`make all SUBGRID=full`) and are read from `../API Keys/keys.env.txt`. They are **not** required for the default reproduction path, which runs entirely from the committed frozen dataset.

---

## 3. Installation and Deployment

### Time estimates

| Step | Typical duration |
|------|------------------|
| Create venv + install PyYAML (first time) | < 1 minute |
| Default reproduction (`bash reproduce.sh`, both pairs) | ~1 minute |
| Determinism check (`bash reproduce.sh --verify`) | ~2 minutes |
| Live re-collection of 14,400 calls (optional) | hours; provider-cost |

### Installation

```bash
git clone https://github.com/samirrc2/version-migration-shock.git
cd version-migration-shock
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
bash reproduce.sh
```

No compilation step is required. On Code Ocean, packages come from `environment/Dockerfile` — no venv step.

### Deployment / execution

| Goal | Command |
|------|---------|
| Regenerate both migrations + gate-check (default) | `bash reproduce.sh` |
| Prove determinism (analyze twice, hash-compare) | `bash reproduce.sh --verify` |
| Analyze one pair | `python3 analysis/run.py --pair openai_nano` |
| Run the build gate only | `python3 render/check_claims.py` |
| Run unit tests | `python3 tests/test_metrics.py && python3 tests/test_stats.py` |
| Code Ocean entry point | `./run` (delegates to `reproduce.sh`) |
| Live re-collection (optional; **not** required to verify the paper) | `make all SUBGRID=full` |

Outputs are written to `claims_<pair>.json` and `results_<pair>.md`, and mirrored into `results/` (the Code Ocean `/results` convention).

---

## 4. Reproducibility of Experiments

### Workflow

```text
data/raw/runs_<pair>_v_{old,new}.csv + data/outcomes/ground_truth.json + config/
        │
        ▼
  bash reproduce.sh
  (→ analysis/run.py per pair → render/report.py → render/check_claims.py)
        │
        ├── claims_<pair>.json     # every reported number, single source of truth
        ├── results_<pair>.md      # human-readable per-pair results report
        └── [check] OK             # build gate: fails if any number ≠ frozen analysis
```

The primary endpoint is `excess_flip_rate = cross_version_flip_rate − within_version_flip_rate`, cluster-bootstrapped over tickers (2,000 draws, seed 42). `analysis/run.py` is a pure, seeded function of the frozen CSVs and configuration and produces byte-identical output on every re-run (`--verify` proves this).

### Expected results

After `bash reproduce.sh`, both pairs must pass the gate (`[check] OK — 39 required claims present`) and `claims_<pair>.json` must contain:

| Quantity | `openai_nano` | `gemini_flash` |
|----------|--------------:|---------------:|
| Matched cells | 3,490 | 3,600 |
| **Excess flip rate (primary)** | **0.1116** | **0.3806** |
| 95% CI (cluster bootstrap) | [0.0772, 0.1495] | [0.3025, 0.4583] |
| cross-version flip | 0.2166 | 0.3886 |
| within-version noise floor (pooled) | 0.1050 | 0.0081 |
| Excess vs conservative max floor | 0.0966 [0.060, 0.135] | 0.3725 [0.295, 0.451] |
| Marginal (rating-mix) shift | 0.0946 | 0.3186 |
| Churn (genuine) | 0.1221 | 0.0700 |
| Cohen κ / Scott π / Gwet AC1 | 0.60 / 0.60 / 0.70 | 0.33 / 0.27 / 0.47 |
| McNemar drift *p* | 5.67×10⁻¹⁸ | 1.39×10⁻⁵⁹ |
| Balanced accuracy old→new | 0.538→0.570 | 0.488→0.408 |
| Macro-F1 old→new (baseline 0.357) | 0.517→0.565 | 0.463→0.325 |

These are the same quantities reported in the article's Results section (Table 1). The determinism check must print `deterministic: byte-identical across re-runs`.

### Out of scope for the default workflow

- Re-issuing live model API calls (`make all` / `capture/orchestrator.py`)
- Any inference or API spend
- Figure regeneration (requires matplotlib; not needed to verify the numbers)

---

## 5. Other Notes

- **Pre-registration and freeze records:** `PREREGISTRATION.md`, `PREREGISTRATION.freeze.txt`, `PREREGISTRATION_AMENDMENTS.md`
- **Model manifest and run playbook:** `docs/model_manifest.md`, `docs/STUDY_RUN.md`
- **Provenance:** every capture is SHA-256-stamped in `DATA_MANIFEST.md` and `data/frozen/*.freeze.json`; the frozen CSVs are the object of record and must not be regenerated (a correction requires a new versioned file plus a manifest changelog entry).
- **Anti-drift gate:** `render/check_claims.py` fails if any reported number disagrees with the frozen analysis or a required claim (`config/slots.yaml`) is missing.
- **Manuscript source:** the official IEEE Access LaTeX and PDF are maintained under `paper/` (not part of the committed code artifact); `paper/main.tex` compiles to `paper/main.pdf`.
- **Submission / anonymization:** see `SUBMISSION_ARTIFACT.md`.
- **Issues and support:** GitHub Issues, or the author emails in Section 1.

### Repository structure

```text
version-migration-shock/
├── README.md                     LICENSE            requirements.txt
├── reproduce.sh                  run                Makefile
├── DATA_MANIFEST.md              SUBMISSION_ARTIFACT.md   ARCHITECTURE.md
├── PREREGISTRATION.md  PREREGISTRATION.freeze.txt  PREREGISTRATION_AMENDMENTS.md
│
├── config/     task.yaml, models.yaml, pairs.yaml, grid.yaml, loader.py, taskcfg.py, slots.yaml
├── capture/    orchestrator.py, agent.py, build_docs/inputs/outcomes.py, freeze.py, secrets.py
├── analysis/   metrics.py, stats.py, baseline.py, groundtruth.py, outcomes.py, tempsweep.py, run.py
├── render/     report.py (results report), check_claims.py (build gate)
├── tests/      test_metrics.py, test_stats.py
├── environment/  Dockerfile + README  (Code Ocean capsule)
├── metadata/   metadata.yml
├── docs/       model_manifest.md, STUDY_RUN.md, and the reported-financials JSON (data)
│
├── data/
│   ├── raw/       runs_<pair>_v_{old,new}.csv (+ temperature subgrids)  — frozen, committed
│   ├── frozen/    *.freeze.json  (SHA-256 receipts)
│   └── outcomes/  ground_truth.json  (Altman labels)
│
├── claims_<pair>.json, results_<pair>.md, tempsweep_<pair>.json    committed per-pair results
├── results/                      generated by reproduce.sh (Code Ocean /results; gitignored)
└── paper/                        official IEEE Access manuscript (gitignored)
```

`inputs/` (legacy price context for the inactive directional task) and generated artifacts (`claims.json`, `PILOT_RESULTS.md`, `results/`, `logs/`, `.venv/`) are gitignored.

### Reviewer quick start

```bash
git clone https://github.com/samirrc2/version-migration-shock.git
cd version-migration-shock
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
bash reproduce.sh          # ~1 min, no keys, no cost
```

Confirm both pairs report `[check] OK`, and that `claims_openai_nano.json` / `claims_gemini_flash.json` match the Expected Results table in Section 4. Optionally run `bash reproduce.sh --verify` for the determinism proof.

## 6. License

MIT (code) — see `LICENSE`.
