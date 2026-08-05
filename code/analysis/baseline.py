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
