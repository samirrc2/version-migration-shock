"""Fill paper/manuscript.md placeholders {{pair:claim_key}} from the per-pair
claims_<pair>.json files and write paper/manuscript_filled.md. Every number in the
manuscript therefore comes from the deterministic claims files, never typed by hand.
Exits nonzero if any placeholder cannot be resolved."""
from __future__ import annotations
import json, re, sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "paper" / "manuscript.md"
_DST = _ROOT / "paper" / "manuscript_filled.md"


def main() -> int:
    if not _SRC.exists():
        print("[fill] paper/manuscript.md missing"); return 2
    text = _SRC.read_text()
    cache: dict[str, dict] = {}
    unresolved = []
    pending = []
    # robustness numbers that may legitimately await data (e.g. the temperature sweep)
    SOFT_PREFIXES = ("tempsweep.",)

    def _load_pair(pair):
        d = {}
        cf = _ROOT / f"claims_{pair}.json"
        if cf.exists():
            d.update(json.loads(cf.read_text()))
        tf = _ROOT / f"tempsweep_{pair}.json"
        if tf.exists():
            ts = json.loads(tf.read_text())
            d["tempsweep.sign_stable"] = ts.get("sign_stable")
            for row in ts.get("by_temperature", []):
                t = int(round(row["T"] * 10))
                for src, dst in (("excess", "excess"), ("ci_low", "ci_low"), ("ci_high", "ci_high")):
                    v = row.get(src)
                    d[f"tempsweep.{dst}_T{t:02d}"] = round(v, 4) if isinstance(v, (int, float)) else v
        return d

    def repl(m):
        pair, key = m.group(1), m.group(2)
        if pair not in cache:
            cache[pair] = _load_pair(pair)
        c = cache[pair]
        if key not in c or c[key] is None:
            if key.startswith(SOFT_PREFIXES):
                pending.append(f"{pair}:{key}")
                return "(pending)"
            unresolved.append(f"{pair}:{key}")
            return m.group(0)
        return str(c[key])

    filled = re.sub(r"\{\{([a-z_]+):([a-zA-Z0-9_.]+)\}\}", repl, text)
    _DST.write_text(filled)
    if pending:
        print(f"[fill] {len(set(pending))} robustness numbers pending (marked '(pending)'): "
              f"{', '.join(sorted(set(pending)))}")
    if unresolved:
        print(f"[fill] {len(set(unresolved))} REQUIRED placeholders unresolved (analyze that pair first):")
        for u in sorted(set(unresolved)):
            print("   -", u)
        print(f"[fill] wrote {_DST} with unresolved markers")
        return 1
    print(f"[fill] wrote {_DST} — all required placeholders resolved"
          + (f" ({len(set(pending))} robustness pending)" if pending else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
