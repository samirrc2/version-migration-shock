# Pre-registration — Version Migration as a Correlated Shock (Paper 2, credit-health task)

This supersedes the earlier directional-task pre-registration (retained in version
history), which is withdrawn. This plan is frozen BEFORE any credit-task data is
collected, so every endpoint below is a genuine pre-registered, out-of-sample test
for BOTH migration pairs. The SHA-256 of this file is recorded in
PREREGISTRATION.freeze.txt. Raw data is collected once per (pair, version) into
immutable, hash-stamped CSVs; analysis/run.py is a pure, seeded function of those
CSVs and config and must produce byte-identical claims.json on every re-execution.

## Background

Financial institutions deploying LLM agents inherit a risk absent from classical
model governance: when the vendor updates the model, every institution's agents
shift behavior simultaneously and involuntarily. We quantify the decision
discontinuity induced purely by vendor version migration on a task that is (a) a
genuine, widely deployed LLM use case and (b) objectively gradeable: credit-health
classification of a company from its most recently reported quarterly financials.

Two vendor-declared "recommended replacement" migrations with hard shutdown dates:
- **openai_nano**: gpt-5-nano-2025-08-07 -> gpt-5.4-nano (v_old shutdown 2026-12-11).
- **gemini_flash**: gemini-2.5-flash -> gemini-3.5-flash (v_old shutdown 2026-10-16).

## Design

- **Unit / task.** Single-model credit-health classification per (company, as-of
  date, replicate). The agent receives the company's most recent quarterly financial
  statements (income statement + balance sheet + cash flow summary), with filing date
  strictly BEFORE the as-of date (no lookahead), and returns STRICT JSON
  {"direction": "SAFE|WATCH|DISTRESS", "conviction": 1-5, "rationale": "<=30 words"}
  (frozen prompt_credit.txt).
- **Decode.** Temperature 0 (version-isolation regime); reasoning-model determinism
  carried by the fixed seed. Robustness across T in {0, 0.7, 1.0} reported.
- **Seed protocol.** cell_parity: seed = SHA256(seed_master | ticker | date |
  replicate) & 0x7FFFFFFF — independent of model/version, so v_old and v_new receive
  identical seeds at each cell (zero seed mismatches verified).
- **Grid.** 100 GICS-stratified companies x 12 as-of dates in 2026 x 3 replicates
  per version. Documents are the reported financials fetched once from FMP stable
  REST and frozen; the reported figures are immutable, so the study is reproducible.

## Primary endpoint

**excess_flip_rate = cross_version_flip_rate - within_version_flip_rate**, where
cross_version_flip_rate is the fraction of matched (company, date, replicate) pairs
whose credit label differs between v_old and v_new, and within_version_flip_rate is
the fraction of within-version replicate pairs (same cell, different seed) that
differ, pooled over both versions. Uncertainty: cluster bootstrap resampling
COMPANIES, 2,000 draws, fixed RNG seed 42, percentile 95% CI.

## Decision rule

Per pair, report **CONFIRMED / WEAKENED / CONTRADICTED** against excess_flip_rate > 0:
CONFIRMED if point > 0 and 95% CI excludes 0; WEAKENED if point > 0 and CI includes 0;
CONTRADICTED if point <= 0. The finding stands on the primary point estimate and CI.

## Pre-registered secondary endpoints (supporting, not gating)

- **Instability dose-response**: cross-version flip rate bucketed by v_old within-cell
  instability across seeds (unstable_minus_stable contrast > 0 expected).
- **Prevalence / churn decomposition**: gross flip = marginal (rating-mix) shift +
  genuine per-company churn; churn CI and Cohen's kappa, with Scott's pi and Gwet's
  AC1 as agreement-statistic robustness.
- **Credit-tier migration magnitude**: mean |Δtier| on the ordinal
  SAFE(0)/WATCH(1)/DISTRESS(2) mapping (the credit analog of turnover).
- **Directional drift**: continuity-corrected McNemar test on the DISTRESS indicator
  (does migration systematically push assessments toward distress?).
- **Accuracy vs objective ground truth**: hit-rate of each version's label against
  the Altman Z'' band (Z''>2.6 SAFE, 1.1-2.6 WATCH, <1.1 DISTRESS) computed from the
  same statements, with Wilson 95% CIs, and the flip-conditional new-minus-old
  hit-rate with a bootstrap CI (does migration change correct assessments?).
- **Per-stratum descriptives**: flip rate by GICS sector and by as-of date.

## Replicability clause

Reported financials (immutable) are fetched once, frozen, and shipped in the
artifact; the Altman ground truth is a fixed formula over those figures. Raw model
data is collected once per (pair, version) into read-only, SHA-256-stamped CSVs.
analysis/run.py emits claims.json deterministically; render/check_claims.py fails the
build on any manuscript number that disagrees with claims.json or any unfilled slot.

## Provenance

The full pipeline, endpoints, decision rule, and Altman ground truth are fixed by
this frozen file before any credit-task model call. The directional-task study is
superseded and reported, if at all, only as a preliminary in version history.
