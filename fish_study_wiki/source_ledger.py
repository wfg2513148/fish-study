from __future__ import annotations

import json
from pathlib import Path

from fish_study_wiki import settings
from fish_study_wiki.models import SourceRecord


def load_sources(path: Path) -> list[SourceRecord]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [SourceRecord(**_resolve_local_path(row)) for row in data]


def _resolve_local_path(row: dict[str, str]) -> dict[str, str]:
    local_path = row.get("local_path", "")
    if not local_path:
        return row
    path = Path(local_path).expanduser()
    if path.is_absolute():
        return row
    resolved = settings.REPO_ROOT / path
    return {**row, "local_path": str(resolved)}


def missing_matrix_entries(matrix: list[dict[str, str]], covered: set[str]) -> list[str]:
    missing: list[str] = []
    for row in matrix:
        key = f"{row['grade']}/{row['volume']}/{row['subject']}"
        if key not in covered:
            missing.append(key)
    return missing
