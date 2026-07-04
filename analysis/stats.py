"""Inferential layer: cluster bootstrap (resample tickers) for the excess-flip-rate
CI, and a McNemar-style paired test for directional drift."""
from __future__ import annotations
import math, sys
import random
from collections import defaultdict
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "config"))
import taskcfg
import metrics as M


def cross_flips_by_ticker(pairs):
    out = defaultdict(list)
    for (tk, _d, _r), o, n in pairs:
        out[tk].append(1 if o["direction"] != n["direction"] else 0)
    return out


def within_flips_by_ticker(rows_old, rows_new):
    out = defaultdict(list)
    for rows in (rows_old, rows_new):
        by_cell = defaultdict(list)
        for r in rows:
            by_cell[(r["ticker"], r["date"])].append(r["direction"])
        for (tk, _d), dirs in by_cell.items():
            for a, b in combinations(dirs, 2):
                out[tk].append(1 if a != b else 0)
    return out


def _rate(by_ticker, tickers):
    num = den = 0
    for tk in tickers:
        v = by_ticker.get(tk)
        if v:
            num += sum(v); den += len(v)
    return (num / den) if den else None


def excess_flip_point(cross_bt, within_bt, tickers):
    c = _rate(cross_bt, tickers)
    w = _rate(within_bt, tickers)
    if c is None or w is None:
        return None, c, w
    return c - w, c, w


def cluster_bootstrap_excess(pairs, rows_old, rows_new, draws=2000, seed=42):
    """95% CI on excess_flip_rate = cross - within, resampling tickers with
    replacement (tickers are the clustering unit)."""
    cross_bt = cross_flips_by_ticker(pairs)
    within_bt = within_flips_by_ticker(rows_old, rows_new)
    tickers = sorted(set(cross_bt) | set(within_bt))
    n = len(tickers)
    pt, c0, w0 = excess_flip_point(cross_bt, within_bt, tickers)
    rng = random.Random(seed)
    deltas = []
    for _ in range(draws):
        samp = [tickers[rng.randrange(n)] for _ in range(n)]
        e, _c, _w = excess_flip_point(cross_bt, within_bt, samp)
        if e is not None:
            deltas.append(e)
    deltas.sort()
    if len(deltas) < 20:
        return {"point": pt, "ci_low": None, "ci_high": None,
                "cross": c0, "within": w0, "n_tickers": n, "n_valid": len(deltas)}
    return {"point": pt,
            "ci_low": deltas[int(0.025 * len(deltas))],
            "ci_high": deltas[int(0.975 * len(deltas)) - 1],
            "cross": c0, "within": w0, "n_tickers": n, "n_valid": len(deltas)}


def cluster_bootstrap_scalar(pairs, fn, draws=2000, seed=42):
    """95% CI for any scalar statistic fn(pairs_subset), resampling tickers with
    replacement (the clustering unit). Returns point + CI."""
    by_tk = defaultdict(list)
    for p in pairs:
        by_tk[p[0][0]].append(p)
    tickers = sorted(by_tk)
    n = len(tickers)
    point = fn(pairs)
    rng = random.Random(seed)
    vals = []
    for _ in range(draws):
        samp = []
        for _i in range(n):
            samp.extend(by_tk[tickers[rng.randrange(n)]])
        v = fn(samp)
        if v is not None:
            vals.append(v)
    vals.sort()
    if len(vals) < 20:
        return {"point": point, "ci_low": None, "ci_high": None}
    return {"point": point,
            "ci_low": vals[int(0.025 * len(vals))],
            "ci_high": vals[int(0.975 * len(vals)) - 1]}


def wilson_ci(k: int, n: int, z: float = 1.96):
    """Wilson score 95% CI for a proportion k/n (used for accuracy hit-rates)."""
    if n == 0:
        return (None, None)
    phat = k / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = (z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n))) / denom
    return (center - half, center + half)


def _chi2_sf_df1(x: float) -> float:
    return math.erfc(math.sqrt(x / 2.0)) if x > 0 else 1.0


def mcnemar_directional(pairs) -> dict:
    """Paired test of asymmetric drift toward the task's drift label (BUY for the
    directional task, DISTRESS for credit). b = old not-label -> new label; c = the
    reverse. Continuity-corrected McNemar chi-square, df=1."""
    label = taskcfg.DRIFT_LABEL
    b = c = 0
    for _k, o, n in pairs:
        ob = o["direction"] == label
        nb = n["direction"] == label
        if (not ob) and nb:
            b += 1
        elif ob and (not nb):
            c += 1
    disc = b + c
    if disc == 0:
        return {"b": b, "c": c, "chi2": 0.0, "p_value": 1.0, "n_discordant": 0}
    chi2 = (abs(b - c) - 1) ** 2 / disc
    return {"b": b, "c": c, "chi2": chi2, "p_value": _chi2_sf_df1(chi2), "n_discordant": disc}
