# Results — gemini_flash  (REAL DATA)

Primary endpoint: excess_flip_rate = cross_version - within_version. Cluster bootstrap over tickers (seed 42, 2000 draws). Matched cells: 3600.

## Headline

Excess flip rate 0.3806 (95% CI [0.3025, 0.4583]); cross-version 0.3886 vs within-version noise floor 0.0081.

## Prevalence decomposition — is it a stance shift or genuine churn?

Gross flip splits into a marginal/prevalence shift of 0.3186 (the book-wide default-stance move the new version forces) plus genuine per-cell churn of 0.07 (95% CI [0.0292, 0.12]). Chance-corrected agreement (Cohen kappa) between versions: 0.3257. If marginal_shift dominates churn, the effect is a wholesale stance change, not per-name reconsideration.

| category | v_old share | v_new share |
|---|---|---|
| SAFE | 0.389 | 0.708 |
| WATCH | 0.525 | 0.281 |
| DISTRESS | 0.086 | 0.012 |

## Agreement robustness (three chance-corrected statistics)

Cohen kappa 0.3257, Scott pi 0.2732, Gwet AC1 0.4696. If all three agree the low agreement is not an artifact of one estimator's chance model.

Context coverage: 1.0 of calls used real price-derived context (price_derived). Primary excess-flip CI half-width: 0.0779.

## Table 1 — flips when nothing changes vs when the model changes

| quantity | flip rate | n pairs |
|---|---|---|
| within-version, v_old (seeds only) | 0.0161 | 3600 |
| within-version, v_new (seeds only) | 0.0000 | 3600 |
| within-version, pooled (noise floor) | 0.0081 | 7200 |
| cross-version (migration) | 0.3886 | 3600 |

## Directional drift and turnover

McNemar (bullish indicator): chi2 = 265.0, p = 1.39e-59. Conviction shift 0.8211. Implied portfolio turnover 0.2014 of the book.

## Accuracy vs realized 20-day forward return (exploratory)

Directional hit-rate: v_old 0.4942 (n=1200), v_new 0.425 (n=1200). On cells that flipped, new-minus-old hit-rate = -0.1785 (95% CI [-0.38, 0.0302]) — CI spanning 0 means the migration neither reliably improves nor degrades the flipped calls.

## Dose-response — flips vs v_old within-cell instability

Boundary-distance proxy (conviction-free). Unstable-minus-stable contrast: 0.2496 (positive = flips concentrate in near-boundary cells; note this proxy has a mechanical component and is pre-registered as a secondary).

| v_old cell | cross-version flip rate | n |
|---|---|---|
| stable | 0.3826 | 3513 |
| unstable | 0.6322 | 87 |

Conviction-based dose-response (secondary, typically degenerate): slope -0.2171 over 3 distinct conviction values.

## Flip rate by sector

| sector | flip rate | n |
|---|---|---|
| Communication Services | 0.1562 | 288 |
| Consumer Discretionary | 0.6556 | 360 |
| Consumer Staples | 0.5278 | 324 |
| Energy | 0.1235 | 324 |
| Financials | 0.6167 | 360 |
| Health Care | 0.2778 | 360 |
| Industrials | 0.4861 | 360 |
| Information Technology | 0.3917 | 360 |
| Materials | 0.3299 | 288 |
| Real Estate | 0.4167 | 288 |
| Utilities | 0.1875 | 288 |

## Flip rate by date

| date | flip rate | n |
|---|---|---|
| 2026-01-09 | 0.3967 | 300 |
| 2026-01-23 | 0.3933 | 300 |
| 2026-02-06 | 0.4067 | 300 |
| 2026-02-20 | 0.3767 | 300 |
| 2026-03-06 | 0.3767 | 300 |
| 2026-03-20 | 0.4000 | 300 |
| 2026-04-03 | 0.3967 | 300 |
| 2026-04-17 | 0.3933 | 300 |
| 2026-05-01 | 0.3700 | 300 |
| 2026-05-15 | 0.3833 | 300 |
| 2026-05-22 | 0.3900 | 300 |
| 2026-05-29 | 0.3800 | 300 |

<!-- CLAIMS-START -->
excess_flip_rate.value = 0.3806
excess_flip_rate.ci_low = 0.3025
excess_flip_rate.ci_high = 0.4583
cross_version_flip_rate.value = 0.3886
within_version_flip_rate.value = 0.0081
prevalence.marginal_shift = 0.3186
prevalence.churn = 0.07
prevalence.cohen_kappa = 0.3257
context_coverage.frac_real = 1.0
agreement.scott_pi = 0.2732
agreement.gwet_ac1 = 0.4696
precision.excess_ci_halfwidth = 0.0779
accuracy.hit_rate_old = 0.4942
accuracy.hit_rate_new = 0.425
accuracy.flip_conditional_delta = -0.1785
accuracy.flip_conditional_ci_low = -0.38
accuracy.flip_conditional_ci_high = 0.0302
conviction_shift.value = 0.8211
implied_turnover.fraction = 0.2014
dose_response.instability_contrast = 0.2496
dose_response.conviction_slope = -0.2171
mcnemar.p_display = 1.39e-59
n_matched_cells = 3600
<!-- CLAIMS-END -->
