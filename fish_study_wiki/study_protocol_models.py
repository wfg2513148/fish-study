from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
from typing import Any


STICKER_COLORS = {"red", "yellow", "blue", "unknown"}
VISUAL_COLOR_VALUES = {"red", "yellow", "blue", "unknown"}
MARK_TYPES = {"sticker", "marker", "circle", "underline", "unknown"}
CONFIDENCE_VALUES = {"high", "medium", "low"}
CONFIRMATION_STATUSES = {"auto", "needs_confirmation", "confirmed", "excluded"}
DIFFICULTY_LEVELS = {"basic", "standard", "variant", "challenge"}
COMPLETION_STATUSES = {"completed", "overtime", "unfinished"}
PHOTO_STATUSES = {"recognized", "needs_confirmation", "excluded"}
PHOTO_SUBJECTS = {"数学", "科学", "英语", "unknown"}
PRIMARY_REASONS_BY_COLOR = {
    "red": "不会",
    "yellow": "马虎",
    "blue": "时间不够",
    "unknown": "待确认",
}
SECONDARY_REASONS_BY_COLOR = {
    "red": {"概念不清", "方法不会", "条件转化失败", "迁移失败"},
    "yellow": {"审题漏条件", "计算错误", "单位/符号错误", "步骤书写问题"},
    "blue": {
        "读题慢",
        "路径选择慢",
        "计算耗时",
        "卡在第一步",
        "时间分配不当",
    },
    "unknown": {"待确认"},
}


@dataclass(frozen=True)
class KnowledgeMatch:
    grade: str
    volume: str
    chapter: str
    note: str
    confidence: str

    @property
    def is_pending(self) -> bool:
        return self.note == "待定位"


@dataclass(frozen=True)
class Diagnosis:
    sticker_color: str
    primary_reason: str
    secondary_reason: str
    evidence: str
    confidence: str
    confirmation_status: str
    visual_mark: "VisualMark | None" = None


@dataclass(frozen=True)
class VisualMark:
    color_detected: str
    color_normalized: str
    mark_type: str
    evidence: str
    confidence: str


@dataclass(frozen=True)
class SourcePhoto:
    photo_id: str
    label_or_filename: str
    subject: str
    confidence: str
    evidence: str
    status: str


@dataclass(frozen=True)
class TrainingQuestion:
    prompt: str
    difficulty: str
    target_reason: str
    answer: str
    scoring_points: tuple[str, ...]
    mastery_signal: str


@dataclass(frozen=True)
class AnalysisCluster:
    subject: str
    problem_type: str
    diagnosis: Diagnosis
    matched_knowledge: tuple[KnowledgeMatch, ...]
    training_questions: tuple[TrainingQuestion, ...]
    difficulty_mix: tuple[str, ...]
    source_photo_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class WrongQuestionTraining:
    task_type: str
    date: str
    source_batch: str
    clusters: tuple[AnalysisCluster, ...]
    uncertain_items: tuple[str, ...]
    source_photos: tuple[SourcePhoto, ...] = ()


@dataclass(frozen=True)
class TrainingResult:
    date: str
    subject: str
    knowledge_note: str
    problem_type: str
    secondary_reason: str
    difficulty: str
    correct_rate: float
    elapsed_minutes: int
    target_minutes: int
    completion_status: str
    major_error: str
    next_difficulty: str
    review_window: str
    due_date: str
    review_result: str
    status: str


@dataclass(frozen=True)
class WeeklyReviewSource:
    task_type: str
    week_start: str
    week_end: str
    events: tuple[AnalysisCluster, ...]
    results: tuple[TrainingResult, ...]
    review_queue: tuple[TrainingResult, ...]
    uncertain_items: tuple[str, ...]


def load_wrong_question_training(path: Path | str) -> WrongQuestionTraining:
    data = _load_json(path)
    _require_task_type(data, "wrong_question_training")
    source_photos = tuple(
        _source_photo(item)
        for item in _list(data.get("source_photos", []), "source_photos")
    )
    clusters = tuple(
        _analysis_cluster(item)
        for item in _list(data.get("clusters", []), "clusters")
    )
    uncertain_items = _string_tuple(data.get("uncertain_items", []))
    _validate_source_photos(source_photos, clusters, uncertain_items)
    return WrongQuestionTraining(
        task_type=data["task_type"],
        date=_iso_date(data.get("date", "")),
        source_batch=str(data.get("source_batch", "")),
        clusters=clusters,
        uncertain_items=uncertain_items,
        source_photos=source_photos,
    )


def load_weekly_review_source(path: Path | str) -> WeeklyReviewSource:
    data = _load_json(path)
    _require_task_type(data, "weekly_review")
    week_start = _iso_date(data.get("week_start", ""))
    week_end = _iso_date(data.get("week_end", ""))
    if date.fromisoformat(week_start) > date.fromisoformat(week_end):
        raise ValueError("week_start must be before or equal to week_end")
    return WeeklyReviewSource(
        task_type=data["task_type"],
        week_start=week_start,
        week_end=week_end,
        events=tuple(
            _analysis_cluster(item)
            for item in _list(data.get("events", []), "events")
        ),
        results=tuple(
            _training_result(item)
            for item in _list(data.get("results", []), "results")
        ),
        review_queue=tuple(
            _training_result(item)
            for item in _list(data.get("review_queue", []), "review_queue")
        ),
        uncertain_items=_string_tuple(data.get("uncertain_items", [])),
    )


def normalize_sticker_color(color: str) -> str:
    normalized = color.strip().lower()
    if normalized not in STICKER_COLORS:
        raise ValueError(f"unknown sticker_color {color!r}")
    return normalized


def _load_json(path: Path | str) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("study protocol input must be a JSON object")
    return data


def _require_task_type(data: dict[str, Any], expected: str) -> None:
    actual = data.get("task_type")
    if actual != expected:
        raise ValueError(f"unknown task_type {actual!r}, expected {expected!r}")


def _iso_date(value: Any) -> str:
    text = str(value)
    try:
        parsed = date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"invalid date {text!r}, expected YYYY-MM-DD") from exc
    if parsed.isoformat() != text:
        raise ValueError(f"invalid date {text!r}, expected YYYY-MM-DD")
    return text


def _knowledge_match(data: dict[str, Any]) -> KnowledgeMatch:
    data = _object(data, "knowledge match")
    return KnowledgeMatch(
        grade=str(data.get("grade", "")),
        volume=str(data.get("volume", "")),
        chapter=str(data.get("chapter", "")),
        note=str(data.get("note", "")),
        confidence=_known_value("confidence", data.get("confidence", ""), CONFIDENCE_VALUES),
    )


def _diagnosis(data: dict[str, Any]) -> Diagnosis:
    data = _object(data, "diagnosis")
    sticker_color = normalize_sticker_color(str(data.get("sticker_color", "")))
    primary_reason = str(data.get("primary_reason", ""))
    secondary_reason = str(data.get("secondary_reason", ""))
    confidence = _known_value("confidence", data.get("confidence", ""), CONFIDENCE_VALUES)
    confirmation_status = _known_value(
        "confirmation_status",
        data.get("confirmation_status", ""),
        CONFIRMATION_STATUSES,
    )
    _validate_reason_pair(sticker_color, primary_reason, secondary_reason)
    _validate_confirmation(confidence, confirmation_status)
    _validate_unknown_diagnosis(sticker_color, confidence, confirmation_status)
    visual_mark = _optional_visual_mark(data.get("visual_mark"))
    _validate_visual_mark_mapping(sticker_color, visual_mark)
    return Diagnosis(
        sticker_color=sticker_color,
        primary_reason=primary_reason,
        secondary_reason=secondary_reason,
        evidence=str(data.get("evidence", "")),
        confidence=confidence,
        confirmation_status=confirmation_status,
        visual_mark=visual_mark,
    )


def _optional_visual_mark(data: Any) -> VisualMark | None:
    if data is None:
        return None
    data = _object(data, "visual mark")
    return VisualMark(
        color_detected=str(data.get("color_detected", "")),
        color_normalized=_known_value(
            "color_normalized",
            data.get("color_normalized", ""),
            VISUAL_COLOR_VALUES,
        ),
        mark_type=_known_value("mark_type", data.get("mark_type", ""), MARK_TYPES),
        evidence=str(data.get("evidence", "")),
        confidence=_known_value("confidence", data.get("confidence", ""), CONFIDENCE_VALUES),
    )


def _training_question(data: dict[str, Any]) -> TrainingQuestion:
    data = _object(data, "training question")
    return TrainingQuestion(
        prompt=str(data.get("prompt", "")),
        difficulty=_known_value("difficulty", data.get("difficulty", ""), DIFFICULTY_LEVELS),
        target_reason=str(data.get("target_reason", "")),
        answer=str(data.get("answer", "")),
        scoring_points=_string_tuple(data.get("scoring_points", [])),
        mastery_signal=str(data.get("mastery_signal", "")),
    )


def _source_photo(data: dict[str, Any]) -> SourcePhoto:
    data = _object(data, "source photo")
    return SourcePhoto(
        photo_id=str(data.get("photo_id", "")),
        label_or_filename=str(data.get("label_or_filename", "")),
        subject=_known_value("subject", data.get("subject", ""), PHOTO_SUBJECTS),
        confidence=_known_value("confidence", data.get("confidence", ""), CONFIDENCE_VALUES),
        evidence=str(data.get("evidence", "")),
        status=_known_value("status", data.get("status", ""), PHOTO_STATUSES),
    )


def _analysis_cluster(data: dict[str, Any]) -> AnalysisCluster:
    data = _object(data, "analysis cluster")
    return AnalysisCluster(
        subject=str(data.get("subject", "")),
        problem_type=str(data.get("problem_type", "")),
        diagnosis=_diagnosis(data.get("diagnosis", {})),
        matched_knowledge=tuple(
            _knowledge_match(match)
            for match in _list(data.get("matched_knowledge", []), "matched_knowledge")
        ),
        training_questions=tuple(
            _training_question(question)
            for question in _list(data.get("training_questions", []), "training_questions")
        ),
        difficulty_mix=tuple(
            _known_value("difficulty", item, DIFFICULTY_LEVELS)
            for item in _list(data.get("difficulty_mix", []), "difficulty_mix")
        ),
        source_photo_ids=_string_tuple(data.get("source_photo_ids", [])),
    )


def _training_result(data: dict[str, Any]) -> TrainingResult:
    data = _object(data, "training result")
    correct_rate = _float(data.get("correct_rate", 0), "correct_rate")
    elapsed_minutes = _int(data.get("elapsed_minutes", 0), "elapsed_minutes")
    target_minutes = _int(data.get("target_minutes", 0), "target_minutes")
    if not 0 <= correct_rate <= 1:
        raise ValueError("correct_rate must be between 0 and 1")
    if elapsed_minutes < 0 or target_minutes < 0:
        raise ValueError("elapsed_minutes and target_minutes must be non-negative")
    return TrainingResult(
        date=_iso_date(data.get("date", "")),
        subject=str(data.get("subject", "")),
        knowledge_note=str(data.get("knowledge_note", "")),
        problem_type=str(data.get("problem_type", "")),
        secondary_reason=_known_secondary_reason(str(data.get("secondary_reason", ""))),
        difficulty=_known_value("difficulty", data.get("difficulty", ""), DIFFICULTY_LEVELS),
        correct_rate=correct_rate,
        elapsed_minutes=elapsed_minutes,
        target_minutes=target_minutes,
        completion_status=_known_value(
            "completion_status",
            data.get("completion_status", ""),
            COMPLETION_STATUSES,
        ),
        major_error=str(data.get("major_error", "")),
        next_difficulty=_known_value(
            "next_difficulty",
            data.get("next_difficulty", ""),
            DIFFICULTY_LEVELS,
        ),
        review_window=str(data.get("review_window", "")),
        due_date=_iso_date(data.get("due_date", "")),
        review_result=str(data.get("review_result", "")),
        status=str(data.get("status", "")),
    )


def _string_tuple(value: Any) -> tuple[str, ...]:
    value = _list(value, "string list")
    return tuple(str(item) for item in value)


def _known_value(name: str, value: Any, allowed: set[str]) -> str:
    text = str(value)
    if text not in allowed:
        expected = "/".join(sorted(allowed))
        raise ValueError(f"unknown {name} {text!r}, expected {expected}")
    return text


def _object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object")
    return value


def _list(value: Any, name: str) -> list[Any] | tuple[Any, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{name} must be a JSON array")
    return value


def _float(value: Any, name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number") from exc


def _int(value: Any, name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _validate_reason_pair(
    sticker_color: str,
    primary_reason: str,
    secondary_reason: str,
) -> None:
    expected_primary = PRIMARY_REASONS_BY_COLOR[sticker_color]
    if primary_reason != expected_primary:
        raise ValueError(
            f"primary_reason {primary_reason!r} does not match {sticker_color}"
        )
    allowed_secondary = SECONDARY_REASONS_BY_COLOR[sticker_color]
    if secondary_reason not in allowed_secondary:
        expected = "/".join(sorted(allowed_secondary))
        raise ValueError(
            f"secondary_reason {secondary_reason!r} does not match "
            f"{sticker_color}, expected {expected}"
        )


def _validate_confirmation(confidence: str, confirmation_status: str) -> None:
    if confidence == "low" and confirmation_status != "needs_confirmation":
        raise ValueError("low confidence diagnosis must need confirmation")
    if confidence == "medium" and confirmation_status == "auto":
        raise ValueError("medium confidence diagnosis cannot be auto-confirmed")


def _validate_unknown_diagnosis(
    sticker_color: str,
    confidence: str,
    confirmation_status: str,
) -> None:
    if sticker_color != "unknown":
        return
    if confidence == "high" or confirmation_status != "needs_confirmation":
        raise ValueError("unknown color diagnosis must need confirmation")


def _validate_visual_mark_mapping(
    sticker_color: str,
    visual_mark: VisualMark | None,
) -> None:
    if visual_mark is None:
        return
    if visual_mark.color_normalized != sticker_color:
        raise ValueError(
            "visual_mark.color_normalized must match sticker_color; "
            "use unknown for ambiguous colors"
        )
    if visual_mark.color_normalized == "unknown":
        if visual_mark.confidence == "high":
            raise ValueError("unknown visual color cannot have high confidence")


def _validate_source_photos(
    source_photos: tuple[SourcePhoto, ...],
    clusters: tuple[AnalysisCluster, ...],
    uncertain_items: tuple[str, ...],
) -> None:
    by_id: dict[str, SourcePhoto] = {}
    for photo in source_photos:
        if not photo.photo_id.strip():
            raise ValueError("source photo photo_id must not be empty")
        if photo.photo_id in by_id:
            raise ValueError(f"duplicate source photo id {photo.photo_id!r}")
        by_id[photo.photo_id] = photo
        if _photo_requires_confirmation(photo) and not _photo_is_uncertain(
            photo,
            uncertain_items,
        ):
            raise ValueError(
                f"source photo {photo.photo_id!r} needs confirmation "
                "but is missing from uncertain_items"
            )

    for cluster in clusters:
        for photo_id in cluster.source_photo_ids:
            photo = by_id.get(photo_id)
            if photo is None:
                raise ValueError(f"unknown source photo id {photo_id!r}")
            if photo.status != "recognized":
                raise ValueError(
                    f"cluster {cluster.subject} references unconfirmed photo {photo_id!r}"
                )
            if photo.subject != cluster.subject:
                raise ValueError(
                    f"cluster subject {cluster.subject!r} does not match "
                    f"source photo {photo_id!r} subject {photo.subject!r}"
                )


def _photo_requires_confirmation(photo: SourcePhoto) -> bool:
    return (
        photo.status == "needs_confirmation"
        or photo.subject == "unknown"
        or photo.confidence in {"medium", "low"}
    )


def _photo_is_uncertain(
    photo: SourcePhoto,
    uncertain_items: tuple[str, ...],
) -> bool:
    tokens = (photo.photo_id, photo.label_or_filename)
    for item in uncertain_items:
        if any(token and token in item for token in tokens):
            return True
    return False


def _known_secondary_reason(value: str) -> str:
    allowed = set().union(*SECONDARY_REASONS_BY_COLOR.values())
    return _known_value("secondary_reason", value, allowed)
