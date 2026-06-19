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
        _has_knowledge_or_pending(review.items, review.uncertain_items),
        _low_confidence_flagged(review.items, review.uncertain_items),
        _printable_path_present(printable_path),
        _sticker_rules_used(review.items),
    )


def check_review_plan_source(source: ReviewPlanSource) -> tuple[CheckRow, ...]:
    return (
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
    has_knowledge = any(_knowledge_matches(item) for item in items)
    has_pending = bool(uncertain_items) or any(
        match.is_pending for item in items for match in _knowledge_matches(item)
    )
    return CheckRow(
        passed=has_knowledge or has_pending,
        code="knowledge_link_or_pending",
        message=(
            "已包含知识点链接或待定位项"
            if has_knowledge or has_pending
            else "缺少知识点链接，也未列出待定位"
        ),
    )


def _low_confidence_flagged(
    items: tuple[object, ...], uncertain_items: tuple[str, ...]
) -> CheckRow:
    low_matches = [
        match
        for item in items
        for match in _knowledge_matches(item)
        if match.confidence == "low"
    ]
    flagged = bool(uncertain_items) or all(match.is_pending for match in low_matches)
    passed = not low_matches or flagged
    return CheckRow(
        passed=passed,
        code="low_confidence_flagged",
        message=(
            "低置信度内容已标给家长确认"
            if passed
            else "存在低置信度知识点，但未进入待确认项"
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
