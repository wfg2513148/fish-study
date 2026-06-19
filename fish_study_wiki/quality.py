from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from fish_study_wiki.models import SourceRecord
from fish_study_wiki.source_ledger import load_sources
from fish_study_wiki.vault_writer import subject_dir
from fish_study_wiki.zip_inventory import sha256


@dataclass(frozen=True)
class QualityRow:
    grade: str
    volume: str
    subject: str
    status: str
    source_ids: tuple[str, ...]
    topic_count: int
    index_exists: bool

    @property
    def key(self) -> str:
        return f"{self.grade}/{self.volume}/{self.subject}"


@dataclass(frozen=True)
class QualityReport:
    rows: tuple[QualityRow, ...]
    errors: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.errors


def load_matrix(path: Path) -> list[dict[str, str]]:
    return json.loads(path.read_text(encoding="utf-8"))


def matrix_keys(matrix: list[dict[str, str]]) -> set[str]:
    return {f"{row['grade']}/{row['volume']}/{row['subject']}" for row in matrix}


def out_of_matrix_available_sources(
    sources: list[SourceRecord], valid_keys: set[str]
) -> list[SourceRecord]:
    return [
        source
        for source in sources
        if source.status == "available" and source.key not in valid_keys
    ]


def validate_available_source(source: SourceRecord) -> Path:
    if source.status != "available":
        raise ValueError(f"source {source.source_id} is not marked available")
    if not source.local_path:
        raise ValueError(f"available source {source.source_id} has no local_path")
    if not source.sha256:
        raise ValueError(f"available source {source.source_id} has no sha256")

    zip_path = Path(source.local_path)
    if not zip_path.exists():
        raise FileNotFoundError(
            f"available source {source.source_id} file not found: {zip_path}"
        )

    actual = sha256(zip_path)
    if actual != source.sha256:
        raise ValueError(
            f"available source {source.source_id} sha256 mismatch: "
            f"expected {source.sha256}, got {actual}"
        )
    return zip_path


def _source_map(sources: list[SourceRecord]) -> dict[str, list[SourceRecord]]:
    mapped: dict[str, list[SourceRecord]] = {}
    for source in sources:
        mapped.setdefault(source.key, []).append(source)
    return mapped


def _topic_count(vault: Path, grade: str, volume: str, subject: str) -> int:
    folder = subject_dir(vault, grade, volume, subject)
    if not folder.exists():
        return 0
    index_name = f"00-{subject}{grade}{volume}索引.md"
    return sum(1 for path in folder.glob("*.md") if path.name != index_name)


def _index_exists(vault: Path, grade: str, volume: str, subject: str) -> bool:
    path = (
        subject_dir(vault, grade, volume, subject)
        / f"00-{subject}{grade}{volume}索引.md"
    )
    return path.exists()


def _row_status(
    sources: list[SourceRecord],
    topic_count: int,
    index_exists: bool,
    validation_failed: bool,
) -> str:
    if validation_failed:
        return "source_error"
    if not sources:
        return "missing_source"
    if any(source.status == "available" for source in sources):
        if not index_exists:
            return "missing_vault_index"
        if topic_count:
            return "verified"
        return "source_index"
    return sources[0].status


def build_quality_report(
    matrix_path: Path,
    ledger_path: Path,
    vault: Path,
) -> QualityReport:
    matrix = load_matrix(matrix_path)
    valid_keys = matrix_keys(matrix)
    sources = load_sources(ledger_path)
    mapped = _source_map(sources)
    errors: list[str] = []
    failed_keys: set[str] = set()
    rows: list[QualityRow] = []

    for source in out_of_matrix_available_sources(sources, valid_keys):
        errors.append(
            f"available source {source.source_id} key {source.key} "
            "is not in subject matrix"
        )

    for source in sources:
        if source.status != "available":
            continue
        try:
            validate_available_source(source)
        except (FileNotFoundError, ValueError) as exc:
            errors.append(str(exc))
            failed_keys.add(source.key)

    for row in matrix:
        grade = row["grade"]
        volume = row["volume"]
        subject = row["subject"]
        key = f"{grade}/{volume}/{subject}"
        row_sources = mapped.get(key, [])
        count = _topic_count(vault, grade, volume, subject)
        has_index = _index_exists(vault, grade, volume, subject)
        status = _row_status(row_sources, count, has_index, key in failed_keys)
        if row_sources and status == "missing_vault_index":
            errors.append(f"{key} has available source but no vault index")
        rows.append(
            QualityRow(
                grade=grade,
                volume=volume,
                subject=subject,
                status=status,
                source_ids=tuple(source.source_id for source in row_sources),
                topic_count=count,
                index_exists=has_index,
            )
        )

    if len(rows) != 28:
        errors.append(f"matrix row count is {len(rows)}, expected 28")

    return QualityReport(rows=tuple(rows), errors=tuple(errors))


def render_quality_report(report: QualityReport) -> str:
    total = len(report.rows)
    verified = sum(1 for row in report.rows if row.status == "verified")
    missing = sum(1 for row in report.rows if row.status == "missing_source")
    lines = [
        "# Fish Study Wiki Quality",
        "",
        "## Summary",
        "",
        f"- Gate: {'PASS' if report.passed else 'FAIL'}",
        f"- Matrix rows: {total}",
        f"- Verified rows: {verified}",
        f"- Missing-source rows: {missing}",
        f"- Errors: {len(report.errors)}",
        "",
    ]

    if report.errors:
        lines.extend(["## Errors", ""])
        lines.extend(f"- {error}" for error in report.errors)
        lines.append("")

    lines.extend(
        [
            "## Coverage Matrix",
            "",
            "| Grade | Volume | Subject | Status | Sources | Topic notes | Index |",
            "|---|---|---|---|---|---:|---|",
        ]
    )
    for row in report.rows:
        sources = ", ".join(row.source_ids) if row.source_ids else "None"
        index = "yes" if row.index_exists else "no"
        lines.append(
            f"| {row.grade} | {row.volume} | {row.subject} | {row.status} | "
            f"{sources} | {row.topic_count} | {index} |"
        )

    return "\n".join(lines).rstrip() + "\n"


def write_quality_reports(
    report: QualityReport,
    repo_report_path: Path,
    vault_report_path: Path,
) -> None:
    text = render_quality_report(report)
    repo_report_path.parent.mkdir(parents=True, exist_ok=True)
    vault_report_path.parent.mkdir(parents=True, exist_ok=True)
    repo_report_path.write_text(text, encoding="utf-8")
    vault_report_path.write_text(text, encoding="utf-8")
