from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
from typing import Any


STICKER_COLORS = {"red", "yellow", "blue"}


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
        confidence=str(data.get("confidence", "")),
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


def _string_tuple(value: Any) -> tuple[str, ...]:
    return tuple(str(item) for item in value)
