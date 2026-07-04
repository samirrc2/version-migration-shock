# Results — openai_nano  (REAL DATA)

Primary endpoint: excess_flip_rate = cross_version - within_version. Cluster bootstrap over tickers (seed 42, 2000 draws). Matched cells: 3490.

## Headline

Excess flip rate 0.1116 (95% CI [0.0772, 0.1495]); cross-version 0.2166 vs within-version noise floor 0.105.

## Prevalence decomposition — is it a stance shift or genuine churn?

Gross flip splits into a marginal/prevalence shift of 0.0946 (the book-wide default-stance move the new version forces) plus genuine per-cell churn of 0.1221 (95% CI [0.0834, 0.1611]). Chance-corrected agreement (Cohen kappa) between versions: 0.6032. If marginal_shift dominates churn, the effect is a wholesale stance change, not per-name reconsideration.

| category | v_old share | v_new share |
|---|---|---|
| SAFE | 0.304 | 0.209 |
| WATCH | 0.588 | 0.636 |
| DISTRESS | 0.108 | 0.155 |

## Agreement robustness (three chance-corrected statistics)

Cohen kappa 0.6032, Scott pi 0.6007, Gwet AC1 0.7027. If all three agree the low agreement is not an artifact of one estimator's chance model.

Context coverage: 1.0 of calls used real price-derived context (price_derived). Primary excess-flip CI half-width: 0.0361.

## Table 1 — flips when nothing changes vs when the model changes

| quantity | flip rate | n pairs |
|---|---|---|
| within-version, v_old (seeds only) | 0.1200 | 3483 |
| within-version, v_new (seeds only) | 0.0901 | 3497 |
| within-version, pooled (noise floor) | 0.1050 | 6980 |
| cross-version (migration) | 0.2166 | 3490 |

## Directional drift and turnover

McNemar (bullish indicator): chi2 = 74.63, p = 5.67e-18. Conviction shift 0.1602. Implied portfolio turnover 0.1083 of the book.

## Accuracy vs realized 20-day forward return (exploratory)

Directional hit-rate: v_old 0.5392 (n=1200), v_new 0.5642 (n=1200). On cells that flipped, new-minus-old hit-rate = 0.1235 (95% CI [-0.1639, 0.4179]) — CI spanning 0 means the migration neither reliably improves nor degrades the flipped calls.

## Dose-response — flips vs v_old within-cell instability

Boundary-distance proxy (conviction-free). Unstable-minus-stable contrast: 0.3295 (positive = flips concentrate in near-boundary cells; note this proxy has a mechanical component and is pre-registered as a secondary).

| v_old cell | cross-version flip rate | n |
|---|---|---|
| stable | 0.1584 | 2873 |
| unstable | 0.4878 | 617 |

Conviction-based dose-response (secondary, typically degenerate): slope 0.1066 over 4 distinct conviction values.

## Flip rate by sector

| sector | flip rate | n |
|---|---|---|
| Communication Services | 0.0423 | 284 |
| Consumer Discretionary | 0.3660 | 347 |
| Consumer Staples | 0.0804 | 311 |
| Energy | 0.4241 | 316 |
| Financials | 0.2964 | 334 |
| Health Care | 0.2257 | 350 |
| Industrials | 0.1069 | 346 |
| Information Technology | 0.0722 | 360 |
| Materials | 0.1489 | 282 |
| Real Estate | 0.3746 | 283 |
| Utilities | 0.2491 | 277 |

## Flip rate by date

| date | flip rate | n |
|---|---|---|
| 2026-01-09 | 0.2111 | 289 |
| 2026-01-23 | 0.1986 | 292 |
| 2026-02-06 | 0.2337 | 291 |
| 2026-02-20 | 0.2069 | 290 |
| 2026-03-06 | 0.2245 | 294 |
| 2026-03-20 | 0.2371 | 291 |
| 2026-04-03 | 0.2218 | 293 |
| 2026-04-17 | 0.2404 | 287 |
| 2026-05-01 | 0.1952 | 292 |
| 2026-05-15 | 0.2158 | 292 |
| 2026-05-22 | 0.2165 | 291 |
| 2026-05-29 | 0.1979 | 288 |

<!-- CLAIMS-START -->
excess_flip_rate.value = 0.1116
excess_flip_rate.ci_low = 0.0772
excess_flip_rate.ci_high = 0.1495
cross_version_flip_rate.value = 0.2166
within_version_flip_rate.value = 0.105
prevalence.marginal_shift = 0.0946
prevalence.churn = 0.1221
prevalence.cohen_kappa = 0.6032
context_coverage.frac_real = 1.0
agreement.scott_pi = 0.6007
agreement.gwet_ac1 = 0.7027
precision.excess_ci_halfwidth = 0.0361
accuracy.hit_rate_old = 0.5392
accuracy.hit_rate_new = 0.5642
accuracy.flip_conditional_delta = 0.1235
accuracy.flip_conditional_ci_low = -0.1639
accuracy.flip_conditional_ci_high = 0.4179
conviction_shift.value = 0.1602
implied_turnover.fraction = 0.1083
dose_response.instability_contrast = 0.3295
dose_response.conviction_slope = 0.1066
mcnemar.p_display = 5.67e-18
n_matched_cells = 3490
<!-- CLAIMS-END -->
