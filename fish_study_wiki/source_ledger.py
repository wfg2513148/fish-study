from __future__ import annotations

import json
from pathlib import Path

from fish_study_wiki.models import SourceRecord


def load_sources(path: Path) -> list[SourceRecord]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [SourceRecord(**row) for row in data]


def missing_matrix_entries(matrix: list[dict[str, str]], covered: set[str]) -> list[str]:
    missing: list[str] = []
    for row in matrix:
        key = f"{row['grade']}/{row['volume']}/{row['subject']}"
        if key not in covered:
            missing.append(key)
    return missing
