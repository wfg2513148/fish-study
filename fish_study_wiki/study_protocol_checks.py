from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from fish_study_wiki.study_protocol_models import (
    AnalysisCluster,
    DIFFICULTY_LEVELS,
    KnowledgeMatch,
    SourcePhoto,
    STICKER_COLORS,
    WeeklyReviewSource,
    WrongQuestionTraining,
)


ANSWER_MARKERS = ("答案", "参考答案", "解析", "解答")
KNOWLEDGE_CARD_FORBIDDEN_PATTERNS = (
    r"photo-",
    r"照片",
    r"来源",
    r"文件名",
    r"第[0-9一二三四五六七八九十]+题",
    r"本题",
    r"本次错题",
    r"这道题",
    r"题目中",
    r"根据照片",
    r"错因",
    r"依据",
    r"诊断",
    r"训练建议",
    r"难度梯度",
    r"红色",
    r"黄色",
    r"蓝色",
    r"sticker",
    r"source_batch",
    r"question_id",
)


@dataclass(frozen=True)
class CheckRow:
    passed: bool
    code: str
    message: str


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
        _source_photos_are_uncertain(training.source_photos, training.uncertain_items),
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


def check_subject_knowledge_cards_output(
    markdown_output: str,
    html_output: str,
) -> tuple[CheckRow, ...]:
    return (
        _knowledge_card_has_title(markdown_output, html_output),
        _knowledge_card_has_diagram(html_output),
        _knowledge_card_image_labels_are_concept_only(html_output),
        _knowledge_card_no_forbidden_text(markdown_output, "markdown"),
        _knowledge_card_no_forbidden_text(html_output, "html"),
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


def _knowledge_card_has_title(markdown_output: str, html_output: str) -> CheckRow:
    passed = "知识点复习卡" in markdown_output and "知识点复习卡" in html_output
    return CheckRow(
        passed=passed,
        code="knowledge_card_has_title",
        message="知识点复习卡标题存在" if passed else "知识点复习卡标题缺失",
    )


def _knowledge_card_has_diagram(html_output: str) -> CheckRow:
    passed = (
        ("<img" not in html_output or 'data-generator="gpt-image-2"' in html_output)
        and "<svg" not in html_output
        and "原题" not in html_output
        and "配图待生成" not in html_output
    )
    return CheckRow(
        passed=passed,
        code="knowledge_card_has_diagram",
        message=(
            "知识点卡片未使用占位图或非 gpt-image-2 图片"
            if passed
            else "知识点卡片仍使用占位图、SVG 或非 gpt-image-2 图片"
        ),
    )


def _knowledge_card_no_forbidden_text(output: str, label: str) -> CheckRow:
    leaked = forbidden_knowledge_card_matches(output)
    return CheckRow(
        passed=not leaked,
        code=f"knowledge_card_no_forbidden_text_{label}",
        message=(
            f"{label} 未发现题号/照片/错因等诊断噪声"
            if not leaked
            else f"{label} 疑似包含诊断噪声: {', '.join(leaked)}"
        ),
    )


def _knowledge_card_image_labels_are_concept_only(html_output: str) -> CheckRow:
    image_labels = tuple(
        re.findall(r'alt="([^"]*)"', html_output)
        + re.findall(r"<figcaption>(.*?)</figcaption>", html_output, flags=re.S)
    )
    leaked = tuple(
        label.strip()
        for label in image_labels
        if re.search(
            r"第[0-9一二三四五六七八九十]+(?:章|节|课时)|专题[0-9一二三四五六七八九十]+",
            label,
        )
    )
    return CheckRow(
        passed=not leaked,
        code="knowledge_card_image_labels_are_concept_only",
        message=(
            "知识点图片标签未发现章节节次说明"
            if not leaked
            else f"知识点图片标签包含章节节次说明: {', '.join(leaked)}"
        ),
    )


def forbidden_knowledge_card_matches(output: str) -> tuple[str, ...]:
    return tuple(
        pattern
        for pattern in KNOWLEDGE_CARD_FORBIDDEN_PATTERNS
        if re.search(pattern, output, flags=re.I)
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


def _source_photos_are_uncertain(
    source_photos: tuple[SourcePhoto, ...],
    uncertain_items: tuple[str, ...],
) -> CheckRow:
    missing = tuple(
        photo.photo_id
        for photo in source_photos
        if _photo_requires_confirmation(photo)
        and not any(_mentions_photo(item, photo) for item in uncertain_items)
    )
    return CheckRow(
        passed=not missing,
        code="source_photos_are_uncertain",
        message=(
            "待确认照片已隔离"
            if not missing
            else f"以下待确认照片未进入待确认项: {', '.join(missing)}"
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
    known = colors & {"red", "yellow", "blue"}
    passed = bool(colors) and bool(known) and not unknown
    if unknown:
        message = f"存在未知贴纸颜色: {', '.join(sorted(unknown))}"
    elif not known:
        message = "缺少可自动归因的红黄蓝贴纸"
    elif not colors:
        message = "缺少红黄蓝贴纸归因"
    else:
        message = "错题已使用红黄蓝贴纸归因规则，歧义颜色已隔离"
    return CheckRow(passed=passed, code="sticker_rules_used", message=message)


def _knowledge_matches(item: object) -> tuple[KnowledgeMatch, ...]:
    return getattr(item, "matched_knowledge", ())


def _has_real_knowledge(item: object) -> bool:
    return any(
        bool(match.note.strip()) and not match.is_pending
        for match in _knowledge_matches(item)
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
        getattr(item, "subject", ""),
        getattr(item, "problem_type", ""),
        getattr(diagnosis, "secondary_reason", ""),
    )
    return tuple(token for token in tokens if token)


def _item_label(item: object) -> str:
    return " ".join(_item_tokens(item)) or "未命名项目"


def _requires_confirmation(cluster: AnalysisCluster) -> bool:
    diagnosis = cluster.diagnosis
    return (
        diagnosis.confidence in {"medium", "low"}
        or diagnosis.confirmation_status == "needs_confirmation"
    )


def _photo_requires_confirmation(photo: SourcePhoto) -> bool:
    return (
        photo.status == "needs_confirmation"
        or photo.subject == "unknown"
        or photo.confidence in {"medium", "low"}
    )


def _mentions_photo(uncertain_item: str, photo: SourcePhoto) -> bool:
    text = uncertain_item.strip()
    return bool(
        text
        and (
            photo.photo_id in text
            or (photo.label_or_filename and photo.label_or_filename in text)
        )
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
        and diagnosis.sticker_color in {"red", "yellow", "blue"}
    )


def _sticker_color(item: object) -> str:
    diagnosis = getattr(item, "diagnosis", None)
    return getattr(diagnosis, "sticker_color", "")


def _knowledge_note_message(
    invalid: tuple[str, ...],
    missing_confirmed: tuple[str, ...],
) -> str:
    if invalid:
        return f"以下项目包含空白或非法知识点标题: {', '.join(invalid)}"
    if missing_confirmed:
        return f"以下已确认项目缺少知识点标题: {', '.join(missing_confirmed)}"
    return "知识点标题有效"
