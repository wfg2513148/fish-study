from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from fish_study_wiki import settings
from fish_study_wiki.knowledge_graph import merge_training_events
from fish_study_wiki.models import safe_markdown_filename
from fish_study_wiki.study_protocol_models import (
    AnalysisCluster,
    KnowledgeMatch,
    WeeklyReviewSource,
    WrongQuestionTraining,
)
from fish_study_wiki.study_protocol_render import (
    COLOR_LABELS,
    render_subject_knowledge_markdown,
    render_training_answer_html,
    render_training_student_html,
    render_weekly_answer_html,
    render_weekly_review_markdown,
    render_weekly_worksheet_html,
)


DEFAULT_OUTPUT_ROOT = Path("outputs")
DEFAULT_VAULT_ROOT = settings.VAULT_ROOT
SUBJECT_SLUGS = {
    "数学": "math",
    "科学": "science",
    "英语": "english",
}


@dataclass(frozen=True)
class SubjectTrainingWriteResult:
    subject: str
    student_html: Path
    answer_html: Path
    knowledge_markdown: Path


@dataclass(frozen=True)
class TrainingWriteResult:
    student_html: Path
    answer_html: Path
    obsidian_note: Path
    event_notes: tuple[Path, ...]
    subject_outputs: tuple[SubjectTrainingWriteResult, ...] = ()


@dataclass(frozen=True)
class WeeklyReviewWriteResult:
    report_markdown: Path
    student_html: Path
    answer_html: Path
    obsidian_note: Path


def write_training_outputs(
    training: WrongQuestionTraining,
    output_root: Path | str = DEFAULT_OUTPUT_ROOT,
    vault_root: Path | str = DEFAULT_VAULT_ROOT,
    graph_path: Path | str | None = None,
) -> TrainingWriteResult:
    output_dir = _dated_output_dir(output_root, training.date)
    student_html = output_dir / "wrong-question-training.html"
    answer_html = output_dir / "wrong-question-training-answers.html"
    student_html.write_text(render_training_student_html(training), encoding="utf-8")
    answer_html.write_text(render_training_answer_html(training), encoding="utf-8")
    subject_outputs = _write_subject_training_outputs(training, output_dir)

    obsidian_note = _wrong_question_path(vault_root, training.date)
    obsidian_note.parent.mkdir(parents=True, exist_ok=True)
    obsidian_note.write_text(
        _render_training_note(training, student_html, answer_html),
        encoding="utf-8",
    )
    event_notes = _append_analysis_event_records(
        Path(vault_root),
        training,
        student_html,
        answer_html,
    )
    merge_training_events(_default_graph_path(output_root, graph_path), training)
    return TrainingWriteResult(
        student_html,
        answer_html,
        obsidian_note,
        tuple(sorted(event_notes)),
        subject_outputs,
    )


def write_weekly_review_outputs(
    source: WeeklyReviewSource,
    output_root: Path | str = DEFAULT_OUTPUT_ROOT,
    vault_root: Path | str = DEFAULT_VAULT_ROOT,
) -> WeeklyReviewWriteResult:
    output_dir = _dated_output_dir(output_root, source.week_end)
    report_markdown = output_dir / "weekly-review.md"
    student_html = output_dir / "weekly-review.html"
    answer_html = output_dir / "weekly-review-answers.html"
    report_markdown.write_text(render_weekly_review_markdown(source), encoding="utf-8")
    student_html.write_text(render_weekly_worksheet_html(source), encoding="utf-8")
    answer_html.write_text(render_weekly_answer_html(source), encoding="utf-8")

    obsidian_note = _review_plan_path(vault_root, source.week_end)
    obsidian_note.parent.mkdir(parents=True, exist_ok=True)
    obsidian_note.write_text(
        _render_weekly_review_note(source, report_markdown, student_html, answer_html),
        encoding="utf-8",
    )
    return WeeklyReviewWriteResult(
        report_markdown,
        student_html,
        answer_html,
        obsidian_note,
    )


def _dated_output_dir(output_root: Path | str, plan_date: str) -> Path:
    output_dir = Path(output_root) / plan_date
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _write_subject_training_outputs(
    training: WrongQuestionTraining,
    output_dir: Path,
) -> tuple[SubjectTrainingWriteResult, ...]:
    outputs = []
    for subject in _training_subjects(training.clusters):
        subject_training = _subject_training(training, subject)
        slug = _subject_slug(subject)
        student_html = output_dir / f"{slug}-training.html"
        answer_html = output_dir / f"{slug}-training-answers.html"
        knowledge_markdown = output_dir / f"{slug}-knowledge.md"
        student_html.write_text(
            render_training_student_html(subject_training),
            encoding="utf-8",
        )
        answer_html.write_text(
            render_training_answer_html(subject_training),
            encoding="utf-8",
        )
        knowledge_markdown.write_text(
            render_subject_knowledge_markdown(training, subject),
            encoding="utf-8",
        )
        outputs.append(
            SubjectTrainingWriteResult(
                subject=subject,
                student_html=student_html,
                answer_html=answer_html,
                knowledge_markdown=knowledge_markdown,
            )
        )
    return tuple(outputs)


def _training_subjects(clusters: tuple[AnalysisCluster, ...]) -> tuple[str, ...]:
    subjects = []
    for cluster in clusters:
        if cluster.subject not in subjects:
            subjects.append(cluster.subject)
    return tuple(subjects)


def _subject_training(
    training: WrongQuestionTraining,
    subject: str,
) -> WrongQuestionTraining:
    clusters = tuple(cluster for cluster in training.clusters if cluster.subject == subject)
    photo_ids = {
        photo_id
        for cluster in clusters
        for photo_id in cluster.source_photo_ids
    }
    return replace(
        training,
        clusters=clusters,
        uncertain_items=_subject_uncertain_items(training.uncertain_items, subject, photo_ids),
        source_photos=tuple(
            photo
            for photo in training.source_photos
            if photo.subject == subject or photo.photo_id in photo_ids
        ),
    )


def _subject_uncertain_items(
    uncertain_items: tuple[str, ...],
    subject: str,
    photo_ids: set[str],
) -> tuple[str, ...]:
    return tuple(
        item
        for item in uncertain_items
        if subject in item or any(photo_id in item for photo_id in photo_ids)
    )


def _subject_slug(subject: str) -> str:
    if subject in SUBJECT_SLUGS:
        return SUBJECT_SLUGS[subject]
    return safe_markdown_filename(subject).removesuffix(".md").lower()


def _default_graph_path(
    output_root: Path | str,
    graph_path: Path | str | None,
) -> Path:
    if graph_path is not None:
        return Path(graph_path)
    return Path(output_root).parent / "data" / "wiki" / "knowledge-graph.json"


def _wrong_question_path(vault_root: Path | str, plan_date: str) -> Path:
    return Path(vault_root) / "20-错题归因" / f"{plan_date}.md"


def _review_plan_path(vault_root: Path | str, plan_date: str) -> Path:
    return Path(vault_root) / "40-复习计划" / f"{plan_date}.md"


def _render_training_note(
    training: WrongQuestionTraining,
    student_html: Path,
    answer_html: Path,
) -> str:
    return f"""# {training.date} 错题归因

## 打印材料

- 学生训练卷：{student_html}
- 批改答案页：{answer_html}

## 静默分析摘要

{_analysis_cluster_lines(training.clusters)}

## 待确认项

{_uncertain_items(training.uncertain_items)}
"""


def _render_weekly_review_note(
    source: WeeklyReviewSource,
    report_markdown: Path,
    student_html: Path,
    answer_html: Path,
) -> str:
    return f"""# {source.week_end} 错题周复盘

## 输出文件

- 周复盘报告：{report_markdown}
- 周巩固测试卷：{student_html}
- 周巩固答案页：{answer_html}

## 周复盘报告

{render_weekly_review_markdown(source).strip()}

## 待确认项

{_uncertain_items(source.uncertain_items)}
"""


def _analysis_cluster_lines(clusters: tuple[AnalysisCluster, ...]) -> str:
    lines = []
    for cluster in clusters:
        diagnosis = cluster.diagnosis
        lines.append(
            f"- {cluster.subject} {cluster.problem_type}："
            f"{COLOR_LABELS.get(diagnosis.sticker_color, diagnosis.sticker_color)}，"
            f"{diagnosis.primary_reason}/{diagnosis.secondary_reason}，"
            f"置信度：{diagnosis.confidence}，确认：{diagnosis.confirmation_status}"
        )
        for match in cluster.matched_knowledge:
            lines.append(f"  - 知识点：{_md_link(match.note)}（{match.confidence}）")
        lines.append(f"  - 难度梯度：{'/'.join(cluster.difficulty_mix)}")
    return "\n".join(lines) if lines else "- 暂无。"


def _append_analysis_event_records(
    vault_root: Path,
    training: WrongQuestionTraining,
    student_html: Path,
    answer_html: Path,
) -> set[Path]:
    by_note: dict[Path, list[AnalysisCluster]] = {}
    for cluster in training.clusters:
        if not _cluster_enters_long_term_stats(cluster):
            continue
        for match in cluster.matched_knowledge:
            if match.is_pending:
                continue
            note_path = _knowledge_note_path(vault_root, match, cluster.subject)
            by_note.setdefault(note_path, []).append(cluster)

    changed: set[Path] = set()
    for note_path, clusters in by_note.items():
        note_path.parent.mkdir(parents=True, exist_ok=True)
        if not note_path.exists():
            note_path.write_text(f"# {note_path.stem}\n\n## 错题分析记录\n", encoding="utf-8")
        current = note_path.read_text(encoding="utf-8")
        block = _analysis_event_block(
            training.date,
            training.source_batch,
            clusters,
            student_html,
            answer_html,
        )
        begin = _analysis_block_begin(training.date, training.source_batch)
        if begin not in current:
            note_path.write_text(current.rstrip() + "\n\n" + block, encoding="utf-8")
        changed.add(note_path)
    return changed


def _cluster_enters_long_term_stats(cluster: AnalysisCluster) -> bool:
    diagnosis = cluster.diagnosis
    return (
        diagnosis.confidence == "high"
        and diagnosis.confirmation_status in {"auto", "confirmed"}
        and diagnosis.sticker_color in {"red", "yellow", "blue"}
    )


def _knowledge_note_path(vault_root: Path, match: KnowledgeMatch, subject: str) -> Path:
    filename = safe_markdown_filename(match.note)
    existing = tuple(vault_root.rglob(filename))
    if existing:
        return existing[0]
    return vault_root / "10-教材Wiki" / match.grade / match.volume / subject / filename


def _analysis_event_block(
    record_date: str,
    source_batch: str,
    clusters: list[AnalysisCluster],
    student_html: Path,
    answer_html: Path,
) -> str:
    lines = [
        _analysis_block_begin(record_date, source_batch),
        f"### {record_date} 错题分析事件",
        "",
        f"- 来源批次：{source_batch}",
        f"- 学生训练卷：{student_html}",
        f"- 批改答案页：{answer_html}",
    ]
    for cluster in clusters:
        diagnosis = cluster.diagnosis
        lines.append(
            f"- {cluster.subject} {cluster.problem_type}："
            f"{COLOR_LABELS.get(diagnosis.sticker_color, diagnosis.sticker_color)}，"
            f"{diagnosis.primary_reason}/{diagnosis.secondary_reason}，"
            f"难度：{'/'.join(cluster.difficulty_mix)}"
        )
        lines.append(f"  - 依据：{diagnosis.evidence}")
        for question in cluster.training_questions:
            lines.append(f"  - 训练题：{question.difficulty} - {question.prompt}")
    lines.append(_analysis_block_end(record_date, source_batch))
    return "\n".join(lines) + "\n"


def _analysis_block_begin(record_date: str, source_batch: str) -> str:
    return f"<!-- study-protocol-analysis:{record_date}:{source_batch}:start -->"


def _analysis_block_end(record_date: str, source_batch: str) -> str:
    return f"<!-- study-protocol-analysis:{record_date}:{source_batch}:end -->"


def _uncertain_items(items: tuple[str, ...]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- 暂无。"


def _md_link(note: str) -> str:
    return "[[待定位]]" if note == "待定位" else f"[[{note}]]"
