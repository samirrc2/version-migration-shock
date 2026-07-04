"""Generate manuscript figures from the per-pair claims_<pair>.json files (falls
back to claims.json). Writes PNGs to figures/. Pure: no data capture."""
from __future__ import annotations
import json, sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "config"))
import taskcfg

_ROOT = Path(__file__).resolve().parent.parent
_FIG = _ROOT / "figures"
PAIRS = ["openai_nano", "gemini_flash"]


def load_claims():
    out = {}
    for p in PAIRS:
        f = _ROOT / f"claims_{p}.json"
        if f.exists():
            out[p] = json.loads(f.read_text())
    if not out and (_ROOT / "claims.json").exists():
        c = json.loads((_ROOT / "claims.json").read_text())
        out[c["meta"]["pair"]] = c
    return out


def fig_excess_forest(cl):
    fig, ax = plt.subplots(figsize=(6, 2.4))
    ys = list(range(len(cl)))
    for y, (p, c) in zip(ys, cl.items()):
        v, lo, hi = c["excess_flip_rate.value"], c["excess_flip_rate.ci_low"], c["excess_flip_rate.ci_high"]
        ax.errorbar(v, y, xerr=[[v - lo], [hi - v]], fmt="o", capsize=4, color="#1f4e79")
        ax.annotate(f"{v:.3f} [{lo:.3f}, {hi:.3f}]", (v, y), textcoords="offset points",
                    xytext=(8, 6), fontsize=8)
    ax.axvline(0, ls="--", color="gray", lw=1)
    ax.set_yticks(ys); ax.set_yticklabels(list(cl))
    ax.set_xlabel("excess flip rate (cross - within), 95% CI")
    ax.set_title("Version-migration excess flip rate by pair")
    fig.tight_layout(); fig.savefig(_FIG / "fig1_excess_forest.png", dpi=150); plt.close(fig)


def fig_prevalence(cl):
    fig, ax = plt.subplots(figsize=(6, 3))
    labels = list(cl); x = range(len(labels)); w = 0.38
    marg = [cl[p]["prevalence.marginal_shift"] for p in labels]
    churn = [cl[p]["prevalence.churn"] for p in labels]
    ax.bar([i - w / 2 for i in x], marg, w, label="marginal shift (stance)", color="#c0504d")
    ax.bar([i + w / 2 for i in x], churn, w, label="churn (reconsideration)", color="#4f81bd")
    ax.set_xticks(list(x)); ax.set_xticklabels(labels)
    ax.set_ylabel("share of decisions"); ax.legend()
    ax.set_title("Prevalence shift vs genuine churn")
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
        ax.set_xlabel("v_new"); ax.set_ylabel("v_old"); ax.set_title(p, fontsize=9)
        for i in range(3):
            for j in range(3):
                ax.text(j, i, M[i][j], ha="center", va="center",
                        color="white" if M[i][j] > max(max(r) for r in M) / 2 else "black", fontsize=8)
    fig.suptitle("Decision transition matrix (v_old -> v_new)")
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
