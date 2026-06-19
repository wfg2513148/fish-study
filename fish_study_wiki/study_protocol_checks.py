from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fish_study_wiki.study_protocol_models import (
    HomeworkPlan,
    KnowledgeMatch,
    ReviewPlanSource,
    STICKER_COLORS,
    WrongQuestionReview,
)


ANSWER_MARKERS = ("答案", "参考答案", "解析", "解答")


@dataclass(frozen=True)
class CheckRow:
    passed: bool
    code: str
    message: str


def check_homework_plan(
    plan: HomeworkPlan,
    student_output: str,
    printable_path: Path | str,
) -> tuple[CheckRow, ...]:
    return (
        _no_answers_in_student_output(student_output),
        _valid_knowledge_notes(plan.items),
        _has_knowledge_or_pending(plan.items, plan.uncertain_items),
        _low_confidence_flagged(plan.items, plan.uncertain_items),
        _printable_path_present(printable_path),
    )


def check_wrong_question_review(
    review: WrongQuestionReview,
    student_output: str,
    printable_path: Path | str,
) -> tuple[CheckRow, ...]:
    return (
        _no_answers_in_student_output(student_output),
        _valid_knowledge_notes(review.items),
        _has_knowledge_or_pending(review.items, review.uncertain_items),
        _low_confidence_flagged(review.items, review.uncertain_items),
        _printable_path_present(printable_path),
        _sticker_rules_used(review.items),
    )


def check_review_plan_source(source: ReviewPlanSource) -> tuple[CheckRow, ...]:
    return (
        _valid_knowledge_notes(source.items),
        _has_knowledge_or_pending(source.items, source.uncertain_items),
        _low_confidence_flagged(source.items, source.uncertain_items),
        _sticker_rules_used(source.items),
    )


def _no_answers_in_student_output(student_output: str) -> CheckRow:
    leaked = [marker for marker in ANSWER_MARKERS if marker in student_output]
    return CheckRow(
        passed=not leaked,
        code="student_no_answers",
        message=(
            "学生输出未发现答案标记"
            if not leaked
            else f"学生输出疑似包含答案标记: {', '.join(leaked)}"
        ),
    )


def _has_knowledge_or_pending(
    items: tuple[object, ...], uncertain_items: tuple[str, ...]
) -> CheckRow:
    missing = tuple(
        _item_label(item)
        for item in items
        if not _has_real_knowledge(item)
        and not _has_flagged_pending_knowledge(item, uncertain_items)
    )
    return CheckRow(
        passed=not missing,
        code="knowledge_link_or_pending",
        message=(
            "已包含知识点链接或已标待定位项"
            if not missing
            else f"以下项目缺少知识点链接或待定位: {', '.join(missing)}"
        ),
    )


def _valid_knowledge_notes(items: tuple[object, ...]) -> CheckRow:
    invalid = tuple(
        _item_label(item)
        for item in items
        for match in _knowledge_matches(item)
        if not match.note.strip() or match.note != match.note.strip()
    )
    return CheckRow(
        passed=not invalid,
        code="knowledge_note_valid",
        message=(
            "知识点标题有效"
            if not invalid
            else f"以下项目包含空白或非法知识点标题: {', '.join(invalid)}"
        ),
    )


def _low_confidence_flagged(
    items: tuple[object, ...], uncertain_items: tuple[str, ...]
) -> CheckRow:
    unflagged = tuple(
        _item_label(item)
        for item in items
        for match in _knowledge_matches(item)
        if match.confidence == "low"
        and not _has_low_confidence_flag(item, match, uncertain_items)
    )
    return CheckRow(
        passed=not unflagged,
        code="low_confidence_flagged",
        message=(
            "低置信度内容已标给家长确认"
            if not unflagged
            else f"以下低置信度项目未进入待确认项: {', '.join(unflagged)}"
        ),
    )


def _printable_path_present(printable_path: Path | str) -> CheckRow:
    present = bool(str(printable_path))
    return CheckRow(
        passed=present,
        code="printable_path_present",
        message="打印材料路径已提供" if present else "缺少打印材料路径",
    )


def _sticker_rules_used(items: tuple[object, ...]) -> CheckRow:
    colors = {getattr(item, "sticker_color", "") for item in items}
    unknown = colors - STICKER_COLORS
    missing_action = [
        getattr(item, "question_id", "")
        for item in items
        if not getattr(item, "next_action", "")
    ]
    passed = bool(colors) and not unknown and not missing_action
    if unknown:
        message = f"存在未知贴纸颜色: {', '.join(sorted(unknown))}"
    elif missing_action:
        message = f"错题缺少贴纸归因动作: {', '.join(missing_action)}"
    elif not colors:
        message = "缺少红黄蓝贴纸归因"
    else:
        message = "错题已使用红黄蓝贴纸归因规则"
    return CheckRow(passed=passed, code="sticker_rules_used", message=message)


def _knowledge_matches(item: object) -> tuple[KnowledgeMatch, ...]:
    return getattr(item, "matched_knowledge", ())


def _has_real_knowledge(item: object) -> bool:
    return any(
        bool(match.note.strip()) and not match.is_pending
        for match in _knowledge_matches(item)
    )


def _has_flagged_pending_knowledge(
    item: object,
    uncertain_items: tuple[str, ...],
) -> bool:
    return any(match.is_pending for match in _knowledge_matches(item)) and any(
        _mentions_item(uncertain_item, item, ("待定位",))
        for uncertain_item in uncertain_items
    )


def _has_low_confidence_flag(
    item: object,
    match: KnowledgeMatch,
    uncertain_items: tuple[str, ...],
) -> bool:
    return any(
        _mentions_item(uncertain_item, item, (match.note,))
        for uncertain_item in uncertain_items
    )


def _mentions_item(
    uncertain_item: str,
    item: object,
    extra_tokens: tuple[str, ...],
) -> bool:
    text = uncertain_item.strip()
    if not text:
        return False
    return any(
        token in text or text in token
        for token in _item_tokens(item) + extra_tokens
    )


def _item_tokens(item: object) -> tuple[str, ...]:
    tokens = (
        getattr(item, "raw_text", ""),
        getattr(item, "question_id", ""),
        getattr(item, "subject", ""),
    )
    return tuple(token for token in tokens if token)


def _item_label(item: object) -> str:
    for token in _item_tokens(item):
        return token
    return getattr(item, "subject", "") or "未命名项目"
