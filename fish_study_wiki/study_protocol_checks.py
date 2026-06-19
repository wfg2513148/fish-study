from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fish_study_wiki.study_protocol_models import (
    AnalysisCluster,
    DIFFICULTY_LEVELS,
    HomeworkPlan,
    KnowledgeMatch,
    ReviewPlanSource,
    STICKER_COLORS,
    WeeklyReviewSource,
    WrongQuestionReview,
    WrongQuestionTraining,
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


def check_wrong_question_training(
    training: WrongQuestionTraining,
    student_output: str,
    answer_output: str,
    printable_path: Path | str,
    answer_path: Path | str,
) -> tuple[CheckRow, ...]:
    return (
        _no_answers_in_student_output(student_output),
        _answer_page_contains_answers(answer_output),
        _valid_knowledge_notes(training.clusters),
        _pending_items_are_uncertain(training.clusters, training.uncertain_items),
        _training_questions_present(training.clusters),
        _difficulty_mix_valid(training.clusters),
        _printable_path_present(printable_path),
        _printable_path_present(answer_path),
        _sticker_rules_used(training.clusters),
    )


def check_weekly_review(
    source: WeeklyReviewSource,
    student_output: str,
    answer_output: str,
    report_path: Path | str,
    printable_path: Path | str,
    answer_path: Path | str,
) -> tuple[CheckRow, ...]:
    return (
        _no_answers_in_student_output(student_output),
        _answer_page_contains_answers(answer_output),
        _valid_knowledge_notes(source.events),
        _pending_items_are_uncertain(source.events, source.uncertain_items),
        _training_questions_present(source.events),
        _difficulty_mix_valid(source.events),
        _printable_path_present(report_path),
        _printable_path_present(printable_path),
        _printable_path_present(answer_path),
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


def _answer_page_contains_answers(answer_output: str) -> CheckRow:
    present = [marker for marker in ANSWER_MARKERS if marker in answer_output]
    return CheckRow(
        passed=bool(present),
        code="answer_page_contains_answers",
        message="答案页包含答案标记" if present else "答案页缺少答案标记",
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
    missing_confirmed = tuple(
        _item_label(item)
        for item in items
        if _is_confirmed_for_statistics(item) and not _has_real_knowledge(item)
    )
    return CheckRow(
        passed=not invalid and not missing_confirmed,
        code="knowledge_note_valid",
        message=_knowledge_note_message(invalid, missing_confirmed),
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
    colors = {_sticker_color(item) for item in items}
    unknown = colors - STICKER_COLORS
    missing_action = [
        getattr(item, "question_id", "")
        for item in items
        if hasattr(item, "next_action") and not getattr(item, "next_action", "")
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


def _pending_items_are_uncertain(
    clusters: tuple[AnalysisCluster, ...],
    uncertain_items: tuple[str, ...],
) -> CheckRow:
    missing = tuple(
        _item_label(cluster)
        for cluster in clusters
        if _requires_confirmation(cluster)
        and not any(_mentions_cluster(item, cluster) for item in uncertain_items)
    )
    return CheckRow(
        passed=not missing,
        code="pending_items_are_uncertain",
        message=(
            "待确认诊断已隔离"
            if not missing
            else f"以下待确认诊断未进入待确认项: {', '.join(missing)}"
        ),
    )


def _training_questions_present(
    clusters: tuple[AnalysisCluster, ...],
) -> CheckRow:
    missing = tuple(
        _item_label(cluster) for cluster in clusters if not cluster.training_questions
    )
    return CheckRow(
        passed=not missing,
        code="training_questions_present",
        message=(
            "每个分析组合都有训练题"
            if not missing
            else f"以下分析组合缺少训练题: {', '.join(missing)}"
        ),
    )


def _difficulty_mix_valid(
    clusters: tuple[AnalysisCluster, ...],
) -> CheckRow:
    invalid = []
    for cluster in clusters:
        if not cluster.difficulty_mix:
            invalid.append(f"{_item_label(cluster)} 缺少难度梯度")
        elif any(
            difficulty not in DIFFICULTY_LEVELS for difficulty in cluster.difficulty_mix
        ):
            invalid.append(f"{_item_label(cluster)} 包含未知难度")
        elif _challenge_question_not_declared(cluster):
            invalid.append(f"{_item_label(cluster)} 挑战题未纳入难度梯度")
        elif _challenge_only(cluster):
            invalid.append(f"{_item_label(cluster)} 只有挑战题")
        elif _challenge_without_foundation(cluster):
            invalid.append(f"{_item_label(cluster)} 挑战题缺少基础/标准铺垫")
    return CheckRow(
        passed=not invalid,
        code="difficulty_mix_valid",
        message="难度梯度可用于校准掌握度" if not invalid else "; ".join(invalid),
    )


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


def _mentions_cluster(uncertain_item: str, cluster: AnalysisCluster) -> bool:
    text = uncertain_item.strip()
    if not text:
        return False
    diagnosis = cluster.diagnosis
    required = (
        cluster.subject,
        cluster.problem_type,
        diagnosis.secondary_reason,
    )
    return all(token and token in text for token in required)


def _item_tokens(item: object) -> tuple[str, ...]:
    diagnosis = getattr(item, "diagnosis", None)
    tokens = (
        getattr(item, "raw_text", ""),
        getattr(item, "question_id", ""),
        getattr(item, "subject", ""),
        getattr(item, "problem_type", ""),
        getattr(diagnosis, "secondary_reason", ""),
    )
    return tuple(token for token in tokens if token)


def _item_label(item: object) -> str:
    for token in _item_tokens(item):
        return token
    return getattr(item, "subject", "") or "未命名项目"


def _requires_confirmation(cluster: AnalysisCluster) -> bool:
    diagnosis = cluster.diagnosis
    return (
        diagnosis.confidence in {"medium", "low"}
        or diagnosis.confirmation_status == "needs_confirmation"
    )


def _challenge_only(cluster: AnalysisCluster) -> bool:
    return set(_difficulty_sequence(cluster)) == {"challenge"}


def _challenge_without_foundation(cluster: AnalysisCluster) -> bool:
    sequence = _difficulty_sequence(cluster)
    if "challenge" not in sequence:
        return False
    before_challenge = sequence[: sequence.index("challenge")]
    return not {"basic", "standard"}.issubset(set(before_challenge))


def _challenge_question_not_declared(cluster: AnalysisCluster) -> bool:
    has_challenge_question = any(
        question.difficulty == "challenge" for question in cluster.training_questions
    )
    return has_challenge_question and "challenge" not in cluster.difficulty_mix


def _difficulty_sequence(cluster: AnalysisCluster) -> tuple[str, ...]:
    return cluster.difficulty_mix + tuple(
        question.difficulty
        for question in cluster.training_questions
        if question.difficulty not in cluster.difficulty_mix
    )


def _is_confirmed_for_statistics(item: object) -> bool:
    diagnosis = getattr(item, "diagnosis", None)
    if diagnosis is None:
        return False
    return (
        diagnosis.confirmation_status in {"auto", "confirmed"}
        and diagnosis.confidence == "high"
    )


def _sticker_color(item: object) -> str:
    diagnosis = getattr(item, "diagnosis", None)
    return getattr(diagnosis, "sticker_color", getattr(item, "sticker_color", ""))


def _knowledge_note_message(
    invalid: tuple[str, ...],
    missing_confirmed: tuple[str, ...],
) -> str:
    if invalid:
        return f"以下项目包含空白或非法知识点标题: {', '.join(invalid)}"
    if missing_confirmed:
        return f"以下已确认项目缺少知识点标题: {', '.join(missing_confirmed)}"
    return "知识点标题有效"
