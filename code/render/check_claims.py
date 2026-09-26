"""Anti-drift build gate. Fails (nonzero exit) if a required claim key is missing,
if any number in a rendered document's CLAIMS block disagrees with claims.json, or
if any unfilled slot token remains. A sentence that contradicts its own table
becomes a build failure, not a referee catch."""
from __future__ import annotations
import json, re, sys
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import code_root, repo_root, results_dir

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

    # The manuscript itself was not gated: every decimal in it was checked by hand. Six of the
    # referee-driven revisions change numbers in the paper, so the check is extended to main.tex.
    # Any figure in the paper must sit within tolerance of some value the frozen analysis produced,
    # or be listed in the allowlist below with a reason (model names, thresholds, DOIs and the like
    # are not analysis outputs).
    # The manuscript cites results from every migration pair, so this check can only run once
    # all of them have been analysed. It is invoked per pair, and on a fresh clone the first
    # pair's run has no sibling claims file yet, which would fail every number belonging to the
    # other pair. Deferring until all are present makes the gate order-independent; reproduce.sh
    # runs it once more after the loop so it is never silently skipped.
    manuscript_scanned = manuscript_allowed = None
    _PAIRS = ("openai_nano", "gemini_flash")
    _have = [(_RES / f"claims_{q}.json").exists() for q in _PAIRS]
    tex = repo_root() / "paper" / "main.tex"
    if tex.exists() and not all(_have):
        missing = [q for q, h in zip(_PAIRS, _have) if not h]
        print(f"[check] manuscript check deferred: awaiting {', '.join(missing)}")
    elif tex.exists():
        pool = set()

        def _harvest(v):
            if isinstance(v, dict):
                for x in v.values():
                    _harvest(x)
            elif isinstance(v, list):
                for x in v:
                    _harvest(x)
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                a = abs(float(v))
                pool.add(a)
                pool.add(a * 100.0)

        for pair in ("openai_nano", "gemini_flash"):
            f = _RES / f"claims_{pair}.json"
            if f.exists():
                _harvest(json.loads(f.read_text()))
            f = _RES / f"tempsweep_{pair}.json"
            if f.exists():
                _harvest(json.loads(f.read_text()))

        # Each allowance is anchored to the context it applies in, so a figure is excused only
        # where it is genuinely external. A bare value list excused the same digits everywhere,
        # including a result that happened to print them.
        allow = {}
        for _e in (yaml.safe_load(_SLOTS.read_text()).get("manuscript_number_allowlist") or []):
            if not isinstance(_e, dict) or not {"value", "context", "reason"} <= set(_e):
                fails.append(f"slots.yaml: allowlist entry {_e!r} needs value, context and reason")
                continue
            allow.setdefault(str(_e["value"]), []).append((_e["context"], _e["reason"]))
        # A LaTeX comment starts at an UNESCAPED %. Stripping at every % also truncated each
        # line at its first "95\%", which hid 39 of the manuscript's 203 numbers from this
        # check -- nearly all of them confidence-interval bounds, the figures most likely to
        # drift. The lookbehind keeps an escaped percent sign as content.
        body = re.sub(r"(?<!\\)%.*", "", tex.read_text())
        i, j = body.find("\\begin{abstract}"), body.find("\\begin{thebibliography}")
        if i >= 0 and j > i:
            body = body[i:j]
        # A figure matches if some analysis output agrees with it to the precision the paper
        # actually prints. Writing 0.60 does not assert 0.600000, so the comparison rounds the
        # pool to the paper's own decimal places rather than demanding exact equality.
        # Two number forms appear in the paper: 0.123 in prose and .123 in the tables, which
        # are set without a leading zero to save column width. Only the first was scanned, so
        # 50 figures -- about a fifth of the manuscript, including Table 2's whole
        # confidence-interval row -- were never checked, and Table 2 kept the superseded
        # [.077,.150] long after the prose was corrected to 0.149.
        scanned = allowed = 0
        for m in re.finditer(r"(?<![\w.])(\d*\.\d+)(?![\w])", body):
            lit = m.group(1)
            lit_value = "0" + lit if lit.startswith(".") else lit
            window = body[max(0, m.start() - 60):m.end() + 60]
            rules = allow.get(lit, []) if lit == lit_value else \
                allow.get(lit, []) + allow.get(lit_value, [])
            if rules:
                if any(re.search(cx, window) for cx, _why in rules):
                    allowed += 1
                    continue
                fails.append(f"main.tex: {lit} is allowlisted only in the context "
                             f"{'/'.join(cx for cx, _ in rules)!r}, but occurs here outside it: "
                             f"...{re.sub(chr(92)+'s+', ' ', window)}...")
                continue
            scanned += 1
            tail = body[m.end():m.end() + 12]
            if tail.startswith("\\textwidth") or tail.startswith("\\linewidth"):
                continue            # a LaTeX column width, not a result
            dp = len(lit_value.split(".")[1])
            v = float(lit_value)
            if not any(round(q, dp) == v for q in pool):
                fails.append(f"main.tex: {lit} traces to no analysis output "
                             f"(add to manuscript_number_allowlist with a reason if external)")
        manuscript_scanned, manuscript_allowed = scanned, allowed
        if scanned == 0:
            fails.append("manuscript scan matched no figures at all; the gate is vacuous")

    if fails:
        print(f"[check] FAILED ({len(fails)}):")
        for f in fails:
            print("   -", f)
        return 1
    # State the coverage, not just the verdict: a gate that prints only "OK" cannot be told
    # apart from one whose scan matched nothing.
    if manuscript_scanned is not None:
        print(f"[check] manuscript: {manuscript_scanned} figure(s) traced to the frozen "
              f"analysis, {manuscript_allowed} allowlisted as external")
    print(f"[check] OK — {len(required)} required claims present; report matches claims.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
