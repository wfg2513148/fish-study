from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from fish_study_wiki.models import safe_markdown_filename
from fish_study_wiki.study_protocol_models import (
    HomeworkItem,
    HomeworkPlan,
    KnowledgeMatch,
    WrongQuestionItem,
    WrongQuestionReview,
)
from fish_study_wiki.study_protocol_render import (
    COLOR_LABELS,
    render_homework_parent_markdown,
    render_homework_student_html,
    render_wrong_question_parent_markdown,
    render_wrong_question_student_html,
)


DEFAULT_OUTPUT_ROOT = Path("outputs")
DEFAULT_VAULT_ROOT = Path("/Users/kwang/Downloads/obsidian/fish-study")


@dataclass(frozen=True)
class StudyProtocolWriteResult:
    student_html: Path
    parent_markdown: Path
    obsidian_note: Path
    knowledge_notes: tuple[Path, ...] = ()


def write_homework_outputs(
    plan: HomeworkPlan,
    output_root: Path | str = DEFAULT_OUTPUT_ROOT,
    vault_root: Path | str = DEFAULT_VAULT_ROOT,
) -> StudyProtocolWriteResult:
    output_dir = _dated_output_dir(output_root, plan.date)
    student_html = output_dir / "today-study-plan.html"
    parent_markdown = output_dir / "today-study-plan-parent.md"
    student_html.write_text(render_homework_student_html(plan), encoding="utf-8")
    parent_markdown.write_text(render_homework_parent_markdown(plan), encoding="utf-8")

    obsidian_note = _daily_plan_path(vault_root, plan.date)
    obsidian_note.parent.mkdir(parents=True, exist_ok=True)
    obsidian_note.write_text(
        _render_daily_plan_note(plan, student_html, parent_markdown),
        encoding="utf-8",
    )
    return StudyProtocolWriteResult(student_html, parent_markdown, obsidian_note)


def write_wrong_question_outputs(
    review: WrongQuestionReview,
    output_root: Path | str = DEFAULT_OUTPUT_ROOT,
    vault_root: Path | str = DEFAULT_VAULT_ROOT,
) -> StudyProtocolWriteResult:
    output_dir = _dated_output_dir(output_root, review.date)
    student_html = output_dir / "wrong-question-review.html"
    parent_markdown = output_dir / "wrong-question-review-parent.md"
    student_html.write_text(render_wrong_question_student_html(review), encoding="utf-8")
    parent_markdown.write_text(render_wrong_question_parent_markdown(review), encoding="utf-8")

    obsidian_note = _wrong_question_path(vault_root, review.date)
    obsidian_note.parent.mkdir(parents=True, exist_ok=True)
    obsidian_note.write_text(
        _render_wrong_question_note(review, student_html, parent_markdown),
        encoding="utf-8",
    )
    knowledge_notes = _append_wrong_question_records(
        Path(vault_root), review, student_html
    )
    return StudyProtocolWriteResult(
        student_html,
        parent_markdown,
        obsidian_note,
        tuple(sorted(knowledge_notes)),
    )


def _dated_output_dir(output_root: Path | str, plan_date: str) -> Path:
    output_dir = Path(output_root) / plan_date
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _daily_plan_path(vault_root: Path | str, plan_date: str) -> Path:
    return Path(vault_root) / "30-每日学习计划" / f"{plan_date}.md"


def _wrong_question_path(vault_root: Path | str, plan_date: str) -> Path:
    return Path(vault_root) / "20-错题归因" / f"{plan_date}.md"


def _render_daily_plan_note(
    plan: HomeworkPlan,
    student_html: Path,
    parent_markdown: Path,
) -> str:
    return f"""# {plan.date} 每日学习计划

## 打印材料

- 学生版：{student_html}
- 家长参考：{parent_markdown}

## 作业清单

{_daily_homework_items(plan.items)}

## 待确认项

{_uncertain_items(plan.uncertain_items)}
"""


def _render_wrong_question_note(
    review: WrongQuestionReview,
    student_html: Path,
    parent_markdown: Path,
) -> str:
    return f"""# {review.date} 错题归因

## 打印材料

- 学生版：{student_html}
- 家长参考：{parent_markdown}

## 错题列表

{_wrong_question_items(review.items, review.date)}

## 家长复盘备注

- 先看贴纸颜色，再按讲解顺序复盘。
- 下次复测日期：{_next_review_date(review.date)}

## 待确认项

{_uncertain_items(review.uncertain_items)}
"""


def _daily_homework_items(items: tuple[HomeworkItem, ...]) -> str:
    lines = []
    for item in items:
        lines.append(f"- {item.subject}：{item.raw_text}")
        for match in item.matched_knowledge:
            lines.append(f"  - 知识点：{_md_link(match.note)}（置信度：{match.confidence}）")
    return "\n".join(lines) if lines else "- 暂无。"


def _wrong_question_items(items: tuple[WrongQuestionItem, ...], source_date: str) -> str:
    lines = []
    for item in items:
        lines.append(
            f"- {item.subject} {item.question_id}："
            f"{COLOR_LABELS.get(item.sticker_color, item.sticker_color)}，"
            f"{item.reason}，{item.next_action}"
        )
        for match in item.matched_knowledge:
            lines.append(f"  - 知识点：{_md_link(match.note)}（置信度：{match.confidence}）")
        lines.append(f"  - 下次复测：{_next_review_date(source_date)}")
    return "\n".join(lines) if lines else "- 暂无。"


def _append_wrong_question_records(
    vault_root: Path,
    review: WrongQuestionReview,
    student_html: Path,
) -> set[Path]:
    by_note: dict[KnowledgeMatch, list[WrongQuestionItem]] = {}
    for item in review.items:
        for match in item.matched_knowledge:
            if match.is_pending:
                continue
            by_note.setdefault(match, []).append(item)

    changed: set[Path] = set()
    for match, items in by_note.items():
        note_path = _knowledge_note_path(vault_root, match, items[0].subject)
        note_path.parent.mkdir(parents=True, exist_ok=True)
        if not note_path.exists():
            note_path.write_text(f"# {match.note}\n\n## 错题记录\n", encoding="utf-8")
        current = note_path.read_text(encoding="utf-8")
        block = _knowledge_wrong_block(review.date, items, student_html)
        begin = _block_begin(review.date)
        if begin not in current:
            note_path.write_text(current.rstrip() + "\n\n" + block, encoding="utf-8")
        changed.add(note_path)
    return changed


def _knowledge_note_path(vault_root: Path, match: KnowledgeMatch, subject: str) -> Path:
    filename = safe_markdown_filename(match.note)
    existing = tuple(vault_root.rglob(filename))
    if existing:
        return existing[0]
    return vault_root / "10-教材Wiki" / match.grade / match.volume / subject / filename


def _knowledge_wrong_block(
    review_date: str,
    items: list[WrongQuestionItem],
    student_html: Path,
) -> str:
    lines = [
        _block_begin(review_date),
        f"### {review_date} 错题记录",
        "",
        f"- 关联打印材料：{student_html}",
    ]
    for item in items:
        lines.append(
            f"- {item.subject} {item.question_id}："
            f"{COLOR_LABELS.get(item.sticker_color, item.sticker_color)}，"
            f"{item.reason}，复测状态：待复测"
        )
    lines.append(_block_end(review_date))
    return "\n".join(lines) + "\n"


def _block_begin(record_date: str) -> str:
    return f"<!-- study-protocol-wrong:{record_date}:start -->"


def _block_end(record_date: str) -> str:
    return f"<!-- study-protocol-wrong:{record_date}:end -->"


def _uncertain_items(items: tuple[str, ...]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- 暂无。"


def _next_review_date(source_date: str) -> str:
    try:
        parsed = date.fromisoformat(source_date)
    except ValueError:
        return "待定"
    return str(parsed + timedelta(days=3))


def _md_link(note: str) -> str:
    return "[[待定位]]" if note == "待定位" else f"[[{note}]]"
