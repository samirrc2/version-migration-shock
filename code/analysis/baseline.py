"""Table 1 decomposition: how much do decisions flip when nothing changes (seeds
only) versus when the model version changes. Built entirely from Paper 2's own
captures of both versions (the standalone noise floor)."""
from __future__ import annotations
import metrics as M


def decomposition(rows_old, rows_new) -> dict:
    w_old, n_old = M.within_version_flip_rate(rows_old)
    w_new, n_new = M.within_version_flip_rate(rows_new)
    pairs = M.paired(rows_old, rows_new)
    cross, n_cross = M.cross_version_flip_rate(pairs)
    within_pooled = ((w_old * n_old) + (w_new * n_new)) / (n_old + n_new) if (n_old + n_new) else 0.0
    return {
        "within_version_v_old": {"flip_rate": w_old, "n_pairs": n_old},
        "within_version_v_new": {"flip_rate": w_new, "n_pairs": n_new},
        "within_version_pooled": {"flip_rate": within_pooled, "n_pairs": n_old + n_new},
        "cross_version": {"flip_rate": cross, "n_pairs": n_cross},
        "excess_flip_rate_point": cross - within_pooled,
    }

def matched_baseline(rows_old, rows_new, rep_old, rep_new) -> dict:
    """Sensitivity to the choice of noise floor, using a same-seed repeat-call baseline.

    Referee objection (R1.1, R2.1): the primary floor is built from different-seed replicate
    pairs, whereas the cross-version comparison holds the seed fixed, so the two need not sit
    on a common scale. The repeat captures give a floor constructed the same way as the
    treatment contrast -- same cell, same replicate index, same seed, same temperature, same
    version, different call occasion -- and the primary endpoint is re-formed against it.

    The repeat grid is small (8 tickers x 3 dates x 3 replicates per version), so the floor
    carries a Wilson interval rather than a ticker-cluster bootstrap, and the recomputed
    excess is reported as a point estimate whose uncertainty is dominated by that floor.
    """
    import stats as S
    pairs = M.paired(rows_old, rows_new)
    cross, _n = M.cross_version_flip_rate(pairs)
    ro = M.repeat_call_flip_rate(rows_old, rep_old)
    rn = M.repeat_call_flip_rate(rows_new, rep_new)
    d = ro["n_differing"] + rn["n_differing"]
    t = ro["n_pairs"] + rn["n_pairs"]
    pooled = (d / t) if t else None
    lo, hi = S.wilson_ci(d, t) if t else (None, None)
    return {
        "repeat_floor_v_old": ro,
        "repeat_floor_v_new": rn,
        "repeat_floor_pooled": {"flip_rate": pooled, "n_pairs": t, "n_differing": d,
                                "wilson_ci": [lo, hi]},
        "cross_version_flip_rate": cross,
        "excess_vs_repeat_floor": (cross - pooled) if pooled is not None else None,
        "excess_vs_repeat_floor_ci": ([cross - hi, cross - lo]
                                      if (lo is not None and hi is not None) else None),
    }
