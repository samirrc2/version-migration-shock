"""Anti-drift build gate. Fails (nonzero exit) if a required claim key is missing,
if any number in a rendered document's CLAIMS block disagrees with claims.json, or
if any unfilled slot token remains. A sentence that contradicts its own table
becomes a build failure, not a referee catch."""
from __future__ import annotations
import json, re, sys
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import code_root, results_dir

_RES = results_dir()
_CLAIMS = _RES / "claims.json"
_SLOTS = code_root() / "config" / "slots.yaml"
_REPORT = _RES / "PILOT_RESULTS.md"


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def main() -> int:
    fails = []
    if not _CLAIMS.exists():
        print("[check] FAIL: claims.json missing")
        return 1
    claims = json.loads(_CLAIMS.read_text())
    slots = yaml.safe_load(_SLOTS.read_text())
    required = slots["required_claims"]
    tol = float(slots.get("tolerance", 0.0005))

    for k in required:
        if k not in claims:
            fails.append(f"missing required claim: {k}")

    # check validates the auto-generated report (always complete). The manuscript's
    # completeness is enforced separately by render/fill_manuscript.py (make paper),
    # since it may legitimately await robustness data (e.g. the temperature sweep).
    for doc in (_REPORT,):
        if not doc.exists():
            continue
        text = doc.read_text()
        for tok in re.findall(r"\{\{([^}]+)\}\}", text):
            fails.append(f"{doc.name}: unfilled slot {{{{{tok}}}}}")
        m = re.search(r"<!-- CLAIMS-START -->(.*?)<!-- CLAIMS-END -->", text, re.S)
        if m:
            for line in m.group(1).strip().splitlines():
                if "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip()
                if k not in claims:
                    fails.append(f"{doc.name}: claim {k} not in claims.json")
                    continue
                cv, rv = _num(claims[k]), _num(v)
                if cv is None or rv is None:
                    if str(claims[k]) != v:
                        fails.append(f"{doc.name}: {k} report={v!r} != claims={claims[k]!r}")
                elif abs(cv - rv) > tol:
                    fails.append(f"{doc.name}: {k} report={rv} != claims={cv} (tol {tol})")

    if fails:
        print(f"[check] FAILED ({len(fails)}):")
        for f in fails:
            print("   -", f)
        return 1
    print(f"[check] OK — {len(required)} required claims present; report matches claims.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
