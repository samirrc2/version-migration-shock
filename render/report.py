"""Render PILOT_RESULTS.md from claims.json only. Numbers are substituted from the
single source of truth, never typed by hand, then validated by check_claims.py."""
from __future__ import annotations
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "config"))
import taskcfg

_HERE = Path(__file__).resolve().parent
_CLAIMS = _HERE.parent / "claims.json"
_OUT = _HERE.parent / "PILOT_RESULTS.md"

H1 = "#"
H2 = "##"


def main() -> int:
    if not _CLAIMS.exists():
        print("[render] claims.json missing — run analysis/run.py first")
        return 2
    c = json.loads(_CLAIMS.read_text())
    d = c["detail"]
    meta = c["meta"]
    decomp = d["decomposition"]
    prev = d["prevalence"]
    dose_i = d["dose_response_instability"]
    dose_c = d["dose_response_conviction"]["table"]
    strata = d["strata"]

    def g(k):
        return c[k]

    L = []
    L.append(f"{H1} Results — {meta['pair']}  ({meta['data_mode']} DATA)\n")
    if meta["data_mode"] == "MOCK":
        L.append("> MOCK DATA. Validates the pipeline, not the hypothesis.\n")
    if meta.get("context_mode") == "placeholder":
        L.append("> WARNING: context_mode = placeholder. Decisions were made on EMPTY "
                 "prompts (no price/fundamental context), so the flips below are a "
                 "version default-stance shift, not grounded decision instability. Run "
                 "capture/build_inputs.py and re-capture before using these numbers.\n")
    L.append(f"Primary endpoint: excess_flip_rate = cross_version - within_version. "
             f"Cluster bootstrap over tickers (seed {meta['bootstrap_seed']}, "
             f"{meta['bootstrap_draws']} draws). Matched cells: {g('n_matched_cells')}.\n")
    L.append(f"Design: {g('design.calls_per_version')} calls/version, "
             f"{g('design.calls_per_pair')} calls/pair, {g('design.calls_two_pairs')} across two pairs.\n")

    L.append(f"{H2} Headline\n")
    L.append(f"Excess flip rate {g('excess_flip_rate.value')} "
             f"(95% CI [{g('excess_flip_rate.ci_low')}, {g('excess_flip_rate.ci_high')}]); "
             f"cross-version {g('cross_version_flip_rate.value')} vs within-version noise "
             f"floor {g('within_version_flip_rate.value')}.\n")

    L.append(f"{H2} Prevalence decomposition — is it a stance shift or genuine churn?\n")
    L.append(f"Gross flip splits into a marginal/prevalence shift of "
             f"{g('prevalence.marginal_shift')} (the book-wide default-stance move the "
             f"new version forces) plus genuine per-cell churn of {g('prevalence.churn')} "
             f"(95% CI [{g('prevalence.churn_ci_low')}, {g('prevalence.churn_ci_high')}]). "
             f"Chance-corrected agreement (Cohen kappa) between versions: "
             f"{g('prevalence.cohen_kappa')}. If marginal_shift dominates churn, the effect "
             f"is a wholesale stance change, not per-name reconsideration.\n")
    L.append("| category | v_old share | v_new share |")
    L.append("|---|---|---|")
    for dr in taskcfg.CATEGORIES:
        L.append(f"| {dr} | {prev['marginals_v_old'][dr]:.3f} | {prev['marginals_v_new'][dr]:.3f} |")
    L.append("")

    agr = d["agreement"]
    L.append(f"{H2} Agreement robustness (three chance-corrected statistics)\n")
    L.append(f"Cohen kappa {agr['cohen_kappa']:.4f}, Scott pi {g('agreement.scott_pi')}, "
             f"Gwet AC1 {g('agreement.gwet_ac1')}. If all three agree the low agreement is "
             f"not an artifact of one estimator's chance model.\n")
    L.append(f"Context coverage: {g('context_coverage.frac_real')} of calls used real "
             f"price-derived context ({meta.get('context_mode')}). Primary excess-flip CI "
             f"half-width: {g('precision.excess_ci_halfwidth')}.\n")

    L.append(f"{H2} Table 1 — flips when nothing changes vs when the model changes\n")
    L.append("| quantity | flip rate | n pairs |")
    L.append("|---|---|---|")
    L.append(f"| within-version, v_old (seeds only) | {decomp['within_version_v_old']['flip_rate']:.4f} | {decomp['within_version_v_old']['n_pairs']} |")
    L.append(f"| within-version, v_new (seeds only) | {decomp['within_version_v_new']['flip_rate']:.4f} | {decomp['within_version_v_new']['n_pairs']} |")
    L.append(f"| within-version, pooled (noise floor) | {decomp['within_version_pooled']['flip_rate']:.4f} | {decomp['within_version_pooled']['n_pairs']} |")
    L.append(f"| cross-version (migration) | {decomp['cross_version']['flip_rate']:.4f} | {decomp['cross_version']['n_pairs']} |\n")

    L.append(f"{H2} Directional drift and turnover\n")
    L.append(f"McNemar (bullish indicator): chi2 = {g('mcnemar.chi2')}, p = {g('mcnemar.p_display')}. "
             f"Conviction shift {g('conviction_shift.value')}. Implied portfolio turnover "
             f"{g('implied_turnover.fraction')} of the book.\n")

    acc = d["accuracy"]
    L.append(f"{H2} Accuracy vs realized 20-day forward return (exploratory)\n")
    if acc.get("available"):
        L.append(f"Directional hit-rate: v_old {g('accuracy.hit_rate_old')} "
                 f"(n={acc['n_scored_old']}), v_new {g('accuracy.hit_rate_new')} "
                 f"(n={acc['n_scored_new']}). On cells that flipped, new-minus-old hit-rate "
                 f"= {g('accuracy.flip_conditional_delta')} "
                 f"(95% CI [{g('accuracy.flip_conditional_ci_low')}, "
                 f"{g('accuracy.flip_conditional_ci_high')}]) — CI spanning 0 means the "
                 f"migration neither reliably improves nor degrades the flipped calls.\n")
    else:
        L.append("Not available — run capture/build_outcomes.py to score decisions against "
                 "realized forward returns.\n")

    L.append(f"{H2} Dose-response — flips vs v_old within-cell instability\n")
    L.append(f"Boundary-distance proxy (conviction-free). Unstable-minus-stable contrast: "
             f"{g('dose_response.instability_contrast')} (positive = flips concentrate in "
             f"near-boundary cells; note this proxy has a mechanical component and is "
             f"pre-registered as a secondary).\n")
    L.append("| v_old cell | cross-version flip rate | n |")
    L.append("|---|---|---|")
    for b in ("stable", "unstable"):
        v = dose_i["table"][b]
        L.append(f"| {b} | {v['flip_rate']:.4f} | {v['n']} |")
    L.append("")
    L.append(f"Conviction-based dose-response (secondary, typically degenerate): slope "
             f"{g('dose_response.conviction_slope')} over "
             f"{d['dose_response_conviction']['n_distinct_conviction']} distinct conviction values.\n")

    L.append(f"{H2} Flip rate by sector\n")
    L.append("| sector | flip rate | n |")
    L.append("|---|---|---|")
    for s, v in strata["by_sector"].items():
        L.append(f"| {s} | {v['flip_rate']:.4f} | {v['n']} |")
    L.append("")
    L.append(f"{H2} Flip rate by date\n")
    L.append("| date | flip rate | n |")
    L.append("|---|---|---|")
    for dt, v in strata["by_date"].items():
        L.append(f"| {dt} | {v['flip_rate']:.4f} | {v['n']} |")
    L.append("")

    L.append("<!-- CLAIMS-START -->")
    for k in ["excess_flip_rate.value", "excess_flip_rate.ci_low", "excess_flip_rate.ci_high",
              "cross_version_flip_rate.value", "within_version_flip_rate.value",
              "prevalence.marginal_shift", "prevalence.churn", "prevalence.cohen_kappa",
              "context_coverage.frac_real", "agreement.scott_pi", "agreement.gwet_ac1",
              "precision.excess_ci_halfwidth", "accuracy.hit_rate_old", "accuracy.hit_rate_new",
              "accuracy.flip_conditional_delta", "accuracy.flip_conditional_ci_low",
              "accuracy.flip_conditional_ci_high",
              "conviction_shift.value", "implied_turnover.fraction",
              "dose_response.instability_contrast", "dose_response.conviction_slope",
              "mcnemar.p_display", "n_matched_cells",
              "design.calls_per_version", "design.calls_per_pair", "design.calls_two_pairs"]:
        L.append(f"{k} = {g(k)}")
    L.append("<!-- CLAIMS-END -->")

    _OUT.write_text("\n".join(L) + "\n")
    print(f"[render] wrote {_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
