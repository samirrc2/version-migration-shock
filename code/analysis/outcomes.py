"""Accuracy analysis, task-aware (EXPLORATORY per amendments log).

Scores each version's majority-vote label per cell against the objective ground
truth in data/outcomes/ground_truth.json: exact category match for label tasks
(credit-health Altman band, earnings surprise), or directional sign match for the
forward-return task (abstain label excluded). Reports per-version hit-rate with
Wilson 95% CIs and the flip-conditional new-minus-old hit-rate with a bootstrap CI.
"""
from __future__ import annotations
import json, random, sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "config"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import repo_root
import taskcfg
import stats as S

_OUTC = repo_root() / "data" / "outcomes" / "ground_truth.json"


def available() -> bool:
    return _OUTC.exists()


def _majority_by_cell(rows):
    by = defaultdict(list)
    for r in rows:
        by[(r["ticker"], r["date"])].append(r["direction"])
    out = {}
    for cell, labels in by.items():
        c = Counter(labels)
        out[cell] = sorted(c.items(), key=lambda kv: (-kv[1], taskcfg.CATEGORIES.index(kv[0])))[0][0]
    return out


def _hit(direction, gt):
    """(scored, hit) for one cell."""
    if gt is None:
        return (False, False)
    if taskcfg.GROUND_TRUTH == "forward_return":
        if direction == taskcfg.ABSTAIN_LABEL:
            return (False, False)
        pred = 1 if direction == "BUY" else -1
        return (True, pred == gt)
    if taskcfg.ABSTAIN_LABEL and direction == taskcfg.ABSTAIN_LABEL:
        return (False, False)
    return (True, direction == gt)


def _rate(mv, signs):
    hits = n = 0
    for cell, direction in mv.items():
        scored, hit = _hit(direction, signs.get(f"{cell[0]}|{cell[1]}"))
        if scored:
            n += 1; hits += 1 if hit else 0
    return (hits / n if n else None), n


_FIN_SECTORS = ("Financials", "Real Estate")


def _label_quality(mv, signs, tk_sector) -> dict:
    """Class-balanced scoring for a label task (credit-health). Reports balanced
    accuracy (mean per-class recall), macro-F1, the majority-class baseline (the
    accuracy of always predicting the most common ground-truth class), per-sector
    hit-rate, and hit-rate with Altman-inappropriate sectors (Financials, Real
    Estate) excluded. Guarded to label ground truths; returns {} otherwise."""
    if taskcfg.GROUND_TRUTH == "forward_return":
        return {}
    classes = list(taskcfg.CATEGORIES)
    conf = {g: {"tp": 0, "fp": 0, "support": 0} for g in classes}
    gt_dist = Counter()
    by_sector = defaultdict(lambda: [0, 0])
    ex_hits = ex_n = 0
    for cell, pred in mv.items():
        gt = signs.get(f"{cell[0]}|{cell[1]}")
        if gt is None:
            continue
        if taskcfg.ABSTAIN_LABEL and pred == taskcfg.ABSTAIN_LABEL:
            continue
        gt_dist[gt] += 1
        if gt in conf:
            conf[gt]["support"] += 1
            if pred == gt:
                conf[gt]["tp"] += 1
        if pred != gt and pred in conf:
            conf[pred]["fp"] += 1
        sec = tk_sector.get(cell[0], "Unknown")
        by_sector[sec][1] += 1
        by_sector[sec][0] += 1 if pred == gt else 0
        if sec not in _FIN_SECTORS:
            ex_n += 1
            ex_hits += 1 if pred == gt else 0
    recalls, f1s = [], []
    for g in classes:
        sup, tp, fp = conf[g]["support"], conf[g]["tp"], conf[g]["fp"]
        if sup == 0:
            continue
        rec = tp / sup
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        recalls.append(rec)
        f1s.append(0.0 if (prec + rec) == 0 else 2 * prec * rec / (prec + rec))
    tot = sum(gt_dist.values())
    return {
        "balanced_accuracy": (sum(recalls) / len(recalls)) if recalls else None,
        "macro_f1": (sum(f1s) / len(f1s)) if f1s else None,
        "majority_class_baseline": (max(gt_dist.values()) / tot) if tot else None,
        "n_scored": tot,
        "hit_rate_ex_financials": (ex_hits / ex_n) if ex_n else None,
        "n_scored_ex_financials": ex_n,
        "by_sector": {s: {"hit_rate": v[0] / v[1] if v[1] else None, "n": v[1]}
                      for s, v in sorted(by_sector.items())},
    }


def accuracy(rows_old, rows_new, sectors: dict | None = None) -> dict:
    if not _OUTC.exists():
        return {"available": False}
    signs = json.loads(_OUTC.read_text())
    tk_sector = {t: sec for sec, ts in (sectors or {}).items() for t in ts}
    mv_o, mv_n = _majority_by_cell(rows_old), _majority_by_cell(rows_new)
    ho, no = _rate(mv_o, signs)
    hn, nn = _rate(mv_n, signs)
    ql_o, ql_n = _label_quality(mv_o, signs, tk_sector), _label_quality(mv_n, signs, tk_sector)

    flip_cells = []
    for cell in set(mv_o) & set(mv_n):
        if mv_o[cell] == mv_n[cell]:
            continue
        gt = signs.get(f"{cell[0]}|{cell[1]}")
        if gt is None:
            continue
        flip_cells.append((cell[0], mv_o[cell], mv_n[cell], gt))
    fo, no_f = _flip_rate(flip_cells, "old")
    fn, nn_f = _flip_rate(flip_cells, "new")
    delta = (fn - fo) if (fo is not None and fn is not None) else None
    ci = _flip_delta_ci(flip_cells)
    return {
        "available": True, "ground_truth": taskcfg.GROUND_TRUTH,
        "hit_rate_old": ho, "n_scored_old": no, "ci_old": list(S.wilson_ci(round((ho or 0) * no), no)),
        "hit_rate_new": hn, "n_scored_new": nn, "ci_new": list(S.wilson_ci(round((hn or 0) * nn), nn)),
        "flip_hit_rate_old": fo, "flip_hit_rate_new": fn,
        "flip_conditional_new_minus_old": delta, "flip_conditional_ci": ci,
        "n_flip_scored_old": no_f, "n_flip_scored_new": nn_f,
        "quality_old": ql_o, "quality_new": ql_n,
        "restricted": _restricted_quality(mv_o, mv_n, signs, tk_sector),
        "quality_ci": _quality_ci(mv_o, mv_n, signs, tk_sector),
    }


def _restricted_quality(mv_o, mv_n, signs, tk_sector) -> dict:
    """Class-balanced scoring on the Altman-appropriate subset (R2.4).

    The manuscript previously reported only a raw hit rate for the subset that drops
    Financials and Real Estate, while arguing elsewhere that imbalanced classes require
    balanced accuracy and macro-F1. The referee is right that the same two statistics have to
    be given here, because this is the subset on which the Z'' reference model is defensible
    and it is where the OpenAI direction reverses.
    """
    keep_o = {c: v for c, v in mv_o.items() if tk_sector.get(c[0], "Unknown") not in _FIN_SECTORS}
    keep_n = {c: v for c, v in mv_n.items() if tk_sector.get(c[0], "Unknown") not in _FIN_SECTORS}
    qo = _label_quality(keep_o, signs, tk_sector)
    qn = _label_quality(keep_n, signs, tk_sector)
    ho, no = _rate(keep_o, signs)
    hn, nn = _rate(keep_n, signs)
    return {
        "excluded_sectors": list(_FIN_SECTORS),
        "hit_rate_old": ho, "hit_rate_new": hn, "n_scored_old": no, "n_scored_new": nn,
        "balanced_accuracy_old": qo.get("balanced_accuracy"),
        "balanced_accuracy_new": qn.get("balanced_accuracy"),
        "macro_f1_old": qo.get("macro_f1"), "macro_f1_new": qn.get("macro_f1"),
        "majority_class_baseline": qo.get("majority_class_baseline"),
    }


def _quality_ci(mv_o, mv_n, signs, tk_sector, draws=2000, seed=42) -> dict:
    """Ticker-clustered bootstrap intervals for balanced accuracy and macro-F1 (R2.5).

    These aggregate comparisons were reported as bare point estimates while the
    flip-conditional analysis carried an interval, leaving their inferential status unstated.
    Tickers are the resampling unit, as everywhere else in the paper, and the paired change
    (new minus old) is resampled on the same draw so the two versions stay coupled.
    """
    cells = sorted(set(mv_o) & set(mv_n))
    by_tk = defaultdict(list)
    for c in cells:
        by_tk[c[0]].append(c)
    tks = sorted(by_tk)
    if len(tks) < 2:
        return {}

    def stat(sel):
        so = {c: mv_o[c] for c in sel}
        sn = {c: mv_n[c] for c in sel}
        a, b = _label_quality(so, signs, tk_sector), _label_quality(sn, signs, tk_sector)
        return (a.get("balanced_accuracy"), b.get("balanced_accuracy"),
                a.get("macro_f1"), b.get("macro_f1"))

    pt = stat(cells)
    rng = random.Random(seed)
    acc = {k: [] for k in ("ba_old", "ba_new", "ba_delta", "f1_old", "f1_new", "f1_delta")}
    for _ in range(draws):
        sel = []
        for _i in range(len(tks)):
            sel.extend(by_tk[tks[rng.randrange(len(tks))]])
        bo, bn, fo, fn = stat(sel)
        if None in (bo, bn, fo, fn):
            continue
        acc["ba_old"].append(bo); acc["ba_new"].append(bn); acc["ba_delta"].append(bn - bo)
        acc["f1_old"].append(fo); acc["f1_new"].append(fn); acc["f1_delta"].append(fn - fo)

    def ci(v):
        if len(v) < 20:
            return [None, None]
        v = sorted(v)
        return [v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1]]

    return {
        "n_tickers": len(tks), "draws": draws,
        "balanced_accuracy_old": pt[0], "balanced_accuracy_old_ci": ci(acc["ba_old"]),
        "balanced_accuracy_new": pt[1], "balanced_accuracy_new_ci": ci(acc["ba_new"]),
        "balanced_accuracy_delta": (pt[1] - pt[0]) if None not in pt[:2] else None,
        "balanced_accuracy_delta_ci": ci(acc["ba_delta"]),
        "macro_f1_old": pt[2], "macro_f1_old_ci": ci(acc["f1_old"]),
        "macro_f1_new": pt[3], "macro_f1_new_ci": ci(acc["f1_new"]),
        "macro_f1_delta": (pt[3] - pt[2]) if None not in pt[2:] else None,
        "macro_f1_delta_ci": ci(acc["f1_delta"]),
    }


def _flip_rate(cells, which):
    hits = n = 0
    for _tk, od, nd, gt in cells:
        scored, hit = _hit(od if which == "old" else nd, gt)
        if scored:
            n += 1; hits += 1 if hit else 0
    return (hits / n if n else None), n


def _flip_delta(cells):
    fo, _ = _flip_rate(cells, "old")
    fn, _ = _flip_rate(cells, "new")
    return (fn - fo) if (fo is not None and fn is not None) else None


def _flip_delta_ci(cells, draws=2000, seed=42):
    by_tk = defaultdict(list)
    for r in cells:
        by_tk[r[0]].append(r)
    tks = sorted(by_tk)
    if len(tks) < 2:
        return [None, None]
    rng = random.Random(seed)
    vals = []
    for _ in range(draws):
        samp = []
        for _i in range(len(tks)):
            samp.extend(by_tk[tks[rng.randrange(len(tks))]])
        v = _flip_delta(samp)
        if v is not None:
            vals.append(v)
    vals.sort()
    if len(vals) < 20:
        return [None, None]
    return [vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]]
