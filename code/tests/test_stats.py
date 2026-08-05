"""Unit tests for the inferential layer (analysis/stats.py).

Runnable two ways:
    python3 tests/test_stats.py
    python3 -m pytest tests/
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "analysis"))
sys.path.insert(0, str(_ROOT / "config"))
import stats as S


def _row(tk, rep, direction):
    return {"ticker": tk, "date": "d1", "replicate": str(rep), "direction": direction,
            "conviction": "3", "ok": "True"}


def test_wilson_ci_bounds():
    lo, hi = S.wilson_ci(5, 10)
    assert 0.0 <= lo < 0.5 < hi <= 1.0
    assert S.wilson_ci(0, 0) == (None, None)


def test_excess_equals_cross_minus_within():
    # old: every ticker unanimous within version (floor 0); new: half the cells flip
    tickers = [f"T{i}" for i in range(8)]
    old = [_row(t, r, "SAFE") for t in tickers for r in range(2)]
    new = [_row(t, r, "SAFE" if int(t[1:]) % 2 == 0 else "DISTRESS") for t in tickers for r in range(2)]
    import metrics as M
    pairs = M.paired(old, new)
    boot = S.cluster_bootstrap_excess(pairs, old, new, draws=200, seed=42)
    assert abs(boot["point"] - (boot["cross"] - boot["within"])) < 1e-9
    assert boot["within"] == 0.0  # unanimous within each version
    assert boot["n_tickers"] == 8


def test_noise_floor_report_structure():
    tickers = [f"T{i}" for i in range(6)]
    old = [_row(t, r, "SAFE") for t in tickers for r in range(2)]
    new = [_row(t, r, "DISTRESS" if int(t[1:]) < 3 else "SAFE") for t in tickers for r in range(2)]
    import metrics as M
    pairs = M.paired(old, new)
    rep = S.noise_floor_report(pairs, old, new, draws=200, seed=42)
    for k in ("old", "new", "pooled", "max", "min"):
        assert k in rep["floors"]
    # conservative (max) floor gives an excess no larger than the pooled-floor excess
    assert rep["excess_by_floor"]["max"] <= rep["excess_by_floor"]["pooled"] + 1e-9


def test_mcnemar_symmetry_gives_high_p():
    # no asymmetric drift toward the label -> not significant
    pairs = [(("A", "d", 0), _row("A", 0, "SAFE"), _row("A", 0, "SAFE"))]
    res = S.mcnemar_directional(pairs)
    assert res["p_value"] == 1.0 and res["n_discordant"] == 0


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"[test_stats] {len(fns)} passed")


if __name__ == "__main__":
    _run()
