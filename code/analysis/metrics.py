"""Paired cross-version metrics (pure functions over rows of the capture CSVs).
The unit is a single-model decision per (ticker, date, replicate). Under
cell_parity seeding, v_old and v_new share the seed at each cell/replicate, so
matched-replicate differences isolate the version.

Primary endpoint:
    excess_flip_rate = cross_version_flip_rate - within_version_flip_rate
where the within-version rate is Paper 2's own noise floor from replicate
disagreement inside each version."""
from __future__ import annotations
import csv, sys
from collections import defaultdict, Counter
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "config"))
import taskcfg

DIRECTIONS = tuple(taskcfg.CATEGORIES)
POS = dict(taskcfg.ORDINAL)


def load_rows(path: str | Path) -> list[dict]:
    with open(path) as f:
        return [r for r in csv.DictReader(f) if r.get("ok") == "True"]


def _key(r):
    return (r["ticker"], r["date"], int(r["replicate"]))


def index_by_cell_rep(rows):
    return {_key(r): r for r in rows}


def within_version_flip_rate(rows) -> tuple[float, int]:
    """Fraction of within-version replicate pairs (same cell, different seed) whose
    direction differs, over all cells with >=2 replicates."""
    by_cell = defaultdict(list)
    for r in rows:
        by_cell[(r["ticker"], r["date"])].append(r["direction"])
    diff = tot = 0
    for _cell, dirs in by_cell.items():
        for a, b in combinations(dirs, 2):
            tot += 1
            diff += (a != b)
    return (diff / tot if tot else 0.0), tot


def paired(rows_old, rows_new):
    """Matched (ticker,date,replicate) rows present in both versions."""
    io, inw = index_by_cell_rep(rows_old), index_by_cell_rep(rows_new)
    keys = sorted(set(io) & set(inw))
    return [(k, io[k], inw[k]) for k in keys]


def cross_version_flip_rate(pairs) -> tuple[float, int]:
    if not pairs:
        return 0.0, 0
    flips = sum(1 for _k, o, n in pairs if o["direction"] != n["direction"])
    return flips / len(pairs), len(pairs)


def conviction_shift(pairs) -> tuple[float, int]:
    ds = [int(n["conviction"]) - int(o["conviction"]) for _k, o, n in pairs
          if o["conviction"] and n["conviction"]]
    return (sum(ds) / len(ds) if ds else 0.0), len(ds)


def implied_turnover(pairs) -> dict:
    """BUY/HOLD/SELL -> +1/0/-1. Per name |dpos| in {0,1,2}; portfolio turnover
    fraction = mean(|dpos|)/2 (share of a fully-rebalanced book)."""
    dpos = [abs(POS[n["direction"]] - POS[o["direction"]]) for _k, o, n in pairs]
    if not dpos:
        return {"mean_abs_dpos": 0.0, "turnover_fraction": 0.0, "n": 0}
    m = sum(dpos) / len(dpos)
    return {"mean_abs_dpos": m, "turnover_fraction": m / 2.0, "n": len(dpos)}


def dose_response_by_conviction(pairs) -> dict:
    """Cross-version flip rate bucketed by v_old conviction. Retained as a
    secondary/robustness view only: the models emit near-constant conviction, so
    this proxy is typically degenerate — see dose_response_by_instability."""
    buckets = defaultdict(lambda: [0, 0])
    for _k, o, n in pairs:
        c = int(o["conviction"]) if o["conviction"] else 0
        buckets[c][1] += 1
        buckets[c][0] += (o["direction"] != n["direction"])
    table = {c: {"flip_rate": v[0] / v[1] if v[1] else 0.0, "n": v[1]}
             for c, v in sorted(buckets.items())}
    xs, ys, ws = [], [], []
    for c, v in table.items():
        xs.append(c); ys.append(v["flip_rate"]); ws.append(v["n"])
    slope = _wls_slope(xs, ys, ws) if len(set(xs)) >= 2 else None
    return {"table": table, "slope_per_conviction_point": slope,
            "n_distinct_conviction": len(table)}


def within_cell_instability(rows) -> dict:
    """{(ticker,date): instability in [0,1]} for one version. 0 = the model is
    unanimous across its own replicate seeds; higher = more split. This is a
    model-internal, conviction-free proxy for proximity to the decision boundary."""
    by_cell = defaultdict(list)
    for r in rows:
        by_cell[(r["ticker"], r["date"])].append(r["direction"])
    out = {}
    for cell, dirs in by_cell.items():
        n = len(dirs)
        out[cell] = 0.0 if n < 2 else 1.0 - max(Counter(dirs).values()) / n
    return out


def dose_response_by_instability(pairs, rows_old) -> dict:
    """Cross-version flip rate as a function of v_old within-cell instability.
    Hypothesis: migration flips concentrate where the model was already internally
    unstable across its own seeds (near-boundary cells). Buckets: stable (v_old
    unanimous) vs unstable (v_old split). Also a weighted continuous slope."""
    inst = within_cell_instability(rows_old)
    buckets = {"stable": [0, 0], "unstable": [0, 0]}
    cellflip = defaultdict(lambda: [0, 0])
    for (tk, dt, _r), o, n in pairs:
        cell = (tk, dt)
        b = "stable" if inst.get(cell, 0.0) == 0.0 else "unstable"
        flip = 1 if o["direction"] != n["direction"] else 0
        buckets[b][1] += 1; buckets[b][0] += flip
        cellflip[cell][1] += 1; cellflip[cell][0] += flip
    table = {b: {"flip_rate": v[0] / v[1] if v[1] else 0.0, "n": v[1]}
             for b, v in buckets.items()}
    contrast = table["unstable"]["flip_rate"] - table["stable"]["flip_rate"]
    xs, ys, ws = [], [], []
    for cell, (f, t) in cellflip.items():
        xs.append(inst.get(cell, 0.0)); ys.append(f / t if t else 0.0); ws.append(t)
    slope = _wls_slope(xs, ys, ws) if len(set(xs)) >= 2 else None
    return {"table": table, "unstable_minus_stable": contrast,
            "slope_per_instability": slope}


def transition_matrix(pairs) -> dict:
    m = {a: {b: 0 for b in DIRECTIONS} for a in DIRECTIONS}
    for _k, o, n in pairs:
        m[o["direction"]][n["direction"]] += 1
    return m


def cohen_kappa(pairs) -> float | None:
    """Chance-corrected agreement between v_old and v_new directions on matched
    cells. Unlike the raw flip rate, this is not inflated by the marginal
    (prevalence) shift — it answers 'do the two versions agree beyond chance?'"""
    n = len(pairs)
    if n == 0:
        return None
    agree = sum(1 for _k, o, x in pairs if o["direction"] == x["direction"])
    po = agree / n
    old = Counter(o["direction"] for _k, o, _x in pairs)
    new = Counter(x["direction"] for _k, _o, x in pairs)
    pe = sum((old[d] / n) * (new[d] / n) for d in DIRECTIONS)
    return 1.0 if abs(1 - pe) < 1e-12 else (po - pe) / (1 - pe)


def agreement_statistics(pairs) -> dict:
    """Chance-corrected agreement between v_old and v_new under three estimators
    (Cohen kappa, Scott pi, Gwet AC1). If all three agree in sign/magnitude the
    result is not an artifact of one statistic's chance model (Paper 1 s5.2 analog)."""
    n = len(pairs)
    if n == 0:
        return {"observed_agreement": None, "cohen_kappa": None, "scott_pi": None, "gwet_ac1": None}
    po = sum(1 for _k, o, x in pairs if o["direction"] == x["direction"]) / n
    old = {d: sum(1 for _k, o, _x in pairs if o["direction"] == d) / n for d in DIRECTIONS}
    new = {d: sum(1 for _k, _o, x in pairs if x["direction"] == d) / n for d in DIRECTIONS}
    pbar = {d: (old[d] + new[d]) / 2 for d in DIRECTIONS}
    pe_cohen = sum(old[d] * new[d] for d in DIRECTIONS)
    pe_scott = sum(pbar[d] ** 2 for d in DIRECTIONS)
    K = len(DIRECTIONS)
    pe_gwet = (1.0 / (K - 1)) * sum(pbar[d] * (1 - pbar[d]) for d in DIRECTIONS)

    def kap(pe):
        return 1.0 if abs(1 - pe) < 1e-12 else (po - pe) / (1 - pe)
    return {"observed_agreement": po, "cohen_kappa": kap(pe_cohen),
            "scott_pi": kap(pe_scott), "gwet_ac1": kap(pe_gwet)}


def prevalence_decomposition(pairs) -> dict:
    """Separate the gross flip rate into (a) the marginal/prevalence shift that a
    change in the version's default stance forces, and (b) genuine per-cell churn
    beyond that. gross = marginal_shift + churn. Addresses the kappa-paradox: a big
    flip rate driven purely by 'the new version is more bullish' is marginal_shift,
    not reconsideration."""
    n = len(pairs)
    if n == 0:
        return {"n": 0}
    old = Counter(o["direction"] for _k, o, _x in pairs)
    new = Counter(x["direction"] for _k, _o, x in pairs)
    gross = sum(1 for _k, o, x in pairs if o["direction"] != x["direction"]) / n
    marginal = 0.5 * sum(abs(new[d] - old[d]) for d in DIRECTIONS) / n
    return {
        "n": n,
        "gross_flip_rate": gross,
        "marginal_shift": marginal,
        "churn": gross - marginal,
        "marginals_v_old": {d: old[d] / n for d in DIRECTIONS},
        "marginals_v_new": {d: new[d] / n for d in DIRECTIONS},
        "cohen_kappa": cohen_kappa(pairs),
    }


def flip_by_stratum(pairs, sectors: dict) -> dict:
    """Cross-version flip rate by GICS sector and by analysis date."""
    tk_sector = {t: sec for sec, ts in sectors.items() for t in ts}
    by_sec = defaultdict(lambda: [0, 0])
    by_date = defaultdict(lambda: [0, 0])
    for (tk, dt, _r), o, x in pairs:
        f = 1 if o["direction"] != x["direction"] else 0
        s = tk_sector.get(tk, "Unknown")
        by_sec[s][1] += 1; by_sec[s][0] += f
        by_date[dt][1] += 1; by_date[dt][0] += f
    mk = lambda dd: {k: {"flip_rate": v[0] / v[1] if v[1] else 0.0, "n": v[1]}
                     for k, v in sorted(dd.items())}
    return {"by_sector": mk(by_sec), "by_date": mk(by_date)}


def _wls_slope(xs, ys, ws):
    sw = sum(ws)
    if sw == 0:
        return None
    mx = sum(w * x for w, x in zip(ws, xs)) / sw
    my = sum(w * y for w, y in zip(ws, ys)) / sw
    num = sum(w * (x - mx) * (y - my) for w, x, y in zip(ws, xs, ys))
    den = sum(w * (x - mx) ** 2 for w, x in zip(ws, xs))
    return (num / den) if den else None

# --- Reviewer-requested estimand work (R1.1/R2.1, R1.2) --------------------------

def repeat_call_flip_rate(rows_main, rows_repeat) -> dict:
    """Same-seed repeat-call disagreement within one version.

    The primary noise floor compares DIFFERENT replicate seeds inside a version, while the
    cross-version flip rate compares the SAME nominal seed across versions. Both referees
    asked whether the former is the right counterfactual for the latter. This function
    supplies the matched alternative: it pairs each (ticker, date, replicate) row in the main
    capture against the independently timed re-capture that carries the identical seed, so
    seed, cell, replicate index, temperature and version are all held fixed and only the call
    occasion differs. Rows whose recorded seed does not match are skipped rather than counted,
    so the statistic is exactly a same-seed repeat.
    """
    main = {_key(r): r for r in rows_main}
    diff = tot = 0
    for r in rows_repeat:
        k = _key(r)
        m = main.get(k)
        if m is None or m.get("seed") != r.get("seed"):
            continue
        tot += 1
        diff += (m["direction"] != r["direction"])
    return {"flip_rate": (diff / tot if tot else None), "n_pairs": tot, "n_differing": diff}


def total_variation_distance(pairs) -> dict:
    """Total variation distance between the two versions' marginal label distributions.

    This answers a different question from the flip rate and the two are not
    interchangeable (R1.2). TVD measures how far the *aggregate mix* of ratings moved; it is
    a property of the two distributions and is insensitive to which company moved. The
    cross-version flip rate measures the probability that a *particular* decision changes at
    cutover, which is the operational quantity for a deployment. A migration can score high
    on one and low on the other: a permutation of labels across companies leaves TVD at zero
    while flipping most decisions, and a uniform shift of a subset moves TVD without
    touching the rest of the book.
    """
    if not pairs:
        return {"tvd": None, "n": 0}
    n = len(pairs)
    po = Counter(o["direction"] for _k, o, _n in pairs)
    pn = Counter(nw["direction"] for _k, _o, nw in pairs)
    # Summation order must be fixed. Iterating a set of string keys varies between processes
    # under hash randomisation, which changes the last bits of the total and breaks the
    # byte-identical reproduction this repository depends on. The declared category order is
    # used, with any unexpected label appended in sorted order rather than silently dropped.
    cats = list(DIRECTIONS)
    cats += sorted((set(po) | set(pn)) - set(cats))
    tvd = 0.5 * sum(abs(pn.get(c, 0) / n - po.get(c, 0) / n) for c in cats)
    return {"tvd": tvd, "n": n,
            "marginals_v_old": {c: po.get(c, 0) / n for c in cats},
            "marginals_v_new": {c: pn.get(c, 0) / n for c in cats},
            "categories": cats}


def restrict_pairs_to_cells(pairs, cells) -> list:
    """Subset of matched pairs whose (ticker, date) is in `cells`."""
    keep = set(cells)
    return [(k, o, n) for (k, o, n) in pairs if (k[0], k[1]) in keep]


def restrict_pairs_excluding_sectors(pairs, sectors: dict, exclude) -> list:
    """Matched pairs with the named GICS sectors removed."""
    tk_sector = {t: sec for sec, ts in sectors.items() for t in ts}
    ex = set(exclude)
    return [(k, o, n) for (k, o, n) in pairs if tk_sector.get(k[0], "Unknown") not in ex]
