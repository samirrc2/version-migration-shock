"""Temperature-sensitivity robustness (Paper 1 s5.9 analog, EXPLORATORY).

Reads the tagged sweep CSVs runs_<pair>_<version>_T{00,07,10}.csv and reports the
excess flip rate (with CI) at each temperature. The claim is robust if the sign and
rough magnitude of the effect hold across T; absolute levels may move.

  python analysis/tempsweep.py --pair openai_nano
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "config"))
import metrics as M
import stats as S
import loader as C

_RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
_TAGS = {0.0: "_T00", 0.7: "_T07", 1.0: "_T10"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", required=True)
    args = ap.parse_args()
    cfg = C.load_all()
    temps = cfg["grid"].get("tempsweep_temperatures", [0.0, 0.7, 1.0])
    draws, seed = int(cfg["grid"]["bootstrap_draws"]), int(cfg["grid"]["bootstrap_seed"])
    rows = []
    for T in temps:
        tag = _TAGS.get(T, f"_T{int(T*10):02d}")
        fo = _RAW / f"runs_{args.pair}_v_old{tag}.csv"
        fn = _RAW / f"runs_{args.pair}_v_new{tag}.csv"
        if not (fo.exists() and fn.exists()):
            print(f"  ! T={T}: missing {fo.name}/{fn.name} — run the sweep capture first")
            continue
        ro, rn = M.load_rows(fo), M.load_rows(fn)
        pairs = M.paired(ro, rn)
        boot = S.cluster_bootstrap_excess(pairs, ro, rn, draws=draws, seed=seed)
        rows.append({"T": T, "excess": boot["point"], "ci_low": boot["ci_low"],
                     "ci_high": boot["ci_high"], "cross": boot["cross"],
                     "within": boot["within"], "n": len(pairs)})
    out = {"pair": args.pair, "by_temperature": rows,
           "sign_stable": all(r["excess"] is not None and r["excess"] > 0 for r in rows) if rows else None}
    dest = Path(__file__).resolve().parent.parent / f"tempsweep_{args.pair}.json"
    dest.write_text(json.dumps(out, indent=2))
    def f(x):
        return "n/a" if x is None else f"{x:.4f}"
    print(f"[tempsweep] pair={args.pair}")
    for r in rows:
        warn = "  (LOW N - incomplete capture?)" if r["n"] < 12 else ""
        print(f"  T={r['T']}: excess={f(r['excess'])} CI[{f(r['ci_low'])},{f(r['ci_high'])}] (n={r['n']}){warn}")
    print(f"[tempsweep] sign_stable={out['sign_stable']} -> {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
