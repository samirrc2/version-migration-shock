"""Generate manuscript figures from the per-pair claims_<pair>.json files (falls
back to claims.json). Writes PNGs to paper/figures/ (single source for LaTeX).
Pure: no data capture."""
from __future__ import annotations
import json, sys
from pathlib import Path

from decimal import Decimal, ROUND_HALF_UP
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _f3(x):
    """Round-half-up to 3 decimals so figure labels match the manuscript tables/body.

    Feed this the full-precision analysis value, never a flat claims_<pair>.json key: those
    are already rounded to four decimals, and rounding again to three double-rounds. That is
    how the excess-flip interval came to be labelled [0.077, 0.150] when the bootstrap bound
    is 0.14948571 -- 0.1495 at four decimals, then 0.150 at three, instead of 0.149.
    """
    # Decimal(x), not Decimal(str(x)): repr() already shortens the double to the fewest
    # digits that round-trip, so str() rounds once before quantize rounds again. The Gemini
    # lower bound is 0.30249999999999999, whose repr is "0.3025" and which then rounds up to
    # 0.303 instead of down to 0.302.
    return str(Decimal(x).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP))


def _exact(c, key, *path):
    """Full-precision value from the detail block, falling back to the rounded flat key."""
    d = c.get("detail")
    for k in path:
        if isinstance(d, dict) and k in d:
            d = d[k]
        elif isinstance(d, list) and isinstance(k, int) and -len(d) <= k < len(d):
            d = d[k]
        else:
            return c[key]
    return d if isinstance(d, (int, float)) and not isinstance(d, bool) else c[key]

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "config"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import repo_root, results_dir
import taskcfg

_ROOT = repo_root()
_RES = results_dir()
_FIG = _ROOT / "paper" / "figures"
PAIRS = ["openai_nano", "gemini_flash"]
_PAIR_LABEL = {"openai_nano": "OpenAI migration", "gemini_flash": "Gemini migration"}


def load_claims():
    out = {}
    for p in PAIRS:
        f = _RES / f"claims_{p}.json"
        if f.exists():
            out[p] = json.loads(f.read_text())
    if not out and (_RES / "claims.json").exists():
        c = json.loads((_RES / "claims.json").read_text())
        out[c["meta"]["pair"]] = c
    return out


def fig_excess_forest(cl):
    fig, ax = plt.subplots(figsize=(6, 2.4))
    ys = list(range(len(cl)))
    # Headroom above the top series and to the right of the widest interval: the value label
    # sits above its marker, and without this the topmost label runs into the title and past
    # the right spine.
    for y, (p, c) in zip(ys, cl.items()):
        v = _exact(c, "excess_flip_rate.value", "excess_flip_rate", "value")
        lo = _exact(c, "excess_flip_rate.ci_low", "excess_flip_rate", "ci", 0)
        hi = _exact(c, "excess_flip_rate.ci_high", "excess_flip_rate", "ci", 1)
        ax.errorbar(v, y, xerr=[[v - lo], [hi - v]], fmt="o", capsize=4, color="#1f4e79")
        ax.annotate(f"{_f3(v)} [{_f3(lo)}, {_f3(hi)}]", (v, y), textcoords="offset points",
                    xytext=(8, 6), fontsize=8)
    ax.axvline(0, ls="--", color="gray", lw=1)
    ax.set_ylim(-0.55, len(ys) - 1 + 0.85)
    lo_all = min(_exact(c, "excess_flip_rate.ci_low", "excess_flip_rate", "ci", 0) for c in cl.values())
    hi_all = max(_exact(c, "excess_flip_rate.ci_high", "excess_flip_rate", "ci", 1) for c in cl.values())
    span = hi_all - min(0.0, lo_all)
    ax.set_xlim(min(0.0, lo_all) - 0.08 * span, hi_all + 0.26 * span)
    ax.set_yticks(ys); ax.set_yticklabels([_PAIR_LABEL.get(p, p) for p in cl])
    ax.set_xlabel("excess flip rate (cross - within), 95% CI")
    ax.set_title("Version-migration excess flip rate by pair")
    fig.tight_layout(); fig.savefig(_FIG / "fig1_excess_forest.png", dpi=150); plt.close(fig)


def fig_prevalence(cl):
    fig, ax = plt.subplots(figsize=(6, 3))
    labels = list(cl); x = range(len(labels)); w = 0.38
    marg = [_exact(cl[p], "prevalence.marginal_shift", "prevalence", "marginal_shift") for p in labels]
    churn = [_exact(cl[p], "prevalence.churn", "prevalence", "churn") for p in labels]
    ax.bar([i - w / 2 for i in x], marg, w, label="marginal (rating-mix) shift", color="#c0504d")
    ax.bar([i + w / 2 for i in x], churn, w, label="residual company-level churn", color="#4f81bd")
    ax.set_xticks(list(x)); ax.set_xticklabels([_PAIR_LABEL.get(l, l) for l in labels])
    ax.set_ylabel("share of decisions"); ax.legend()
    ax.set_title("Marginal shift vs residual company-level churn")
    fig.tight_layout(); fig.savefig(_FIG / "fig2_prevalence.png", dpi=150); plt.close(fig)


def fig_transition(cl):
    dirs = list(taskcfg.CATEGORIES)
    fig, axes = plt.subplots(1, len(cl), figsize=(3.4 * len(cl), 3.1), squeeze=False)
    for ax, (p, c) in zip(axes[0], cl.items()):
        m = c["detail"]["transition_matrix"]
        M = [[m[a][b] for b in dirs] for a in dirs]
        im = ax.imshow(M, cmap="Blues")
        ax.set_xticks(range(3)); ax.set_xticklabels(dirs)
        ax.set_yticks(range(3)); ax.set_yticklabels(dirs)
        ax.set_xlabel("Successor"); ax.set_ylabel("Incumbent")
        ax.set_title(_PAIR_LABEL.get(p, p), fontsize=9)
        for i in range(3):
            for j in range(3):
                ax.text(j, i, M[i][j], ha="center", va="center",
                        color="white" if M[i][j] > max(max(r) for r in M) / 2 else "black", fontsize=8)
    fig.suptitle("Decision transition matrix (Incumbent -> Successor)")
    fig.tight_layout(); fig.savefig(_FIG / "fig3_transition.png", dpi=150); plt.close(fig)


def fig_sector(cl):
    p = next(iter(cl)); sec = cl[p]["detail"]["strata"]["by_sector"]
    labels = list(sec); vals = [sec[s]["flip_rate"] for s in labels]
    fig, ax = plt.subplots(figsize=(7, 3.4))
    ax.barh(labels, vals, color="#4f81bd")
    ax.set_xlabel("cross-version flip rate"); ax.set_title(f"Flip rate by sector ({p})")
    fig.tight_layout(); fig.savefig(_FIG / "fig4_sector.png", dpi=150); plt.close(fig)


def main() -> int:
    cl = load_claims()
    if not cl:
        print("[figures] no claims_*.json found — run analysis first"); return 2
    _FIG.mkdir(parents=True, exist_ok=True)
    fig_excess_forest(cl); fig_prevalence(cl); fig_transition(cl); fig_sector(cl)
    print(f"[figures] wrote fig1-4 to {_FIG} (pairs: {', '.join(cl)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
