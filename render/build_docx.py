#!/usr/bin/env python3
"""Build paper/main.docx from paper/main.tex so the Word file matches the PDF.

IEEE Access requires that the submitted Word/LaTeX source and the PDF match in
content. The manuscript is authored in the IEEE Access LaTeX template, whose
custom front-matter macros pandoc does not understand. This script preprocesses
main.tex into pandoc-friendly LaTeX (neutralizing IEEE-only macros, flattening
\\PARstart, biographies, keywords, and numbering \\cite from the bibitem order)
and then runs pandoc to emit main.docx.

Usage:  python3 render/build_docx.py
Requires: pandoc on PATH.
"""
import re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEX = HERE.parent / "paper" / "main.tex"
OUT = HERE.parent / "paper" / "main.docx"


def build_cite_map(src: str):
    keys = re.findall(r"\\bibitem\{([^}]+)\}", src)
    return {k: i + 1 for i, k in enumerate(keys)}


def repl_cites(src: str, cmap: dict) -> str:
    def sub(m):
        nums = [str(cmap.get(k.strip(), "?")) for k in m.group(1).split(",")]
        return "[" + ", ".join(nums) + "]"
    return re.sub(r"\\cite\{([^}]+)\}", sub, src)


def preprocess(src: str) -> str:
    cmap = build_cite_map(src)

    # 1. class + drop the boldmath font block (times fonts unavailable to pandoc)
    src = src.replace(r"\documentclass{ieeeaccess}", r"\documentclass{article}")
    src = re.sub(r"\\makeatletter.*?\\makeatother", "", src, flags=re.S)
    src = re.sub(r"\\graphicspath\{[^\n]*\}", "", src)
    for pkg in ("cite",):  # cite pkg conflicts with manual numbering
        src = src.replace(f"\\usepackage{{{pkg}}}", "")

    # 2. numbered citations from bibitem order, then strip the cls-only line pieces
    src = repl_cites(src, cmap)

    # 2b. resolve \ref against paper/main.aux, which pandoc cannot do for itself. Two
    # references (Table 1 and Table 5) reached the Word file as "Table [tab:models]" and
    # "Table [tab:gov]". Taking the numbers from the aux file of the PDF build means the
    # Word file cannot disagree with the PDF about a table number.
    aux = TEX.with_suffix(".aux")
    if aux.exists():
        labels = dict(re.findall(r"\\newlabel\{([^}]+)\}\{\{(?:\\mbox\s*\{)?([^}]+)\}", aux.read_text()))
        src = re.sub(r"\\ref\{([^}]+)\}", lambda m: labels.get(m.group(1), m.group(1)), src)

    # 3. neutralize IEEE front-matter macros -> plain content
    src = re.sub(r"\\history\{[^}]*\}", "", src)
    src = re.sub(r"\\doi\{[^}]*\}", "", src)
    src = re.sub(r"\\markboth\s*\{[^}]*\}\s*\{[^}]*\}", "", src)
    src = re.sub(r"\\titlepgskip=[^\n]*", "", src)
    src = src.replace(r"\authorrefmark{1}", "")
    src = re.sub(r"\\uppercase\{([^}]*)\}", r"\1", src)
    # affiliation, corresponding author, and funding footnote -> visible paragraphs
    src = re.sub(r"\\address\[1\]\{([^}]*)\}", r"\n\\medskip\\noindent \1\n", src)
    src = re.sub(r"\\corresp\{([^}]*)\}", r"\n\\noindent \1\n", src)
    src = re.sub(r"\\tfootnote\{([^}]*)\}", r"\n\\noindent \1\n", src)
    # \PARstart{L}{arge} -> Large
    src = re.sub(r"\\PARstart\{(.)\}\{([^}]*)\}", r"\1\2", src)
    src = src.replace(r"\EOD", "")

    # 4. keywords environment -> Index Terms paragraph
    src = re.sub(r"\\begin\{keywords\}(.*?)\\end\{keywords\}",
                 lambda m: r"\medskip\noindent\textbf{Index Terms—}" + m.group(1).strip(),
                 src, flags=re.S)

    # 5. biographies -> subsection heading + body
    src = re.sub(r"\\begin\{IEEEbiographynophoto\}\{([^}]*)\}(.*?)\\end\{IEEEbiographynophoto\}",
                 lambda m: "\n\\subsection*{" + m.group(1) + "}\n" + m.group(2).strip() + "\n",
                 src, flags=re.S)

    # Biographies WITH a photo. Only the nophoto form was rewritten, so when the photos were
    # added pandoc silently dropped them: the Word file kept both biographies and lost both
    # portraits, and nothing compared the two files' image counts. The optional argument holds
    # the \includegraphics call, which is lifted out and emitted as its own paragraph.
    def _bio(m):
        photo = re.search(r"\\includegraphics\[[^\]]*\]\{([^}]*)\}", m.group(1))
        img = f"\n\\includegraphics[width=1in]{{{photo.group(1)}}}\n" if photo else ""
        return f"\n\\subsection*{{{m.group(2)}}}\n{img}\n{m.group(3).strip()}\n"

    # The optional argument is wrapped in its own braces -- [{\includegraphics[..]{..}}] -- so the
    # pattern anchors on "[{" ... "}]". Matching on "[" ... "]" instead stops at the first "]",
    # which belongs to \includegraphics's own options, and leaves the rest as stray LaTeX.
    src = re.sub(r"\\begin\{IEEEbiography\}\[\{(.*?)\}\]\{([^}]*)\}(.*?)\\end\{IEEEbiography\}",
                 _bio, src, flags=re.S)

    # 7. bibliography -> REFERENCES heading + explicitly numbered entries.
    # pandoc renders \begin{thebibliography}{99} by emitting the "99" width argument as
    # literal text and dropping both the section heading and the per-entry numbers. The
    # Word file therefore carried an unnumbered reference list while its own body cited
    # [29] and [31], so every citation pointed at nothing. The numbers below come from the
    # same cmap that numbers the in-text citations, so the two cannot drift apart.
    def _bib(m):
        parts = re.split(r"\\bibitem\{([^}]+)\}", m.group(1))
        out = ["\\section*{REFERENCES}"]
        for k in range(1, len(parts), 2):
            key, text = parts[k], " ".join(parts[k + 1].split())
            out.append(f"[{cmap[key]}] {text}")
        return "\n\n".join(out) + "\n"

    src = re.sub(r"\\begin\{thebibliography\}\{[^}]*\}(.*?)\\end\{thebibliography\}",
                 _bib, src, flags=re.S)

    # 6. figures: point at the png files that live in paper/figures/
    return src


def main():
    if not TEX.exists():
        sys.exit(f"missing {TEX}")
    pre = preprocess(TEX.read_text())
    tmp = HERE.parent / "paper" / "_main_docx_src.tex"
    tmp.write_text(pre)
    try:
        subprocess.run(
            ["pandoc", tmp.name, "-f", "latex", "-o", OUT.name,
             "--resource-path", ".:figures"],
            cwd=str(TEX.parent), check=True)
        print(f"wrote {OUT}")
    finally:
        tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
