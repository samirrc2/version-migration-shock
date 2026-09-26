"""The document gate reads a printed figure's sign.

The pool used to store abs(), so a confidence interval printed as [0.140, -0.028] traced
cleanly against an analysis value of -0.140. Reading the sign brought its own trap: the "-" in
gemini-2.5-flash is a hyphen, and treating it as a minus turned three model names into negative
numbers. Both directions are pinned here.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "render"))
from check_docs import signed, check_interval_order          # noqa: E402

CASES = [
    ("gemini-2.5-flash is the incumbent", "2.5", 2.5),
    ("gpt-5.4-nano", "5.4", 5.4),
    ("CI [-0.140, -0.028]", "0.140", -0.140),
    ("a range of 7.7--14.9 points", "14.9", 14.9),
    ("delta = -0.178 overall", "0.178", -0.178),
    ("(-0.0046, 0.07)", "0.0046", -0.0046),
    ("declined by 0.080 points", "0.080", 0.080),
]


def _match(text, lit):
    return next(m for m in re.finditer(r"(?<![\w.])(\d+\.\d+)(?![\w])", text)
                if m.group(1) == lit)


def test_sign_is_read_from_context():
    for text, lit, want in CASES:
        got, _shown = signed(text, _match(text, lit))
        assert abs(got - want) < 1e-12, f"{text!r}: {lit} read as {got}, expected {want}"


def test_interval_order_flags_reversed_and_sign_flipped():
    _c, fails = check_interval_order("t", "CI [0.140, -0.028] and [-0.078, -0.203]")
    assert len(fails) == 2, fails


def test_interval_order_accepts_ordered_intervals():
    _c, fails = check_interval_order("t", "[-0.140, -0.028] [0.077, 0.149] [0.302, 0.458]")
    assert fails == []
