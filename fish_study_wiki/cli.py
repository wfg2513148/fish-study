from __future__ import annotations

import argparse
from collections.abc import Callable
import io
from pathlib import Path
import sys
import zipfile

from fish_study_wiki import settings
from fish_study_wiki import study_protocol_cli
from fish_study_wiki.knowledge_graph import build_topic_graph, write_graph
from fish_study_wiki.models import SourceRecord
from fish_study_wiki.pptx_text import extract_pptx_text
from fish_study_wiki.quality import (
    build_quality_report,
    load_matrix,
    matrix_keys,
    out_of_matrix_available_sources,
    validate_available_source,
    write_quality_reports,
)
from fish_study_wiki.source_ledger import load_sources
from fish_study_wiki.topic_builder import topic_from_source_file
from fish_study_wiki.vault_writer import (
    subject_dir,
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
    matrix_path: Path = MATRIX_PATH,
) -> list[tuple[SourceRecord, Path]]:
    sources = [
        source for source in load_sources(ledger_path) if source.status == "available"
    ]
    valid_keys = matrix_keys(load_matrix(matrix_path))
    out_of_matrix = out_of_matrix_available_sources(sources, valid_keys)
    if out_of_matrix:
        source = out_of_matrix[0]
        raise ValueError(
            f"available source {source.source_id} key {source.key} "
            "is not in subject matrix"
        )
    return [(source, validate_available_source(source)) for source in sources]


def source_topics(
    vault: Path = settings.VAULT_ROOT,
    ledger_path: Path = LEDGER_PATH,
    matrix_path: Path = MATRIX_PATH,
    graph_path: Path | None = None,
) -> dict[tuple[str, str, str], tuple[str, list[str]]]:
    grouped: dict[tuple[str, str, str], tuple[str, list[str]]] = {}
    sources_with_paths = available_sources_with_paths(ledger_path, matrix_path)
    sources = [source for source, _ in sources_with_paths]
    notes = []
    for source, zip_path in sources_with_paths:
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
                notes.append(note)
                links.append(topic_link(note))
        grouped[key] = (version, links)
    if graph_path is not None:
        write_graph(build_topic_graph(sources, notes), graph_path)
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
    grouped = source_topics(vault, graph_path=settings.KNOWLEDGE_GRAPH_PATH)
    make_subject_indexes(grouped, vault)
    topic_count = sum(len(links) for _, links in grouped.values())
    print(f"Built {topic_count} topic links and subject indexes under {vault}")
    print(f"Wrote knowledge graph to {settings.KNOWLEDGE_GRAPH_PATH}")
    return 0


def run_verify(
    matrix_path: Path = MATRIX_PATH,
    ledger_path: Path = LEDGER_PATH,
    vault: Path = settings.VAULT_ROOT,
    repo_report_path: Path = REPO_QUALITY_PATH,
    vault_report_path: Path = VAULT_QUALITY_PATH,
) -> int:
    report = build_quality_report(
        matrix_path,
        ledger_path,
        vault,
        settings.KNOWLEDGE_GRAPH_PATH,
    )
    write_quality_reports(report, repo_report_path, vault_report_path)
    print(f"Wrote quality report to {repo_report_path}")
    print(f"Wrote vault quality report to {vault_report_path}")
    if not report.passed:
        for error in report.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Quality gate passed")
    return 0


def run_study_context(
    matrix_path: Path = MATRIX_PATH,
    ledger_path: Path = LEDGER_PATH,
    vault: Path = settings.VAULT_ROOT,
) -> int:
    matrix = load_matrix(matrix_path)
    sources = [source for source in load_sources(ledger_path) if source.status == "available"]
    lines = [
        "# Fish Study 当前工作上下文",
        "",
        "## 可用资料范围",
        "",
        f"- 覆盖矩阵：{len(matrix)} 个年级/册别/学科组合",
        f"- 当前可用资料：{len(sources)} 套",
        "",
    ]
    for source in sorted(sources, key=lambda item: item.key):
        note_count = _topic_note_count(vault, source.grade, source.volume, source.subject)
        lines.append(
            f"- {source.grade}{source.volume}{source.subject}：{source.version}，"
            f"{source.source_id}，知识点笔记 {note_count} 篇"
        )
    lines.extend(
        [
            "",
            "## 使用边界",
            "",
            "- 只基于上述可用资料定位知识点；没有资料的学科不要猜。",
            "- 看不清题目或知识点无法确认时，写 `note: 待定位`，并加入 `uncertain_items`。",
            "- 只有 `confidence: high` 且 `confirmation_status: auto/confirmed` 的分析进入长期统计。",
            "",
            "## 常用命令",
            "",
            "```bash",
            "python3 -m fish_study_wiki.cli study-wrong samples/wrong-question-training.json",
            "python3 -m fish_study_wiki.cli study-weekly-review samples/weekly-review-source.json",
            "python3 -m fish_study_wiki.cli verify",
            "```",
        ]
    )
    print("\n".join(lines))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python3 -m fish_study_wiki.cli")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("inventory", help="rebuild source ZIP inventories")
    subcommands.add_parser("build", help="build Obsidian wiki indexes and notes")
    subcommands.add_parser("verify", help="write quality reports and run gates")
    subcommands.add_parser("study-context", help="print current study workflow context")
    _add_study_alias(subcommands, "study-wrong", "generate wrong-question training")
    _add_study_alias(
        subcommands,
        "study-weekly-review",
        "generate weekly wrong-question review",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "inventory":
        return run_inventory()
    if args.command == "build":
        return run_build()
    if args.command == "verify":
        return run_verify()
    if args.command == "study-context":
        return run_study_context()
    if args.command == "study-wrong":
        return _run_study_alias(study_protocol_cli.run_wrong, args)
    if args.command == "study-weekly-review":
        return _run_study_alias(study_protocol_cli.run_weekly_review, args)
    raise ValueError(f"unknown command: {args.command}")


def _run_study_alias(
    runner: Callable[[Path, Path, Path], int],
    args: argparse.Namespace,
) -> int:
    try:
        return runner(args.input_path, args.output_root, args.vault_root)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def _topic_note_count(vault: Path, grade: str, volume: str, subject: str) -> int:
    folder = subject_dir(vault, grade, volume, subject)
    if not folder.exists():
        return 0
    return sum(
        1
        for path in folder.glob("*.md")
        if not path.name.startswith("00-")
    )


def _add_study_alias(
    subcommands: argparse._SubParsersAction[argparse.ArgumentParser],
    name: str,
    help_text: str,
) -> None:
    command = subcommands.add_parser(name, help=help_text)
    command.add_argument("input_path", type=Path)
    command.add_argument(
        "--output-root",
        type=Path,
        default=study_protocol_cli.DEFAULT_OUTPUT_ROOT,
    )
    command.add_argument(
        "--vault-root",
        type=Path,
        default=study_protocol_cli.DEFAULT_VAULT_ROOT,
    )


if __name__ == "__main__":
    raise SystemExit(main())
