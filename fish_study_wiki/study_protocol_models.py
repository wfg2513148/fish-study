from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
from typing import Any


STICKER_COLORS = {"red", "yellow", "blue"}
CONFIDENCE_VALUES = {"high", "medium", "low"}
CONFIRMATION_STATUSES = {"auto", "needs_confirmation", "confirmed", "excluded"}
DIFFICULTY_LEVELS = {"basic", "standard", "variant", "challenge"}


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
class HomeworkItem:
    subject: str
    raw_text: str
    book_or_source: str
    page: str
    question_range: str
    deadline: str
    matched_knowledge: tuple[KnowledgeMatch, ...]
    status: str


@dataclass(frozen=True)
class HomeworkPlan:
    task_type: str
    date: str
    items: tuple[HomeworkItem, ...]
    uncertain_items: tuple[str, ...]


@dataclass(frozen=True)
class WrongQuestionItem:
    subject: str
    question_id: str
    sticker_color: str
    reason: str
    problem_type: str
    matched_knowledge: tuple[KnowledgeMatch, ...]
    next_action: str


@dataclass(frozen=True)
class WrongQuestionReview:
    task_type: str
    date: str
    items: tuple[WrongQuestionItem, ...]
    uncertain_items: tuple[str, ...]


@dataclass(frozen=True)
class ReviewPlanSource:
    task_type: str
    date: str
    items: tuple[WrongQuestionItem, ...]
    uncertain_items: tuple[str, ...]


@dataclass(frozen=True)
class Diagnosis:
    sticker_color: str
    primary_reason: str
    secondary_reason: str
    evidence: str
    confidence: str
    confirmation_status: str


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


@dataclass(frozen=True)
class WrongQuestionTraining:
    task_type: str
    date: str
    source_batch: str
    clusters: tuple[AnalysisCluster, ...]
    uncertain_items: tuple[str, ...]


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


def load_homework_plan(path: Path | str) -> HomeworkPlan:
    data = _load_json(path)
    _require_task_type(data, "homework_plan")
    return HomeworkPlan(
        task_type=data["task_type"],
        date=_iso_date(data.get("date", "")),
        items=tuple(_homework_item(item) for item in data.get("items", [])),
        uncertain_items=_string_tuple(data.get("uncertain_items", [])),
    )


def load_wrong_question_review(path: Path | str) -> WrongQuestionReview:
    data = _load_json(path)
    _require_task_type(data, "wrong_question_review")
    return WrongQuestionReview(
        task_type=data["task_type"],
        date=_iso_date(data.get("date", "")),
        items=tuple(_wrong_question_item(item) for item in data.get("items", [])),
        uncertain_items=_string_tuple(data.get("uncertain_items", [])),
    )


def load_review_plan_source(path: Path | str) -> ReviewPlanSource:
    data = _load_json(path)
    _require_task_type(data, "review_plan_source")
    return ReviewPlanSource(
        task_type=data["task_type"],
        date=_iso_date(data.get("date", "")),
        items=tuple(_wrong_question_item(item) for item in data.get("items", [])),
        uncertain_items=_string_tuple(data.get("uncertain_items", [])),
    )


def load_wrong_question_training(path: Path | str) -> WrongQuestionTraining:
    data = _load_json(path)
    _require_task_type(data, "wrong_question_training")
    return WrongQuestionTraining(
        task_type=data["task_type"],
        date=_iso_date(data.get("date", "")),
        source_batch=str(data.get("source_batch", "")),
        clusters=tuple(_analysis_cluster(item) for item in data.get("clusters", [])),
        uncertain_items=_string_tuple(data.get("uncertain_items", [])),
    )


def load_weekly_review_source(path: Path | str) -> WeeklyReviewSource:
    data = _load_json(path)
    _require_task_type(data, "weekly_review")
    return WeeklyReviewSource(
        task_type=data["task_type"],
        week_start=_iso_date(data.get("week_start", "")),
        week_end=_iso_date(data.get("week_end", "")),
        events=tuple(_analysis_cluster(item) for item in data.get("events", [])),
        results=tuple(_training_result(item) for item in data.get("results", [])),
        review_queue=tuple(
            _training_result(item) for item in data.get("review_queue", [])
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
    return KnowledgeMatch(
        grade=str(data.get("grade", "")),
        volume=str(data.get("volume", "")),
        chapter=str(data.get("chapter", "")),
        note=str(data.get("note", "")),
        confidence=_known_value(
            "confidence",
            data.get("confidence", ""),
            CONFIDENCE_VALUES,
        ),
    )


def _homework_item(data: dict[str, Any]) -> HomeworkItem:
    return HomeworkItem(
        subject=str(data.get("subject", "")),
        raw_text=str(data.get("raw_text", "")),
        book_or_source=str(data.get("book_or_source", "")),
        page=str(data.get("page", "")),
        question_range=str(data.get("question_range", "")),
        deadline=str(data.get("deadline", "")),
        matched_knowledge=tuple(
            _knowledge_match(match) for match in data.get("matched_knowledge", [])
        ),
        status=str(data.get("status", "")),
    )


def _wrong_question_item(data: dict[str, Any]) -> WrongQuestionItem:
    return WrongQuestionItem(
        subject=str(data.get("subject", "")),
        question_id=str(data.get("question_id", "")),
        sticker_color=normalize_sticker_color(str(data.get("sticker_color", ""))),
        reason=str(data.get("reason", "")),
        problem_type=str(data.get("problem_type", "")),
        matched_knowledge=tuple(
            _knowledge_match(match) for match in data.get("matched_knowledge", [])
        ),
        next_action=str(data.get("next_action", "")),
    )


def _diagnosis(data: dict[str, Any]) -> Diagnosis:
    return Diagnosis(
        sticker_color=normalize_sticker_color(str(data.get("sticker_color", ""))),
        primary_reason=str(data.get("primary_reason", "")),
        secondary_reason=str(data.get("secondary_reason", "")),
        evidence=str(data.get("evidence", "")),
        confidence=_known_value(
            "confidence",
            data.get("confidence", ""),
            CONFIDENCE_VALUES,
        ),
        confirmation_status=_known_value(
            "confirmation_status",
            data.get("confirmation_status", ""),
            CONFIRMATION_STATUSES,
        ),
    )


def _training_question(data: dict[str, Any]) -> TrainingQuestion:
    return TrainingQuestion(
        prompt=str(data.get("prompt", "")),
        difficulty=_known_value(
            "difficulty",
            data.get("difficulty", ""),
            DIFFICULTY_LEVELS,
        ),
        target_reason=str(data.get("target_reason", "")),
        answer=str(data.get("answer", "")),
        scoring_points=_string_tuple(data.get("scoring_points", [])),
        mastery_signal=str(data.get("mastery_signal", "")),
    )


def _analysis_cluster(data: dict[str, Any]) -> AnalysisCluster:
    return AnalysisCluster(
        subject=str(data.get("subject", "")),
        problem_type=str(data.get("problem_type", "")),
        diagnosis=_diagnosis(data.get("diagnosis", {})),
        matched_knowledge=tuple(
            _knowledge_match(match) for match in data.get("matched_knowledge", [])
        ),
        training_questions=tuple(
            _training_question(question)
            for question in data.get("training_questions", [])
        ),
        difficulty_mix=tuple(
            _known_value("difficulty", item, DIFFICULTY_LEVELS)
            for item in data.get("difficulty_mix", [])
        ),
    )


def _training_result(data: dict[str, Any]) -> TrainingResult:
    return TrainingResult(
        date=_iso_date(data.get("date", "")),
        subject=str(data.get("subject", "")),
        knowledge_note=str(data.get("knowledge_note", "")),
        problem_type=str(data.get("problem_type", "")),
        secondary_reason=str(data.get("secondary_reason", "")),
        difficulty=_known_value(
            "difficulty",
            data.get("difficulty", ""),
            DIFFICULTY_LEVELS,
        ),
        correct_rate=float(data.get("correct_rate", 0)),
        elapsed_minutes=int(data.get("elapsed_minutes", 0)),
        status=str(data.get("status", "")),
    )


def _string_tuple(value: Any) -> tuple[str, ...]:
    return tuple(str(item) for item in value)


def _known_value(name: str, value: Any, allowed: set[str]) -> str:
    text = str(value)
    if text not in allowed:
        expected = "/".join(sorted(allowed))
        raise ValueError(f"unknown {name} {text!r}, expected {expected}")
    return text
