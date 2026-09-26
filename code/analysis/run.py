"""Single analysis entrypoint. Pure, deterministic, zero-cost. Reads the two frozen
version CSVs for a pair and emits claims.json, the single source of truth that every
table, figure, and manuscript sentence must agree with (checked by
render/check_claims.py)."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "config"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import metrics as M
import stats as S
import baseline as B
import outcomes as O
import loader as C
from _paths import repo_root, results_dir

_ROOT = repo_root()
_RAW = _ROOT / "data" / "raw"
_OUT = results_dir() / "claims.json"


def analyse_pair(pair_id: str, draws: int, seed: int, sectors: dict) -> dict:
    old_csv = _RAW / f"runs_{pair_id}_v_old.csv"
    new_csv = _RAW / f"runs_{pair_id}_v_new.csv"
    if not (old_csv.exists() and new_csv.exists()):
        raise FileNotFoundError(f"need both {old_csv.name} and {new_csv.name} — capture first")
    rows_old, rows_new = M.load_rows(old_csv), M.load_rows(new_csv)
    pairs = M.paired(rows_old, rows_new)

    decomp = B.decomposition(rows_old, rows_new)
    boot = S.cluster_bootstrap_excess(pairs, rows_old, rows_new, draws=draws, seed=seed)
    prev = M.prevalence_decomposition(pairs)
    strata = M.flip_by_stratum(pairs, sectors)
    conv, n_conv = M.conviction_shift(pairs)
    turn = M.implied_turnover(pairs)
    dose_i = M.dose_response_by_instability(pairs, rows_old)
    dose_c = M.dose_response_by_conviction(pairs)
    mcn = S.mcnemar_directional(pairs)
    tmat = M.transition_matrix(pairs)

    ci_churn = S.cluster_bootstrap_scalar(
        pairs, lambda ps: M.prevalence_decomposition(ps).get("churn"), draws, seed)
    ci_kappa = S.cluster_bootstrap_scalar(pairs, lambda ps: M.cohen_kappa(ps), draws, seed)
    ci_conv = S.cluster_bootstrap_scalar(pairs, lambda ps: M.conviction_shift(ps)[0], draws, seed)
    ci_turn = S.cluster_bootstrap_scalar(
        pairs, lambda ps: M.implied_turnover(ps)["turnover_fraction"], draws, seed)

    agr = M.agreement_statistics(pairs)
    acc = O.accuracy(rows_old, rows_new, sectors)

    # --- referee-requested additions -------------------------------------------------
    # R1.1/R2.1: a same-seed repeat-call noise floor, constructed the same way as the
    # cross-version contrast. The T00 re-captures are independently timed calls at the
    # identical seed and temperature, so they give the matched floor the referees asked for.
    rep_old = _RAW / f"runs_{pair_id}_v_old_T00.csv"
    rep_new = _RAW / f"runs_{pair_id}_v_new_T00.csv"
    matched = (B.matched_baseline(rows_old, rows_new, M.load_rows(rep_old), M.load_rows(rep_new))
               if (rep_old.exists() and rep_new.exists()) else {"available": False})

    # R1.2: the distribution-distance statistic, named and separated from the per-call
    # flip probability so the two are not read as answering the same question.
    tvd = M.total_variation_distance(pairs)
    ci_tvd = S.cluster_bootstrap_scalar(
        pairs, lambda ps: M.total_variation_distance(ps).get("tvd"), draws, seed)

    # R2.6: the temperature subgrid's T=0 row differs from the full-grid primary estimate at
    # the same nominal setting. Re-running the primary estimator on exactly the subgrid cells
    # separates cell selection from any temperature effect.
    sub_cells = sorted({(r["ticker"], r["date"]) for r in M.load_rows(rep_old)}) \
        if rep_old.exists() else []
    if sub_cells:
        sp = M.restrict_pairs_to_cells(pairs, sub_cells)
        so = [r for r in rows_old if (r["ticker"], r["date"]) in set(sub_cells)]
        sn = [r for r in rows_new if (r["ticker"], r["date"]) in set(sub_cells)]
        sub = B.decomposition(so, sn)
        subgrid_recon = {"n_cells": len(sub_cells), "n_matched": len(sp),
                         "cross_version_flip_rate": sub["cross_version"]["flip_rate"],
                         "within_version_pooled": sub["within_version_pooled"]["flip_rate"],
                         "excess_flip_rate": sub["excess_flip_rate_point"]}
    else:
        subgrid_recon = {"available": False}

    # R2.4: the same class-balanced statistics on the Altman-appropriate subset, computed on
    # matched pairs so the restricted flip rate is available alongside the accuracy figures.
    restricted_pairs = M.restrict_pairs_excluding_sectors(pairs, sectors, ("Financials", "Real Estate"))
    rcross, rn = M.cross_version_flip_rate(restricted_pairs)
    restricted_flip = {"cross_version_flip_rate": rcross, "n_matched": rn,
                       "excluded_sectors": ["Financials", "Real Estate"]}
    noise = S.noise_floor_report(pairs, rows_old, rows_new, draws=draws, seed=seed)
    all_rows = rows_old + rows_new
    n_real = sum(1 for r in all_rows if r.get("snippet_source") == "inputs_file")
    frac_real = (n_real / len(all_rows)) if all_rows else 0.0
    frac_placeholder = sum(1 for r in rows_old if r.get("snippet_source") == "constructed_placeholder")
    context_mode = ("placeholder" if frac_placeholder == len(rows_old) and rows_old
                    else ("price_derived" if frac_real > 0.99 else "mixed"))
    excess_hw = None
    if boot["ci_low"] is not None and boot["ci_high"] is not None:
        excess_hw = (boot["ci_high"] - boot["ci_low"]) / 2

    return {
        "pair": pair_id,
        "n_matched_cells": len(pairs),
        "context_mode": context_mode,
        "context_coverage": {"frac_real": frac_real},
        "agreement": agr,
        "accuracy": acc,
        "precision": {"excess_ci_halfwidth": excess_hw},
        "decomposition": decomp,
        "excess_flip_rate": {"value": boot["point"], "ci": [boot["ci_low"], boot["ci_high"]],
                             "cross": boot["cross"], "within": boot["within"],
                             "n_tickers": boot["n_tickers"], "n_boot": boot["n_valid"]},
        "noise_sensitivity": noise,
        "matched_baseline": matched,
        "distribution_distance": {**tvd, "tvd_ci": [ci_tvd["ci_low"], ci_tvd["ci_high"]]},
        "subgrid_reconciliation": subgrid_recon,
        "restricted_flip": restricted_flip,
        "prevalence": {**prev, "churn_ci": [ci_churn["ci_low"], ci_churn["ci_high"]],
                       "cohen_kappa_ci": [ci_kappa["ci_low"], ci_kappa["ci_high"]]},
        "conviction_shift": {"value": conv, "n": n_conv,
                             "ci": [ci_conv["ci_low"], ci_conv["ci_high"]]},
        "implied_turnover": {**turn, "ci": [ci_turn["ci_low"], ci_turn["ci_high"]]},
        "dose_response_instability": dose_i,
        "dose_response_conviction": dose_c,
        "mcnemar_directional": mcn,
        "strata": strata,
        "transition_matrix": tmat,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", default=None)
    args = ap.parse_args()
    cfg = C.load_all()
    pair_id = args.pair or cfg["pairs"]["pilot"]["pair"]
    grid = cfg["grid"]
    res = analyse_pair(pair_id, int(grid["bootstrap_draws"]), int(grid["bootstrap_seed"]),
                       grid.get("sectors", {}))

    p = res["mcnemar_directional"]["p_value"]
    p_display = "<1e-16" if p == 0 else f"{p:.2e}"
    mock = _mock_flag(pair_id)
    _full = cfg["grid"]["subgrids"]["full"]
    _nrep = int(cfg["pairs"]["defaults"]["n_replicates"])
    per_ver = len(_full["tickers"]) * len(_full["dates"]) * _nrep  # design constants (gated)
    claims = {
        "meta": {"pair": pair_id, "bootstrap_seed": int(grid["bootstrap_seed"]),
                 "bootstrap_draws": int(grid["bootstrap_draws"]),
                 "data_mode": "MOCK" if mock else "REAL",
                 "context_mode": res["context_mode"],
                 "primary_endpoint": "excess_flip_rate = cross_version - within_version"},
        "excess_flip_rate.value": _r(res["excess_flip_rate"]["value"]),
        "excess_flip_rate.ci_low": _r(res["excess_flip_rate"]["ci"][0]),
        "excess_flip_rate.ci_high": _r(res["excess_flip_rate"]["ci"][1]),
        "cross_version_flip_rate.value": _r(res["excess_flip_rate"]["cross"]),
        "within_version_flip_rate.value": _r(res["excess_flip_rate"]["within"]),
        "prevalence.marginal_shift": _r(res["prevalence"]["marginal_shift"]),
        "prevalence.churn": _r(res["prevalence"]["churn"]),
        "prevalence.churn_ci_low": _r(res["prevalence"]["churn_ci"][0]),
        "prevalence.churn_ci_high": _r(res["prevalence"]["churn_ci"][1]),
        "prevalence.cohen_kappa": _r(res["prevalence"]["cohen_kappa"]),
        "context_coverage.frac_real": _r(res["context_coverage"]["frac_real"]),
        "agreement.scott_pi": _r(res["agreement"]["scott_pi"]),
        "agreement.gwet_ac1": _r(res["agreement"]["gwet_ac1"]),
        "precision.excess_ci_halfwidth": _r(res["precision"]["excess_ci_halfwidth"]),
        "accuracy.hit_rate_old": _r(res["accuracy"].get("hit_rate_old")),
        "accuracy.hit_rate_new": _r(res["accuracy"].get("hit_rate_new")),
        "accuracy.balanced_old": _r((res["accuracy"].get("quality_old") or {}).get("balanced_accuracy")),
        "accuracy.balanced_new": _r((res["accuracy"].get("quality_new") or {}).get("balanced_accuracy")),
        "accuracy.macro_f1_old": _r((res["accuracy"].get("quality_old") or {}).get("macro_f1")),
        "accuracy.macro_f1_new": _r((res["accuracy"].get("quality_new") or {}).get("macro_f1")),
        "accuracy.majority_baseline": _r((res["accuracy"].get("quality_old") or {}).get("majority_class_baseline")),
        "accuracy.hit_rate_old_ex_fin": _r((res["accuracy"].get("quality_old") or {}).get("hit_rate_ex_financials")),
        "accuracy.hit_rate_new_ex_fin": _r((res["accuracy"].get("quality_new") or {}).get("hit_rate_ex_financials")),
        "noise.within_old": _r(res["noise_sensitivity"]["floors"]["old"]),
        "noise.within_new": _r(res["noise_sensitivity"]["floors"]["new"]),
        "noise.within_pooled": _r(res["noise_sensitivity"]["floors"]["pooled"]),
        "noise.excess_conservative": _r(res["noise_sensitivity"]["conservative_excess"]),
        "noise.excess_conservative_ci_low": _r(res["noise_sensitivity"]["conservative_ci"][0]),
        "noise.excess_conservative_ci_high": _r(res["noise_sensitivity"]["conservative_ci"][1]),
        # --- referee-requested claims (gated like every other reported number) ---
        "matched.repeat_floor_pooled": _r(((res.get("matched_baseline") or {})
                                           .get("repeat_floor_pooled") or {}).get("flip_rate")),
        "matched.repeat_floor_n": (((res.get("matched_baseline") or {})
                                    .get("repeat_floor_pooled") or {}).get("n_pairs")),
        "matched.repeat_floor_ci_low": _r((((res.get("matched_baseline") or {})
                                            .get("repeat_floor_pooled") or {})
                                           .get("wilson_ci") or [None, None])[0]),
        "matched.repeat_floor_ci_high": _r((((res.get("matched_baseline") or {})
                                             .get("repeat_floor_pooled") or {})
                                            .get("wilson_ci") or [None, None])[1]),
        "matched.excess_vs_repeat_floor": _r((res.get("matched_baseline") or {})
                                             .get("excess_vs_repeat_floor")),
        "matched.excess_vs_repeat_ci_low": _r(((res.get("matched_baseline") or {})
                                               .get("excess_vs_repeat_floor_ci") or [None, None])[0]),
        "matched.excess_vs_repeat_ci_high": _r(((res.get("matched_baseline") or {})
                                                .get("excess_vs_repeat_floor_ci") or [None, None])[1]),
        "distance.tvd": _r((res.get("distribution_distance") or {}).get("tvd")),
        "distance.tvd_ci_low": _r(((res.get("distribution_distance") or {})
                                   .get("tvd_ci") or [None, None])[0]),
        "distance.tvd_ci_high": _r(((res.get("distribution_distance") or {})
                                    .get("tvd_ci") or [None, None])[1]),
        "subgrid.excess_on_subgrid_cells": _r((res.get("subgrid_reconciliation") or {})
                                              .get("excess_flip_rate")),
        "subgrid.n_cells": ((res.get("subgrid_reconciliation") or {}).get("n_cells")),
        "restricted.cross_version_flip_rate": _r((res.get("restricted_flip") or {})
                                                 .get("cross_version_flip_rate")),
        "restricted.hit_rate_old": _r(((res["accuracy"].get("restricted") or {})).get("hit_rate_old")),
        "restricted.hit_rate_new": _r(((res["accuracy"].get("restricted") or {})).get("hit_rate_new")),
        "restricted.balanced_old": _r(((res["accuracy"].get("restricted") or {})).get("balanced_accuracy_old")),
        "restricted.balanced_new": _r(((res["accuracy"].get("restricted") or {})).get("balanced_accuracy_new")),
        "restricted.macro_f1_old": _r(((res["accuracy"].get("restricted") or {})).get("macro_f1_old")),
        "restricted.macro_f1_new": _r(((res["accuracy"].get("restricted") or {})).get("macro_f1_new")),
        "quality.balanced_delta": _r(((res["accuracy"].get("quality_ci") or {})).get("balanced_accuracy_delta")),
        "quality.balanced_delta_ci_low": _r((((res["accuracy"].get("quality_ci") or {})
                                              ).get("balanced_accuracy_delta_ci") or [None, None])[0]),
        "quality.balanced_delta_ci_high": _r((((res["accuracy"].get("quality_ci") or {})
                                               ).get("balanced_accuracy_delta_ci") or [None, None])[1]),
        "quality.macro_f1_delta": _r(((res["accuracy"].get("quality_ci") or {})).get("macro_f1_delta")),
        "quality.macro_f1_delta_ci_low": _r((((res["accuracy"].get("quality_ci") or {})
                                               ).get("macro_f1_delta_ci") or [None, None])[0]),
        "quality.macro_f1_delta_ci_high": _r((((res["accuracy"].get("quality_ci") or {})
                                                ).get("macro_f1_delta_ci") or [None, None])[1]),
        "accuracy.flip_conditional_delta": _r(res["accuracy"].get("flip_conditional_new_minus_old")),
        "accuracy.flip_conditional_ci_low": _r(res["accuracy"].get("flip_conditional_ci", [None, None])[0]),
        "accuracy.flip_conditional_ci_high": _r(res["accuracy"].get("flip_conditional_ci", [None, None])[1]),
        "conviction_shift.value": _r(res["conviction_shift"]["value"]),
        "implied_turnover.fraction": _r(res["implied_turnover"]["turnover_fraction"]),
        "dose_response.instability_contrast": _r(res["dose_response_instability"]["unstable_minus_stable"]),
        "dose_response.conviction_slope": _r(res["dose_response_conviction"]["slope_per_conviction_point"]),
        "mcnemar.chi2": _r(res["mcnemar_directional"]["chi2"], 2),
        "mcnemar.p_display": p_display,
        "n_matched_cells": res["n_matched_cells"],
        "design.calls_per_version": per_ver,
        "design.calls_per_pair": per_ver * 2,
        "design.calls_two_pairs": per_ver * 4,
        "detail": res,
    }
    _OUT.write_text(json.dumps(claims, indent=2))
    print(f"[analyze] pair={pair_id} mode={claims['meta']['data_mode']} context={res['context_mode']}")
    print(f"[analyze] excess_flip_rate = {claims['excess_flip_rate.value']} "
          f"(95% CI [{claims['excess_flip_rate.ci_low']}, {claims['excess_flip_rate.ci_high']}])")
    print(f"[analyze] prevalence: marginal_shift={claims['prevalence.marginal_shift']} "
          f"churn={claims['prevalence.churn']} cohen_kappa={claims['prevalence.cohen_kappa']}")
    if res["context_mode"] == "placeholder":
        print("[analyze] WARNING: context_mode=placeholder — decisions were made on empty "
              "prompts; run capture/build_inputs.py and re-capture for a valid experiment.")
    print(f"[analyze] wrote {_OUT}")
    return 0


def _mock_flag(pair_id: str) -> bool:
    p = _RAW / f"runs_{pair_id}_v_old.csv"
    try:
        import csv
        with p.open() as f:
            row = next(csv.DictReader(f))
        return (row.get("mode", "").upper() == "MOCK") or ("mock" in row.get("rationale", "").lower())
    except Exception:
        return False


def _r(x, nd=4):
    return round(x, nd) if isinstance(x, (int, float)) else x


if __name__ == "__main__":
    sys.exit(main())
