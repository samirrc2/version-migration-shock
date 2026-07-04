"""Objective ground-truth labels. Altman Z''-score (no market-value term, so it is
computable from reported statements alone and fully reproducible) with the standard
emerging-market bands. Used to grade the credit-health task."""
from __future__ import annotations


def altman_z(fin: dict):
    ta = fin.get("total_assets")
    tl = fin.get("total_liabilities")
    eq = fin.get("equity")
    if not ta or tl in (None, 0) or eq is None:
        return None
    wc = (fin.get("current_assets") or 0) - (fin.get("current_liabilities") or 0)
    re_ = fin.get("retained_earnings") or 0
    ebit = fin.get("ebit") or 0
    return 6.56 * (wc / ta) + 3.26 * (re_ / ta) + 6.72 * (ebit / ta) + 1.05 * (eq / tl)


def altman_band(z) -> str | None:
    if z is None:
        return None
    if z > 2.6:
        return "SAFE"
    if z >= 1.1:
        return "WATCH"
    return "DISTRESS"


def band_from_fin(fin: dict) -> str | None:
    return altman_band(altman_z(fin))
