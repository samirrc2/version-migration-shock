#!/usr/bin/env python3
"""Build a neutral (non-IEEE) preprint PDF from paper/main.tex for SSRN.

Same text, numbers, equations, tables, figures, and references as the IEEE
Access manuscript, but rendered in a plain single-column `article` class with
NO IEEE template, NO "IEEE Access" running heads, and NO DOI/history line.
Output: ssrn/preprint.tex (+ compile with pdflatex to ssrn/preprint.pdf).
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "paper" / "main.tex"
OUT = HERE / "preprint.tex"

s = SRC.read_text()

title = re.search(r"\\title\{(.+?)\}", s, re.S).group(1).strip()
abstract = re.search(r"\\begin\{abstract\}(.+?)\\end\{abstract\}", s, re.S).group(1).strip()
keywords = re.search(r"\\begin\{keywords\}(.+?)\\end\{keywords\}", s, re.S).group(1).strip()

# body: from Introduction through the biographies, up to \EOD
body = s[s.index("\\section{Introduction}"):s.index("\\EOD")]

# --- neutralize IEEE-only markup in the body ---
body = re.sub(r"\\PARstart\{(.)\}\{([^}]*)\}", r"\1\2", body)       # \PARstart{L}{arge} -> Large
body = body.replace("figure*", "figure").replace("table*", "table")  # no starred floats single-col
# biographies -> plain bold-name paragraphs under a heading
body = body.replace("\\begin{IEEEbiographynophoto}{",
                    "\\section*{Author Biographies}\n\\noindent\\textbf{", 1)   # first one gets the heading
body = re.sub(r"\\begin\{IEEEbiographynophoto\}\{([^}]*)\}",
              r"\n\\medskip\\noindent\\textbf{\1.} ", body)          # any remaining
body = re.sub(r"\\section\*\{Author Biographies\}\n\\noindent\\textbf\{([^}]*)\}",
              r"\\section*{Author Biographies}\n\\noindent\\textbf{\1.} ", body, count=1)
body = body.replace("\\end{IEEEbiographynophoto}", "\n")

preamble = r"""\documentclass[11pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{multirow}
\usepackage{array}
\usepackage{url}
\usepackage{cite}
\usepackage{caption}
\captionsetup{font=small,labelfont=bf}
\graphicspath{{../paper/figures/}{../paper/}}
\setlength{\parskip}{2pt}

\title{\textbf{%s}%%
\thanks{This work received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors. Corresponding author: Robin Chawla (robin.chawla.cse14@iitbhu.ac.in).}}
\author{Samir Chincholikar\thanks{Independent Researcher. Email: samir.chincholikar@gmail.com; ORCID 0009-0007-2779-3492.}
\and Robin Chawla\thanks{Independent Researcher. Email: robin.chawla.cse14@iitbhu.ac.in; ORCID 0009-0007-2807-3948.}}
\date{Preprint --- August 2026. This is a preprint and has not been peer reviewed.}

\begin{document}
\maketitle

\begin{abstract}
%s
\end{abstract}

\noindent\textbf{Keywords:} %s

\medskip
""" % (title, abstract, keywords.rstrip("."))

OUT.write_text(preamble + "\n" + body + "\n\\end{document}\n")
print("wrote", OUT)
