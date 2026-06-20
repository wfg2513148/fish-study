from __future__ import annotations

import argparse
from pathlib import Path
import sys

from fish_study_wiki.study_protocol_checks import (
    CheckRow,
    check_weekly_review,
    check_wrong_question_training,
)
from fish_study_wiki.study_protocol_models import (
    load_weekly_review_source,
    load_wrong_question_training,
)
from fish_study_wiki.study_protocol_render import (
    render_training_answer_html,
    render_training_student_html,
    render_weekly_answer_html,
    render_weekly_worksheet_html,
)
from fish_study_wiki.study_protocol_writer import (
    DEFAULT_OUTPUT_ROOT,
    DEFAULT_VAULT_ROOT,
    write_training_outputs,
    write_weekly_review_outputs,
)


def run_wrong(
    input_path: Path | str,
    output_root: Path | str = DEFAULT_OUTPUT_ROOT,
    vault_root: Path | str = DEFAULT_VAULT_ROOT,
) -> int:
    training = load_wrong_question_training(input_path)
    student_html = render_training_student_html(training)
    answer_html = render_training_answer_html(training)
    printable_path = Path(output_root) / training.date / "wrong-question-training.html"
    answer_path = Path(output_root) / training.date / "wrong-question-training-answers.html"
    if not _print_check_errors(
        check_wrong_question_training(
            training,
            student_html,
            answer_html,
            printable_path,
            answer_path,
        )
    ):
        return 1

    result = write_training_outputs(training, output_root, vault_root)
    _print_paths(
        ("student_html", result.student_html),
        ("answer_html", result.answer_html),
        ("obsidian_note", result.obsidian_note),
        *tuple(("event_note", path) for path in result.event_notes),
        *tuple(
            (f"{output.subject}_student_html", output.student_html)
            for output in result.subject_outputs
        ),
        *tuple(
            (f"{output.subject}_answer_html", output.answer_html)
            for output in result.subject_outputs
        ),
        *tuple(
            (f"{output.subject}_knowledge_markdown", output.knowledge_markdown)
            for output in result.subject_outputs
        ),
    )
    return 0


def run_weekly_review(
    input_path: Path | str,
    output_root: Path | str = DEFAULT_OUTPUT_ROOT,
    vault_root: Path | str = DEFAULT_VAULT_ROOT,
) -> int:
    source = load_weekly_review_source(input_path)
    student_html = render_weekly_worksheet_html(source)
    answer_html = render_weekly_answer_html(source)
    report_path = Path(output_root) / source.week_end / "weekly-review.md"
    printable_path = Path(output_root) / source.week_end / "weekly-review.html"
    answer_path = Path(output_root) / source.week_end / "weekly-review-answers.html"
    if not _print_check_errors(
        check_weekly_review(
            source,
            student_html,
            answer_html,
            report_path,
            printable_path,
            answer_path,
        )
    ):
        return 1

    result = write_weekly_review_outputs(source, output_root, vault_root)
    _print_paths(
        ("report_markdown", result.report_markdown),
        ("student_html", result.student_html),
        ("answer_html", result.answer_html),
        ("obsidian_note", result.obsidian_note),
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m fish_study_wiki.study_protocol_cli"
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    _add_study_command(subcommands, "wrong", "generate wrong-question training")
    _add_study_command(
        subcommands,
        "weekly-review",
        "generate weekly wrong-question review",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "wrong":
            return run_wrong(args.input_path, args.output_root, args.vault_root)
        if args.command == "weekly-review":
            return run_weekly_review(args.input_path, args.output_root, args.vault_root)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    raise ValueError(f"unknown command: {args.command}")


def _add_study_command(
    subcommands: argparse._SubParsersAction[argparse.ArgumentParser],
    name: str,
    help_text: str,
) -> None:
    command = subcommands.add_parser(name, help=help_text)
    command.add_argument("input_path", type=Path)
    command.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    command.add_argument("--vault-root", type=Path, default=DEFAULT_VAULT_ROOT)


def _print_check_errors(rows: tuple[CheckRow, ...]) -> bool:
    failed = tuple(row for row in rows if not row.passed)
    for row in failed:
        print(f"ERROR: {row.code}: {row.message}", file=sys.stderr)
    return not failed


def _print_paths(*paths: tuple[str, Path]) -> None:
    for label, path in paths:
        print(f"{label}: {path}")


if __name__ == "__main__":
    raise SystemExit(main())
