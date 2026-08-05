"""Active-task configuration, read once and shared by agent/metrics/outcomes so the
whole pipeline is label-agnostic. Switch the task in config/task.yaml."""
from __future__ import annotations
from pathlib import Path
import yaml

_HERE = Path(__file__).resolve().parent
_T = yaml.safe_load((_HERE / "task.yaml").read_text())

NAME: str = _T["active"]
_t = _T["tasks"][NAME]

CATEGORIES: list[str] = list(_t["categories"])
CATEGORY_SET = set(CATEGORIES)
ORDINAL: dict[str, int] = dict(_t["ordinal"])
DRIFT_LABEL: str = _t["drift_label"]
ABSTAIN_LABEL = _t.get("abstain_label")
GROUND_TRUTH: str = _t["ground_truth"]
DOC_KIND: str = _t.get("doc_kind", "fundamentals")
DOC_DIR: str = "docs" if DOC_KIND == "fundamentals" else "inputs"
PROMPT_FILE: str = _t["prompt_file"]


def all_tasks() -> dict:
    return _T["tasks"]
