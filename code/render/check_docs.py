#!/usr/bin/env python3
"""Trace every reported figure in the non-manuscript documents to the frozen analysis.

check_claims.py gates paper/main.tex. Nothing gated the README or the reviewer response,
which is how the README kept [0.077, 0.150] and [0.303, 0.458] after the manuscript was
corrected to 0.149 and 0.302: the numbers lived in documents no check looked at.

Same rule as the manuscript gate -- a figure matches if some analysis output agrees with it
to the precision the document actually prints -- with a per-document allowlist for values
that are not analysis outputs (grid sizes, dates, version strings, counts of files).

Usage:  python3 code/render/check_docs.py
Exit:   0 all traced, 1 something untraceable, 2 analysis outputs absent
"""
from __future__ import annotations
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import repo_root, results_dir

ROOT = repo_root()
RES = results_dir()
PAIRS = ("openai_nano", "gemini_flash")

# Figures that are not analysis outputs. Each needs a reason.
ALLOW = {
    "README.md": {
        "10.24433": "Code Ocean DOI prefix",
        "3.13": "upper bound of the accepted Python range",
        "1.40": "openai package minimum version",
        "8.7": "size on disk of data/raw, in MB",
        "4.7": "size on disk of docs/, in MB",
        "2.5": "model version string (gemini-2.5-flash)",
        "3.5": "model version string (gemini-3.5-flash)",
        "5.4": "model version string (gpt-5.4-nano)",
        "3.10": "minimum Python version",
        "3.12": "Code Ocean image Python version",
        "2874343.1": "Code Ocean DOI fragment",
        "0.1": "illustrative tolerance in prose",
    },
    "submission/response_to_reviewers.txt": {
        "2.5": "model version string",
        "3.5": "model version string",
        "5.4": "model version string",
        "39991.0": "manuscript ID fragment",
    },
}

DOCS = ["README.md", "submission/response_to_reviewers.txt"]


def pool():
    """Every numeric value the frozen analysis produced, and its percentage form."""
    out = set()

    def harvest(v):
        if isinstance(v, dict):
            for x in v.values():
                harvest(x)
        elif isinstance(v, list):
            for x in v:
                harvest(x)
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            # Signed. This used to store abs(), which meant the gate could not tell +0.140
            # from -0.140: a confidence interval printed as [0.140, -0.028] traced cleanly.
            f = float(v)
            out.add(f)
            out.add(f * 100.0)
            # Prose legitimately states a magnitude ("a decline of 0.080"), so keep those too;
            # inside a bracketed interval the signed form is required (see check_interval_order
            # and the interval-aware branch of the document scan).
            out.add(abs(f))
            out.add(abs(f) * 100.0)

    found = 0
    for pair in PAIRS:
        for name in (f"claims_{pair}.json", f"tempsweep_{pair}.json"):
            f = RES / name
            if f.exists():
                harvest(json.loads(f.read_text()))
                found += 1
    return out, found


SUP = str.maketrans("\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079\u207b",
                    "0123456789-")


def scientific(text):
    """Values written as mantissa x 10^exponent, which a bare decimal scan splits in two.

    The README prints McNemar p as 5.67x10^-18. Scanning for decimals alone sees "5.67",
    which matches nothing, and the exponent disappears. Reconstructing the value lets the
    figure be checked instead of excused.
    """
    out = []
    for m in re.finditer(r"(\d+\.\d+)\s*(?:\u00d7|x)\s*10\s*([\u2070-\u209f\u00b9\u00b2\u00b3\u207b]+|\^?-?\d+)",
                         text):
        exp = m.group(2).translate(SUP).lstrip("^")
        try:
            out.append((m.group(1), float(m.group(1)) * 10 ** int(exp), m.start()))
        except ValueError:
            continue
    return out


# ── README expected-results table, bound row by row ──────────────────────────────────────
# The pool test above asks only whether a figure appears somewhere in the analysis. That is
# too weak for this table: changing a CI bound from 0.149 to 0.152 passed, because 0.152
# happens to round-match an unrelated bootstrap statistic. Each row is therefore tied to the
# claim keys it reports, in the order the cell prints them.
TABLE = [
    ("Matched cells",                          ["n_matched_cells"]),
    ("Excess flip rate (primary)",             ["excess_flip_rate.value"]),
    ("95% CI (cluster bootstrap)",             ["excess_flip_rate.ci_low", "excess_flip_rate.ci_high"]),
    ("cross-version flip",                     ["cross_version_flip_rate.value"]),
    ("within-version noise floor (pooled)",    ["within_version_flip_rate.value"]),
    ("Excess vs conservative max floor",       ["noise.excess_conservative",
                                                "noise.excess_conservative_ci_low",
                                                "noise.excess_conservative_ci_high"]),
    ("Marginal (rating-mix) shift",            ["prevalence.marginal_shift"]),
    ("Churn (genuine)",                        ["prevalence.churn"]),
    ("Cohen \u03ba / Scott \u03c0 / Gwet AC1", ["prevalence.cohen_kappa", "agreement.scott_pi",
                                                "agreement.gwet_ac1"]),
    ("McNemar drift",                          ["mcnemar.p_display"]),
    ("Balanced accuracy old",                  ["accuracy.balanced_old", "accuracy.balanced_new"]),
    ("Same-seed repeat-call floor (matched)",  ["matched.repeat_floor_pooled",
                                                "matched.repeat_floor_ci_low",
                                                "matched.repeat_floor_ci_high"]),
    ("Excess vs matched floor (sensitivity)",  ["matched.excess_vs_repeat_floor"]),
    ("Label-distribution distance (TVD)",      ["distance.tvd", "distance.tvd_ci_low",
                                                "distance.tvd_ci_high"]),
    ("Excess on the 24 robustness cells",      ["subgrid.excess_on_subgrid_cells"]),
    ("Restricted balanced acc. old",           ["restricted.balanced_old", "restricted.balanced_new"]),
    ("Restricted macro-F1 old",                ["restricted.macro_f1_old", "restricted.macro_f1_new"]),
    ("Balanced-acc. \u0394 (95% CI)",           ["quality.balanced_delta",
                                                "quality.balanced_delta_ci_low",
                                                "quality.balanced_delta_ci_high"]),
    ("Macro-F1 \u0394 (95% CI)",                ["quality.macro_f1_delta",
                                                "quality.macro_f1_delta_ci_low",
                                                "quality.macro_f1_delta_ci_high"]),
    ("Macro-F1 old\u2192new (baseline",          ["accuracy.macro_f1_old", "accuracy.macro_f1_new"]),
]

NUM = re.compile(r"-?\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:\u00d7|x)\s*10\s*[\u2070-\u209f\u00b9\u00b2\u00b3\u207b^\-\d]+)?")


def _val(tok):
    tok = tok.replace(",", "").strip()
    m = re.match(r"^(-?\d+(?:\.\d+)?)\s*(?:\u00d7|x)\s*10\s*(.+)$", tok)
    if m:
        return float(m.group(1)) * 10 ** int(m.group(2).translate(SUP).lstrip("^"))
    return float(tok)


def check_table(readme, claims):
    """Each printed cell against the claim key it reports."""
    rows = [l for l in readme.split("\n") if l.startswith("|")]
    checks = 0
    fails = []
    matched = 0
    used = set()
    for label, keys in TABLE:
        # first unused row: "Macro-F1 old" is a substring of "Restricted macro-F1 old",
        # so an unqualified search binds the wrong row and reports a phantom mismatch
        row = next((r for r in rows if label.lower() in r.lower() and r not in used), None)
        if row is not None:
            used.add(row)
        if row is None:
            fails.append(f"README table: no row for {label!r}")
            continue
        matched += 1
        cells = [c.strip() for c in row.strip("|").split("|")]
        if len(cells) < 3:
            fails.append(f"README table: row {label!r} has {len(cells)} cells")
            continue
        for cell, pair in zip(cells[1:3], ("openai_nano", "gemini_flash")):
            printed = [x for x in NUM.findall(cell) if x.strip(" -")]
            if len(printed) != len(keys):
                fails.append(f"README table [{label} / {pair}]: prints {len(printed)} "
                             f"value(s), expected {len(keys)} ({keys})")
                continue
            for tok, key in zip(printed, keys):
                checks += 1
                want = claims[pair].get(key)
                if want is None:
                    fails.append(f"README table [{label} / {pair}]: claim key {key} absent")
                    continue
                got = _val(tok)
                dp = len(tok.split(".")[1].split()[0]) if "." in tok else 0
                if dp == 0:
                    # A relative tolerance on an integer count permits any value at all:
                    # 3,491 passed against 3,490. Counts must match exactly.
                    ok = got == float(want)
                elif re.search(r"(?:\u00d7|x)\s*10", tok):
                    # A p-value written as 5.67x10^-18: compare the mantissas at the printed
                    # precision, so 5.68 fails while the stored 5.6716 still passes.
                    w = float(want)
                    scale = 10 ** math.floor(math.log10(abs(w))) if w else 1.0
                    ok = round(w / scale, dp) == round(got / scale, dp)
                else:
                    # A cell printing d decimals asserts the stored value rounds to it:
                    # 0.5167 legitimately prints as 0.517, but 0.5168 does not.
                    ok = round(float(want), dp) == got
                if not ok:
                    fails.append(f"README table [{label} / {pair}]: prints {tok} "
                                 f"but {key} = {want}")
    return checks, matched, fails


# ── response-letter citations ────────────────────────────────────────────────────────────
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]


def manuscript_map():
    """IEEE numbering for every section and subsection, plus the table count."""
    body = re.sub(r"(?<!\\)%.*", "", (ROOT / "paper" / "main.tex").read_text(encoding="utf-8"))
    body = body[body.find("\\section{Introduction}"):]
    sec = sub = 0
    out = {}
    for m in re.finditer(r"\\(section|subsection)\{([^}]*)\}", body):
        if m.group(1) == "section":
            sec += 1; sub = 0
            out[ROMAN[sec - 1]] = m.group(2)
        else:
            sub += 1
            out[f"{ROMAN[sec - 1]}-{chr(64 + sub)}"] = m.group(2)
    return out, len(re.findall(r"\\begin\{table\*?\}", body))


def check_citations():
    """Every Section/Table the reviewer response points at must exist and be named correctly.

    A response letter that cites a section which moved, or quotes a title that has since been
    reworded, tells the editor to look somewhere the text no longer is. Quoted titles are
    compared with trailing punctuation removed: the letter writes
    "...Repeat-Call Sensitivity," with the comma inside the quotation marks, which is correct
    and is not a mismatch.
    """
    sections, n_tables = manuscript_map()
    letter = (ROOT / "submission" / "response_to_reviewers.txt").read_text(encoding="utf-8")
    checks = 0
    fails = []
    for ref in re.findall(r"Section ([IVX]+(?:-[A-Z])?)", letter):
        checks += 1
        if ref not in sections:
            fails.append(f"response letter: Section {ref} does not exist in the manuscript")
    for ref, quoted in re.findall(r'Section ([IVX]+(?:-[A-Z])?),\s*"([^"]+)"', letter):
        checks += 1
        want = sections.get(ref, "")
        if quoted.rstrip(",.;:").strip() != want.strip():
            fails.append(f"response letter: Section {ref} is titled {want!r}, "
                         f"but the letter quotes {quoted!r}")
    for ref in re.findall(r"Table (\d+)", letter):
        checks += 1
        if not 1 <= int(ref) <= n_tables:
            fails.append(f"response letter: Table {ref} cited, paper has {n_tables}")
    return checks, fails


# Quotations in the author's own blocks that are deliberately NOT in the manuscript, because
# the letter is quoting text the revision removed. Each needs a reason; anything else quoted as
# the paper's wording must actually be the paper's wording.
REMOVED_QUOTES = {
    "cannot be explained solely by sampling variability":
        "the superseded claim, quoted in R2 C8 to say it was replaced with a narrower statement",
}


# Wording the revision committed to removing, with the concern that prompted each. The letter
# tells the editor these claims are gone; nothing checked the manuscript for their return, and
# two of them came back in sections other than the one the reviewer had quoted -- III-B kept an
# "alone would produce" reading of the same claim, and III-C asserted a floor ordering the
# paper's own next paragraph contradicts for Gemini.
RETIRED = {
    r"sampling variability alone":
        "R2 C8: the letter says the 'solely/alone' exclusion was replaced by a "
        "defined-baseline statement",
    r"cannot be explained solely":
        "R2 C8: the superseded claim itself",
    r"rules out sampling|excludes sampling":
        "R2 C8: the same exclusion in other words",
    r"at least as large as the same-seed":
        "false for Gemini (different-seed 0.008 < same-seed repeat 0.014); the next "
        "paragraph prints both",
}


def signed(text, m):
    """The value a figure actually prints, minus sign included.

    The scan pattern matches digits only, so "-0.140" was read as 0.140 and checked against the
    pool as a positive number. A sign flip therefore passed: the letter could print a confidence
    interval as [0.140, -0.028] -- not even an ordered interval -- and the gate saw two values it
    recognised. A leading "-" counts only where it can be a sign rather than a range dash, so
    "7.7--14.9" still reads as two positive numbers.
    """
    lit = m.group(1)
    val = float("0" + lit if lit.startswith(".") else lit)
    i = m.start() - 1
    while i >= 0 and text[i] == " ":
        i -= 1
    # A "-" is a sign only where a number can start. Inside an identifier it is a hyphen:
    # reading "gemini-2.5-flash" as -2.5 turned three model names into negative numbers.
    if i >= 0 and text[i] == "-" and (i == 0 or text[i - 1] in "([{,=:> \t\n$"):
        return -val, "-" + lit
    return val, lit


def check_interval_order(label, text):
    """Printed intervals must run low to high.

    Independent of any pool lookup: [0.140, -0.028] is wrong on its face, and this catches it
    even when both magnitudes exist somewhere in the analysis.
    """
    checks, fails = 0, []
    for m in re.finditer(r"\[\s*(-?\d*\.\d+)\s*,\s*(-?\d*\.\d+)\s*\]", text):
        checks += 1
        lo, hi = (float("0" + x if x.startswith(".") else
                        ("-0" + x[1:] if x.startswith("-.") else x)) for x in m.groups())
        if lo > hi:
            fails.append(f"{label}: interval {m.group(0)} runs high to low")
    return checks, fails


def check_docx_parity():
    """The Word file must carry every image the LaTeX source includes.

    IEEE Access wants the manuscript in both formats and expects them to match. The DOCX is
    built by a preprocessor that rewrites environments pandoc cannot read, so an environment it
    does not know about degrades quietly: when author photographs were added, the biography
    rewrite still only matched the no-photo form, pandoc dropped both portraits, and the Word
    file kept the biographies without them. Counting images in both files catches that.
    """
    import zipfile
    tex = (ROOT / "paper" / "main.tex").read_text(encoding="utf-8")
    want = len(re.findall(r"\\includegraphics", tex))
    docx = ROOT / "submission" / "main_manuscript.docx"
    if not docx.exists():
        return 0, ["submission/main_manuscript.docx missing; cannot compare formats"]
    with zipfile.ZipFile(docx) as z:
        media = [n for n in z.namelist() if n.startswith("word/media/")]
        body = z.read("word/document.xml").decode("utf-8", "replace")
    fails = []
    if len(media) != want:
        fails.append(f"main.tex includes {want} image(s); main_manuscript.docx embeds "
                     f"{len(media)}. The DOCX preprocessor dropped some.")
    for leak in ("includegraphics", "IEEEbiography", "\\begin{"):
        if leak.replace("\\", "\\") in body:
            fails.append(f"main_manuscript.docx contains raw LaTeX ({leak!r}); the preprocessor "
                         f"left an environment unconverted")
    for who in ("Samir Chincholikar", "Robin Chawla"):
        if who not in body:
            fails.append(f"main_manuscript.docx is missing the biography for {who}")
    return 1 + len(media) + 2, fails


def check_retired_language():
    """Claims the response letter says were removed must not survive anywhere in the paper.

    A reviewer concern is answered in one section and quietly recreated in another. Checking
    only the section the reviewer quoted is how that survives a full read.
    """
    tex = re.sub(r"\s+", " ", (ROOT / "paper" / "main.tex").read_text(encoding="utf-8"))
    checks, fails = 0, []
    for pat, why in RETIRED.items():
        checks += 1
        for m in re.finditer(pat, tex, re.I):
            fails.append(f"paper/main.tex still contains {m.group(0)!r} — {why}; "
                         f"context: ...{tex[max(0, m.start()-70):m.end()+70]}...")
    return checks, fails


def check_letter_content():
    """The letter's own figures and quotations, bound to the manuscript.

    check_citations only asks whether a cited section exists, and the figure scan only asks
    whether a number occurs somewhere in the analysis. Neither notices a letter that tells the
    editor the paper now reports a value it does not report, or that quotes wording the paper
    does not use. The reviewer's own blocks are excluded: those are their words, and may quote
    the version being replaced.
    """
    letter = (ROOT / "submission" / "response_to_reviewers.txt").read_text(encoding="utf-8")
    tex = (ROOT / "paper" / "main.tex").read_text(encoding="utf-8")
    flat = re.sub(r"\{,\}", ",", tex)                 # 14{,}400 -> 14,400

    def norm(s):
        s = re.sub(r"\\[a-zA-Z]+\s*", "", s)
        s = re.sub(r"[{}$~\\]", "", s)
        s = s.replace("``", '"').replace("''", '"').replace("--", "-").replace(",", "")
        return re.sub(r"\s+", " ", s).strip().lower()

    flat_norm = norm(tex)
    parts = re.split(r"(?m)^(Reviewer comment:|Author response:|Author action:)\s*$", letter)
    author = "\n".join(parts[i + 1] for i in range(1, len(parts), 2)
                       if parts[i] != "Reviewer comment:")
    checks, fails = 0, []

    for m in re.finditer(r"(?<![\w.])(\d+\.\d+)(?![\w])", author):
        checks += 1
        _v, shown = signed(author, m)
        if shown.lstrip("-") not in flat or (shown.startswith("-") and shown not in
                                             flat.replace("$-", "-").replace("−", "-")):
            ctx = re.sub(r"\s+", " ", author[max(0, m.start() - 60):m.end() + 25]).strip()
            fails.append(f"response letter reports {shown}, which does not appear in "
                         f"paper/main.tex: ...{ctx}...")

    for q in re.findall(r'"([^"]{15,200})"', author):
        checks += 1
        key = re.sub(r"\s+", " ", q).strip().rstrip(" .,")
        if key in REMOVED_QUOTES:
            continue
        if norm(q).rstrip(" .,") not in flat_norm:
            fails.append(f"response letter quotes {key[:70]!r} as the paper's wording; "
                         f"paper/main.tex does not contain it")
    return checks, fails


def check_sr2602():
    """Table 5's guidance citations, against archived copies of the two letters.

    The table gives each provision as a section number and title, in its own column per
    letter: column 2 is SR 11-7, column 3 is SR 26-2. Every (number, title) pair printed must
    be one the archived document actually contains, so a renamed section, a title moved to
    the wrong number, or one letter's title placed in the other's column all fail.
    """
    docs = {}
    for key, name in (("sr117", "SR1107.json"), ("sr2602", "SR2602.json")):
        path = ROOT / "docs" / "provenance" / name
        if not path.exists():
            return 0, [f"docs/provenance/{name} missing; guidance citations unverifiable"]
        prov = json.loads(path.read_text(encoding="utf-8"))
        byname = {}
        for s in prov["sections"]:
            num, title = s.split(".", 1)
            byname.setdefault(num.strip(), set()).add(title.strip())
        for num, subs in prov.get("subsections", {}).items():
            for sname in subs:
                byname.setdefault(num.strip(), set()).add(sname.strip())
        docs[key] = byname

    tex = (ROOT / "paper" / "main.tex").read_text(encoding="utf-8")
    i = tex.find("Mapping vendor version migration")
    if i < 0:
        return 0, ["Table 5 not found in paper/main.tex"]
    block = tex[tex.find(r"\toprule", i):tex.find(r"\bottomrule", i)]
    checks, fails = 0, []
    rows = 0
    for line in block.split(r"\\"):
        # split on unescaped & only: a cell may contain "responsibility \& contingency"
        cells = [c.strip() for c in re.split(r"(?<!\\)&", line)]
        if len(cells) != 5 or cells[1].strip() in ("SR 11-7",) or not cells[0]:
            continue
        rows += 1
        for cell, key, col in ((cells[1], "sr117", "SR 11-7"), (cells[2], "sr2602", "SR 26-2")):
            flat = re.sub(r"\s+", " ", cell.replace(r"\addlinespace", "")).strip()
            pairs = re.findall(r"\\S\s*([IVX]+)\s+([^;]+?)(?=\s*;\s*\\S|\s*$)", flat)
            if not pairs:
                fails.append(f"Table 5, {col} column: no 'section number + title' found in "
                             f"{flat[:60]!r}")
                continue
            for num, title in pairs:
                checks += 1
                known = docs[key].get(num, set())
                if not known:
                    fails.append(f"Table 5, {col} column: section {num} does not exist in "
                                 f"the archived {col}")
                elif title.strip() not in known:
                    fails.append(f"Table 5, {col} column: section {num} is printed as "
                                 f"{title.strip()!r}, but the archived {col} calls it "
                                 f"{sorted(known)}")
    if rows == 0:
        fails.append("Table 5: no data rows parsed; the checker and the table have diverged")
    return checks, fails

FOOTNOTE = ("3",)   # SR 26-2's scope carve-out for generative and agentic AI


def check_letter_table5():
    """The response letter's account of Table 5, bound to the table itself.

    The letter tells the reviewer what Table 5 now contains. Nothing checked that, so when the
    table was restructured the letter kept describing the layout before it -- it promised a
    section number and title for every entry while listing only the SR 26-2 side, and named
    four row concepts for a table that has five. Two bindings, because the letter went stale
    in both ways: the concepts it names must be exactly the table's first column, and any
    provision it spells out longhand must be a provision the table actually prints.
    """
    tex = (ROOT / "paper" / "main.tex").read_text(encoding="utf-8")
    i = tex.find("Mapping vendor version migration")
    if i < 0:
        return 0, ["Table 5 not found in paper/main.tex"]
    block = tex[tex.find(r"\toprule", i):tex.find(r"\bottomrule", i)]
    concepts, titles, ncols = [], set(), 0
    for line in block.split(r"\\"):
        cells = [c.strip() for c in re.split(r"(?<!\\)&", line)]
        if len(cells) != 5 or not cells[0]:
            continue
        head = re.sub(r"\s+", " ",
                      re.sub(r"\\(toprule|midrule|addlinespace)", "", cells[0])).strip()
        if cells[1].strip() == "SR 11-7":
            ncols = len(cells)          # the header row states the table's shape
            continue
        concepts.append(head.lower())
        for cell in (cells[1], cells[2]):
            for num, title in re.findall(r"\\S\s*([IVX]+)\s+([^;&]+?)(?=\s*;\s*\\S|\s*$)",
                                         re.sub(r"\s+", " ", cell)):
                titles.add(f"section {num.lower()}, {title.strip().lower()}")
    if not concepts or not ncols:
        return 0, ["Table 5: header or rows not parsed; checker and table have diverged"]

    cap = re.sub(r"\s+", " ", tex[tex.rfind(r"\caption", 0, i):tex.find(r"\toprule", i)])

    letter = (ROOT / "submission" / "response_to_reviewers.txt").read_text(encoding="utf-8")
    i = letter.find("Reviewer #2, Concern #3")
    blk = re.sub(r"\s+", " ", letter[i:letter.find("Reviewer #2, Concern #4")])
    checks, fails = 0, []

    m = re.search(r"The (?:five|four|three|six) rows are [^:]*: (.+?)\.", blk)
    if not m:
        fails.append("letter no longer lists Table 5's rows; it cannot be bound to the table")
    else:
        named = [re.sub(r"^and ", "", s.strip().lower()) for s in m.group(1).split(";")]
        checks += 1
        if named != concepts:
            fails.append(f"letter names Table 5's rows as {named}, table has {concepts}")
        if len(named) != len(concepts):
            fails.append(f"letter says {len(named)} rows, Table 5 has {len(concepts)}")

    # A provision written out longhand in the letter must be one the table prints. This is what
    # caught nothing before: the letter listed SR 26-2 titles for a table that had gained an
    # SR 11-7 column, and four titles for five rows.
    for m in re.finditer(r"[Ss]ection ([IVX]+), ([A-Z][^.;:]{6,70}?)(?=[.;]|, and | and )", blk):
        checks += 1
        claim = f"section {m.group(1).lower()}, {m.group(2).strip().lower()}"
        if claim not in titles:
            fails.append(f"letter cites {m.group(0)!r} as a Table 5 provision; the table does "
                         f"not print it")
    # The letter and the caption both rest on SR 26-2's footnote 3. "footnote 3" alone names no
    # document and no reviewer can check it, so the letter must attribute it and quote it, and
    # the quotation must be the archived text -- not a paraphrase that drifts toward the claim
    # we want it to support.
    for doc, text in (("letter", blk), ("Table 5 caption", cap)):
        m = re.search(r"footnote[~ ]*(\d+)", text)
        checks += 1
        if not m:
            fails.append(f"{doc}: the scope carve-out is no longer attributed to a footnote")
        elif m.group(1) != FOOTNOTE[0]:
            fails.append(f"{doc}: cites footnote {m.group(1)}; the carve-out is footnote "
                         f"{FOOTNOTE[0]} of SR 26-2")
    prov = json.loads((ROOT / "docs" / "provenance" / "SR2602.json").read_text(encoding="utf-8"))
    archived = re.sub(r"\s+", " ", prov["provisions_cited_by_the_paper"]["footnote_3"]).lower()
    # Only the quotations offered as the guidance's own words: the sentence citing the footnote.
    # Scanning the whole block flagged the section title, which is quoted for a different reason.
    sent = next((s for s in re.split(r"(?<=[.!]) ", blk) if "footnote" in s), "")
    for q in re.findall(r'"([^"]{12,200})"', sent):
        checks += 1
        if re.sub(r"\s+", " ", q).lower().strip(" .") not in archived:
            fails.append(f"letter quotes {q[:60]!r} from the guidance; the archived SR 26-2 "
                         f"footnote {FOOTNOTE[0]} does not contain those words")
    if "not within the scope of this guidance" not in archived:
        fails.append("archived SR 26-2 footnote 3 no longer carries the carve-out language the "
                     "paper's argument rests on")
        checks += 1
    return checks, fails

# ── Table 2, the results table, bound row by row ─────────────────────────────────────────
# The pool test only asks whether a printed figure exists somewhere in the analysis, which is
# not enough for this table: a wrong CI bound can round-match an unrelated bootstrap value.
# It is also the table that carried the superseded [.077,.150] for months, because its
# numbers are set without a leading zero and the manuscript gate never scanned that form.
TABLE2 = [
    (r"95\% CI",                        ["excess_flip_rate.ci_low", "excess_flip_rate.ci_high"]),
    ("cross-version flip",              ["cross_version_flip_rate.value"]),
    ("within-version floor (pooled)",   ["within_version_flip_rate.value"]),
    ("floor old / new",                 ["noise.within_old", "noise.within_new"]),
    (r"excess, $\max$ floor",           ["noise.excess_conservative",
                                         "noise.excess_conservative_ci_low",
                                         "noise.excess_conservative_ci_high"]),
    ("Marginal (rating-mix) shift",     ["prevalence.marginal_shift"]),
    ("Residual company-level churn",    ["prevalence.churn"]),
    ("churn 95",                        ["prevalence.churn_ci_low", "prevalence.churn_ci_high"]),
    ("Gwet",                            ["prevalence.cohen_kappa", "agreement.scott_pi",
                                         "agreement.gwet_ac1"]),
    ("Balanced acc",                    ["accuracy.balanced_old", "accuracy.balanced_new"]),
    ("Macro-F1 old/new",                ["accuracy.macro_f1_old", "accuracy.macro_f1_new"]),
    (r"Flip-cond.\ accuracy",           ["accuracy.flip_conditional_delta"]),
]


def check_table2(claims):
    """Each printed cell of Table 2 against the claim key it reports."""
    tex = (ROOT / "paper" / "main.tex").read_text(encoding="utf-8")
    i = tex.find("Primary and secondary results")
    if i < 0:
        return 0, 0, ["Table 2 not found in paper/main.tex"]
    rows = [re.sub(r"\s+", " ", r).strip()
            for r in tex[tex.find(r"\toprule", i):tex.find(r"\bottomrule", i)].split(r"\\")]
    checks = matched = 0
    fails = []
    used = set()
    for label, keys in TABLE2:
        row = next((r for k, r in enumerate(rows)
                    if label in r and k not in used), None)
        if row is None:
            fails.append(f"Table 2: no row for {label!r}")
            continue
        used.add(rows.index(row))
        matched += 1
        cells = [c.strip() for c in re.split(r"(?<!\\)&", row)]
        if len(cells) != 3:
            fails.append(f"Table 2 [{label}]: {len(cells)} cells, expected 3")
            continue
        for cell, pair in zip(cells[1:3], ("openai_nano", "gemini_flash")):
            printed = re.findall(r"[-+]?\d*\.\d+", cell)
            if len(printed) != len(keys):
                fails.append(f"Table 2 [{label} / {pair}]: prints {len(printed)} value(s), "
                             f"expected {len(keys)} ({keys})")
                continue
            for tok, key in zip(printed, keys):
                checks += 1
                want = claims[pair].get(key)
                if want is None:
                    fails.append(f"Table 2 [{label} / {pair}]: claim key {key} absent")
                    continue
                norm = tok if not tok.lstrip("+-").startswith(".") else \
                    tok.replace(".", "0.", 1) if tok[0] not in "+-" else \
                    tok[0] + "0" + tok[1:]
                dp = len(norm.split(".")[1])
                if round(float(want), dp) != float(norm):
                    fails.append(f"Table 2 [{label} / {pair}]: prints {tok} but {key} = {want}")
    return checks, matched, fails


# The documents this gate reads. A Code Ocean capsule mounts only /code and /data, so in that
# layout none of them are present. That must read as "not checkable here", not as a failure and
# certainly not as a traceback: adding this gate to reproduce.sh without the guard made the
# capsule's Reproducible Run crash on a missing README.md after the analysis had already passed.
INPUTS = ("README.md", "paper/main.tex", "submission/response_to_reviewers.txt")


def main():
    p, found = pool()
    if found == 0:
        print("[docs] analysis outputs absent; run code/reproduce.sh first")
        sys.exit(2)

    absent = [rel for rel in INPUTS if not (ROOT / rel).exists()]
    if absent:
        print(f"[docs] not checkable in this copy: {', '.join(absent)} not published here "
              f"(expected in a /code + /data capsule layout); skipping the documentation gate")
        sys.exit(2)

    checks = 0
    fails = []
    for rel in DOCS:
        path = ROOT / rel
        if not path.exists():
            fails.append(f"{rel}: missing")
            continue
        text = path.read_text(encoding="utf-8")
        if rel.endswith(".md"):
            # fenced code blocks hold shell commands and paths, not reported figures
            text = re.sub(r"```.*?```", " ", text, flags=re.S)
        allow = ALLOW.get(rel, {})
        # check mantissa-and-exponent figures as single values, and take their mantissas out
        # of the plain-decimal scan so they are not double-reported
        consumed = set()
        for lit, value, pos in scientific(text):
            checks += 1
            consumed.add(pos)
            dp = len(lit.split(".")[1])
            if not any(abs(q - value) <= abs(value) * 10 ** -dp for q in p):
                line = text.count("\n", 0, pos) + 1
                fails.append(f"{rel}:{line}: {value:g} traces to no analysis output")
        for m in re.finditer(r"(?<![\w.])(\d+\.\d+)(?![\w])", text):
            if m.start() in consumed:
                continue
            lit = m.group(1)
            if lit in allow:
                continue
            checks += 1
            v, shown = signed(text, m)
            dp = len(lit.split(".")[1])
            # Inside a bracketed interval the sign is part of the claim, so the magnitude form
            # is not accepted there. In running prose a magnitude is legitimate.
            head = text[max(0, m.start() - 40):m.start()]
            in_interval = "[" in head and "]" not in head[head.rfind("["):]
            cand = [q for q in p if round(q, dp) == v]
            if in_interval:
                cand = [q for q in cand if (q < 0) == (v < 0)]
            if not cand:
                line = text.count("\n", 0, m.start()) + 1
                ctx = re.sub(r"\s+", " ", text[max(0, m.start() - 55):m.end() + 35]).strip()
                fails.append(f"{rel}:{line}: {shown} traces to no analysis output — …{ctx}…")

    claims = {q: json.loads((RES / f"claims_{q}.json").read_text()) for q in PAIRS
              if (RES / f"claims_{q}.json").exists()}
    tchecks = tmatched = 0
    if len(claims) == len(PAIRS):
        tchecks, tmatched, tfails = check_table((ROOT / "README.md").read_text(encoding="utf-8"),
                                                claims)
        fails.extend(tfails)
    print(f"[docs] {checks} figures checked across {len(DOCS)} documents "
          f"against {len(p)} analysis values")
    print(f"[docs] {tchecks} README table cells bound to claim keys "
          f"across {tmatched}/{len(TABLE)} rows")
    cchecks, cfails = check_citations()
    fails.extend(cfails)
    print(f"[docs] {cchecks} response-letter citations resolved against the manuscript")
    t2checks = t2matched = 0
    if len(claims) == len(PAIRS):
        t2checks, t2matched, t2fails = check_table2(claims)
        fails.extend(t2fails)
    print(f"[docs] {t2checks} Table 2 cells bound to claim keys across "
          f"{t2matched}/{len(TABLE2)} rows")
    schecks, sfails = check_sr2602()
    fails.extend(sfails)
    print(f"[docs] {schecks} guidance provision name(s) matched to the archived SR 11-7 and "
          f"SR 26-2 documents")
    ichecks = 0
    for rel in DOCS:
        c, f = check_interval_order(rel, (ROOT / rel).read_text(encoding="utf-8"))
        ichecks += c
        fails.extend(f)
    c, f = check_interval_order("paper/main.tex",
                                (ROOT / "paper" / "main.tex").read_text(encoding="utf-8"))
    ichecks += c
    fails.extend(f)
    print(f"   {ichecks} printed interval(s) confirmed to run low to high")

    dchecks, dfails = check_docx_parity()
    fails.extend(dfails)
    print(f"   {dchecks} check(s) that the DOCX carries the same images and biographies "
          f"as the LaTeX source")

    rchecks, rfails = check_retired_language()
    fails.extend(rfails)
    print(f"   {rchecks} retired claim(s) confirmed absent from the manuscript")

    kchecks, kfails = check_letter_content()
    fails.extend(kfails)
    print(f"   {kchecks} figure(s) and quotation(s) in the letter's own blocks bound to the "
          f"manuscript")
    for k, why in REMOVED_QUOTES.items():
        print(f"   allowed  letter quotes removed text: {k[:46]!r} — {why[:60]}")

    lchecks, lfails = check_letter_table5()
    fails.extend(lfails)
    print(f"[docs] {lchecks} claim(s) the letter makes about Table 5 bound to the table")
    for rel, a in ALLOW.items():
        for k, why in sorted(a.items()):
            print(f"   allowed  {rel}: {k} — {why}")
    if fails:
        print(f"[docs] FAILED ({len(fails)}):")
        for f in fails:
            print("   -", f)
        sys.exit(1)
    if checks == 0:
        sys.exit("[docs] VACUOUS: no figures were checked")
    print("[docs] OK — every reported figure traces to the frozen analysis")


if __name__ == "__main__":
    main()
