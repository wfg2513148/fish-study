from __future__ import annotations

import argparse
from pathlib import Path
import sys

from fish_study_wiki.study_protocol_checks import (
    CheckRow,
    check_homework_plan,
    check_review_plan_source,
    check_wrong_question_review,
)
from fish_study_wiki.study_protocol_models import (
    load_homework_plan,
    load_review_plan_source,
    load_wrong_question_review,
)
from fish_study_wiki.study_protocol_render import (
    render_homework_student_html,
    render_wrong_question_student_html,
)
from fish_study_wiki.study_protocol_writer import (
    DEFAULT_OUTPUT_ROOT,
    DEFAULT_VAULT_ROOT,
    write_homework_outputs,
    write_review_plan_outputs,
    write_wrong_question_outputs,
)


def run_homework(
    input_path: Path | str,
    output_root: Path | str = DEFAULT_OUTPUT_ROOT,
    vault_root: Path | str = DEFAULT_VAULT_ROOT,
) -> int:
    plan = load_homework_plan(input_path)
    student_html = render_homework_student_html(plan)
    printable_path = Path(output_root) / plan.date / "today-study-plan.html"
    if not _print_check_errors(
        check_homework_plan(plan, student_html, printable_path)
    ):
        return 1

    result = write_homework_outputs(plan, output_root, vault_root)
    _print_paths(
        ("student_html", result.student_html),
        ("parent_markdown", result.parent_markdown),
        ("obsidian_note", result.obsidian_note),
    )
    return 0


def run_wrong(
    input_path: Path | str,
    output_root: Path | str = DEFAULT_OUTPUT_ROOT,
    vault_root: Path | str = DEFAULT_VAULT_ROOT,
) -> int:
    review = load_wrong_question_review(input_path)
    student_html = render_wrong_question_student_html(review)
    printable_path = Path(output_root) / review.date / "wrong-question-review.html"
    if not _print_check_errors(
        check_wrong_question_review(review, student_html, printable_path)
    ):
        return 1

    result = write_wrong_question_outputs(review, output_root, vault_root)
    _print_paths(
        ("student_html", result.student_html),
        ("parent_markdown", result.parent_markdown),
        ("obsidian_note", result.obsidian_note),
        *tuple(("knowledge_note", path) for path in result.knowledge_notes),
    )
    return 0


def run_review_plan(
    input_path: Path | str,
    output_root: Path | str = DEFAULT_OUTPUT_ROOT,
    vault_root: Path | str = DEFAULT_VAULT_ROOT,
) -> int:
    source = load_review_plan_source(input_path)
    if not _print_check_errors(check_review_plan_source(source)):
        return 1

    result = write_review_plan_outputs(source, output_root, vault_root)
    _print_paths(
        ("markdown", result.markdown),
        ("obsidian_note", result.obsidian_note),
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m fish_study_wiki.study_protocol_cli"
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    _add_study_command(subcommands, "homework", "generate today's study plan")
    _add_study_command(subcommands, "wrong", "generate wrong-question review")
    _add_study_command(
        subcommands,
        "review-plan",
        "generate red/yellow/blue review plan",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "homework":
            return run_homework(args.input_path, args.output_root, args.vault_root)
        if args.command == "wrong":
            return run_wrong(args.input_path, args.output_root, args.vault_root)
        if args.command == "review-plan":
            return run_review_plan(args.input_path, args.output_root, args.vault_root)
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
