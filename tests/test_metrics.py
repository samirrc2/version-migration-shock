"""Unit tests for the paired cross-version metrics (analysis/metrics.py).

Runnable two ways:
    python3 tests/test_metrics.py      # plain asserts, no pytest needed
    python3 -m pytest tests/           # if pytest is installed
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "analysis"))
sys.path.insert(0, str(_ROOT / "config"))
import metrics as M


def _row(tk, dt, rep, direction):
    return {"ticker": tk, "date": dt, "replicate": str(rep), "direction": direction,
            "conviction": "3", "ok": "True"}


def test_within_version_flip_rate():
    # one cell, 3 replicates all agree -> floor 0
    rows = [_row("A", "d1", i, "SAFE") for i in range(3)]
    rate, n = M.within_version_flip_rate(rows)
    assert n == 3 and rate == 0.0
    # one cell, replicates split 2 SAFE / 1 DISTRESS -> 2 of 3 pairs differ
    rows = [_row("A", "d1", 0, "SAFE"), _row("A", "d1", 1, "SAFE"), _row("A", "d1", 2, "DISTRESS")]
    rate, n = M.within_version_flip_rate(rows)
    assert n == 3 and abs(rate - 2 / 3) < 1e-9


def test_cross_version_flip_rate_and_pairing():
    old = [_row("A", "d1", 0, "SAFE"), _row("A", "d1", 1, "SAFE")]
    new = [_row("A", "d1", 0, "SAFE"), _row("A", "d1", 1, "DISTRESS")]
    pairs = M.paired(old, new)
    assert len(pairs) == 2
    rate, n = M.cross_version_flip_rate(pairs)
    assert n == 2 and abs(rate - 0.5) < 1e-9  # one of two matched cells flips


def test_prevalence_decomposition_gross_equals_marginal_plus_churn():
    # 4 matched cells; new version moves stance -> nonzero marginal + churn
    old = [_row(t, "d", 0, "SAFE") for t in "ABCD"]
    new = [_row("A", "d", 0, "SAFE"), _row("B", "d", 0, "DISTRESS"),
           _row("C", "d", 0, "WATCH"), _row("D", "d", 0, "DISTRESS")]
    pairs = M.paired(old, new)
    dec = M.prevalence_decomposition(pairs)
    assert abs(dec["gross_flip_rate"] - (dec["marginal_shift"] + dec["churn"])) < 1e-9
    assert dec["marginal_shift"] >= 0 and dec["gross_flip_rate"] <= 1.0


def test_cohen_kappa_bounds_and_perfect_agreement():
    rows = [_row(t, "d", 0, "SAFE") for t in "ABCD"]
    pairs = M.paired(rows, rows)
    assert M.cohen_kappa(pairs) == 1.0  # identical labels -> perfect agreement
    for stat in M.agreement_statistics(pairs).values():
        if stat is not None:
            assert -1.0 - 1e-9 <= stat <= 1.0 + 1e-9


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"[test_metrics] {len(fns)} passed")


if __name__ == "__main__":
    _run()
