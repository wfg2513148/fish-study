from __future__ import annotations

import argparse
import io
from pathlib import Path
import sys
import zipfile

from fish_study_wiki import settings
from fish_study_wiki.models import SourceRecord
from fish_study_wiki.pptx_text import extract_pptx_text
from fish_study_wiki.quality import (
    build_quality_report,
    validate_available_source,
    write_quality_reports,
)
from fish_study_wiki.source_ledger import load_sources
from fish_study_wiki.topic_builder import topic_from_source_file
from fish_study_wiki.vault_writer import (
    topic_link,
    write_subject_index,
    write_topic_note,
)
from fish_study_wiki.zip_inventory import decode_zip_name, rebuild_inventories


MATRIX_PATH = settings.REPO_ROOT / "data" / "catalog" / "subject-matrix.json"
LEDGER_PATH = settings.REPO_ROOT / "data" / "sources" / "source-ledger.json"
REPO_QUALITY_PATH = settings.REPORT_DIR / "wiki-quality.md"
VAULT_QUALITY_PATH = settings.VAULT_ROOT / "00-入口" / "wiki-quality.md"


def available_sources_with_paths(
    ledger_path: Path = LEDGER_PATH,
) -> list[tuple[SourceRecord, Path]]:
    sources = [
        source for source in load_sources(ledger_path) if source.status == "available"
    ]
    return [(source, validate_available_source(source)) for source in sources]


def source_topics(
    vault: Path = settings.VAULT_ROOT,
    ledger_path: Path = LEDGER_PATH,
) -> dict[tuple[str, str, str], tuple[str, list[str]]]:
    grouped: dict[tuple[str, str, str], tuple[str, list[str]]] = {}
    for source, zip_path in available_sources_with_paths(ledger_path):
        key = (source.grade, source.volume, source.subject)
        version, links = grouped.setdefault(key, (source.version, []))
        with zipfile.ZipFile(zip_path) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                source_file = decode_zip_name(info.filename)
                if not source_file.lower().endswith(".pptx"):
                    continue
                extracted_text = extract_pptx_text(io.BytesIO(archive.read(info)))
                note = topic_from_source_file(source, source_file, extracted_text)
                write_topic_note(vault, note)
                links.append(topic_link(note))
        grouped[key] = (version, links)
    return grouped


def make_subject_indexes(
    grouped: dict[tuple[str, str, str], tuple[str, list[str]]],
    vault: Path = settings.VAULT_ROOT,
) -> None:
    for grade in settings.GRADES:
        for volume in settings.VOLUMES:
            for subject in settings.SUBJECTS:
                version, links = grouped.get(
                    (grade, volume, subject), ("待确认或待补齐。", [])
                )
                write_subject_index(vault, grade, volume, subject, version, links)


def run_inventory(
    raw_dir: Path = settings.RAW_SOURCE_DIR,
    inventory_dir: Path = settings.INVENTORY_DIR,
) -> int:
    summaries = rebuild_inventories(raw_dir, inventory_dir)
    print(f"Wrote inventories for {len(summaries)} source ZIPs to {inventory_dir}")
    return 0


def run_build(vault: Path = settings.VAULT_ROOT) -> int:
    grouped = source_topics(vault)
    make_subject_indexes(grouped, vault)
    topic_count = sum(len(links) for _, links in grouped.values())
    print(f"Built {topic_count} topic links and subject indexes under {vault}")
    return 0


def run_verify(
    matrix_path: Path = MATRIX_PATH,
    ledger_path: Path = LEDGER_PATH,
    vault: Path = settings.VAULT_ROOT,
    repo_report_path: Path = REPO_QUALITY_PATH,
    vault_report_path: Path = VAULT_QUALITY_PATH,
) -> int:
    report = build_quality_report(matrix_path, ledger_path, vault)
    write_quality_reports(report, repo_report_path, vault_report_path)
    print(f"Wrote quality report to {repo_report_path}")
    print(f"Wrote vault quality report to {vault_report_path}")
    if not report.passed:
        for error in report.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Quality gate passed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python3 -m fish_study_wiki.cli")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("inventory", help="rebuild source ZIP inventories")
    subcommands.add_parser("build", help="build Obsidian wiki indexes and notes")
    subcommands.add_parser("verify", help="write quality reports and run gates")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "inventory":
        return run_inventory()
    if args.command == "build":
        return run_build()
    if args.command == "verify":
        return run_verify()
    raise ValueError(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
