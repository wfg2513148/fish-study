# Wrong Question Analysis Training Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the old homework/review-plan workflow with a wrong-question-only analysis and training workflow that generates student worksheets, separate answer pages, structured Obsidian records, and weekly review outputs with adaptive difficulty.

**Architecture:** Keep photo/OCR interpretation in Codex Desktop, and make this repository process structured JSON deterministically. The implementation keeps the existing `study_protocol_*` module family but changes the public protocol to wrong-question training and weekly review only; homework planning is removed from CLI and usage docs. Analysis events become the durable data layer for daily output, weekly aggregation, and adaptive difficulty.

**Tech Stack:** Python 3 standard library, dataclasses, argparse, JSON, Markdown, HTML, unittest, existing Obsidian vault paths.

---

## Scope

Implement the approved design:

- `docs/superpowers/specs/2026-06-19-wrong-question-analysis-training-design.md`

This implementation does not add OCR, handwriting recognition, a web UI, or network answer lookup. Codex Desktop still converts photos into structured JSON. The repository validates the JSON, renders files, writes Obsidian records, and provides repeatable CLI tests.

## File Structure

- Modify `fish_study_wiki/study_protocol_models.py`: replace public homework/review-plan loaders with `load_wrong_question_training` and `load_weekly_review_source`; add diagnosis, cluster, training question, result, and adaptive difficulty fields.
- Modify `fish_study_wiki/study_protocol_checks.py`: replace homework/review-plan checks with wrong-question training and weekly review checks; enforce student answer isolation, confirmed-vs-pending analysis rules, valid knowledge notes, adaptive difficulty coverage, printable paths, and sticker rules.
- Modify `fish_study_wiki/study_protocol_render.py`: render student worksheet HTML, separate answer page HTML, and weekly review Markdown/worksheet/answer page; remove parent-reference rendering from public use.
- Modify `fish_study_wiki/study_protocol_writer.py`: write daily training outputs and weekly review outputs; append analysis events and review queue records in Obsidian.
- Modify `fish_study_wiki/study_protocol_cli.py`: remove `homework` and `review-plan`; expose `wrong` and `weekly-review`.
- Modify `fish_study_wiki/cli.py`: remove `study-homework` and `study-review-plan`; expose `study-wrong` and `study-weekly-review`.
- Modify `docs/codex-study-task-usage.md`: document wrong-question-only daily workflow and weekly review workflow.
- Create/update samples:
  - `samples/wrong-question-training.json`
  - `samples/weekly-review-source.json`
  - Remove or stop documenting `samples/homework-plan.json` and `samples/review-plan-source.json`.
- Update tests:
  - `tests/test_study_protocol_models.py`
  - `tests/test_study_protocol_checks.py`
  - `tests/test_study_protocol_render.py`
  - `tests/test_study_protocol_writer.py`
  - `tests/test_study_protocol_cli.py`
  - `tests/test_cli.py`

---

### Task 1: Data Models, Loaders, and Samples

**Files:**
- Modify: `fish_study_wiki/study_protocol_models.py`
- Create: `samples/wrong-question-training.json`
- Create: `samples/weekly-review-source.json`
- Delete or stop using: `samples/homework-plan.json`
- Delete or stop using: `samples/review-plan-source.json`
- Test: `tests/test_study_protocol_models.py`

- [ ] Define these dataclasses in `fish_study_wiki/study_protocol_models.py`:

```python
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
```

- [ ] Implement `load_wrong_question_training(path)` requiring `task_type == "wrong_question_training"` and strict ISO date validation.
- [ ] Implement `load_weekly_review_source(path)` requiring `task_type == "weekly_review"` and strict ISO `week_start` / `week_end` validation.
- [ ] Normalize sticker colors to `red/yellow/blue`.
- [ ] Validate confidence values as `high/medium/low`.
- [ ] Validate confirmation status as `auto/needs_confirmation/confirmed/excluded`.
- [ ] Validate difficulty as `basic/standard/variant/challenge`.
- [ ] Add `samples/wrong-question-training.json` with at least three clusters: one red/basic-heavy, one yellow/standard, one blue/timed standard.
- [ ] Add `samples/weekly-review-source.json` with events, results, and review_queue covering repeated red knowledge, yellow checks, blue timing, and a D+7 review item.
- [ ] Update model tests to prove:
  - Daily sample loads.
  - Weekly sample loads.
  - Invalid `task_type` fails.
  - Invalid date such as `../escaped` fails.
  - Invalid difficulty fails.
  - Invalid confirmation status fails.

Run:

```bash
python3 -m unittest tests.test_study_protocol_models -v
```

Expected: all model tests pass.

Commit:

```bash
git add fish_study_wiki/study_protocol_models.py samples tests/test_study_protocol_models.py
git commit -m "Add wrong-question analysis data models"
```

### Task 2: Quality Checks

**Files:**
- Modify: `fish_study_wiki/study_protocol_checks.py`
- Test: `tests/test_study_protocol_checks.py`

- [ ] Replace public checks with:

```python
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
        _difficulty_mix_valid(source.events),
        _printable_path_present(report_path),
        _printable_path_present(printable_path),
        _printable_path_present(answer_path),
    )
```

- [ ] Preserve `ANSWER_MARKERS = ("答案", "参考答案", "解析", "解答")` and ensure student outputs fail if any marker appears.
- [ ] Ensure answer outputs must contain answer markers so the separate answer page is not accidentally empty or student-like.
- [ ] Ensure every confirmed/auto cluster has at least one non-pending knowledge note.
- [ ] Ensure `needs_confirmation` and `low` confidence clusters are excluded from long-term statistics checks but included in `uncertain_items`.
- [ ] Ensure each cluster has at least one training question.
- [ ] Ensure each cluster difficulty mix contains only known difficulty levels and is not empty.
- [ ] Ensure challenge questions appear only when the cluster has prior stable result evidence or the sample explicitly sets difficulty mix with basic/standard first.
- [ ] Ensure printable and answer paths are present.
- [ ] Add tests for:
  - Passing daily training check.
  - Student answer leakage fails.
  - Missing answer page answers fails.
  - Needs-confirmation cluster not listed in `uncertain_items` fails.
  - Empty knowledge note fails.
  - Empty training questions fail.
  - Invalid challenge-only difficulty fails.
  - Passing weekly review check.

Run:

```bash
python3 -m unittest tests.test_study_protocol_checks -v
```

Expected: all check tests pass.

Commit:

```bash
git add fish_study_wiki/study_protocol_checks.py tests/test_study_protocol_checks.py
git commit -m "Add wrong-question analysis quality checks"
```

### Task 3: Renderers

**Files:**
- Modify: `fish_study_wiki/study_protocol_render.py`
- Test: `tests/test_study_protocol_render.py`

- [ ] Add `render_training_student_html(training)`:
  - Title: `{date} 错题分析训练卷`.
  - Group by “错误类型 × 知识点 × 题型”.
  - Include short knowledge repair text.
  - Include training question prompts, difficulty labels, and self-check area.
  - Do not include answers, standard solutions, or explanations.
  - Do not repeat original wrong questions one-by-one.

- [ ] Add `render_training_answer_html(training)`:
  - Separate answer page.
  - Include answers, scoring points, mastery signals, and next difficulty suggestion.

- [ ] Add `render_weekly_review_markdown(source)`:
  - Weekly error distribution.
  - Repeated knowledge points.
  - High-frequency secondary reasons.
  - Difficulty fit analysis.
  - Forgetting-risk and review queue summary.
  - Next-week priorities.

- [ ] Add `render_weekly_worksheet_html(source)` and `render_weekly_answer_html(source)`.
- [ ] Keep private shared helpers for A4 CSS and Markdown links.
- [ ] Update render tests to prove:
  - Student daily HTML contains no answer markers.
  - Answer HTML contains answer markers.
  - Student daily HTML includes difficulty labels.
  - Student daily HTML does not include `question_id`-style original wrong-question listing.
  - Weekly Markdown includes difficulty fit and repeated knowledge sections.
  - Weekly worksheet contains no answers; weekly answer page contains answers.

Run:

```bash
python3 -m unittest tests.test_study_protocol_render -v
```

Expected: all render tests pass.

Commit:

```bash
git add fish_study_wiki/study_protocol_render.py tests/test_study_protocol_render.py
git commit -m "Render analysis training outputs"
```

### Task 4: Writers and Obsidian Data

**Files:**
- Modify: `fish_study_wiki/study_protocol_writer.py`
- Test: `tests/test_study_protocol_writer.py`

- [ ] Add result dataclasses:

```python
@dataclass(frozen=True)
class TrainingWriteResult:
    student_html: Path
    answer_html: Path
    obsidian_note: Path
    event_notes: tuple[Path, ...]


@dataclass(frozen=True)
class WeeklyReviewWriteResult:
    report_markdown: Path
    student_html: Path
    answer_html: Path
    obsidian_note: Path
```

- [ ] Implement `write_training_outputs(training, output_root, vault_root)`:
  - `outputs/YYYY-MM-DD/wrong-question-training.html`
  - `outputs/YYYY-MM-DD/wrong-question-training-answers.html`
  - Obsidian note: `20-错题归因/YYYY-MM-DD.md`
  - Append analysis event blocks to knowledge notes without duplicate same-date/source-batch blocks.

- [ ] Implement `write_weekly_review_outputs(source, output_root, vault_root)`:
  - `outputs/YYYY-MM-DD/weekly-review.html`, using `week_end` as output date.
  - `outputs/YYYY-MM-DD/weekly-review-answers.html`
  - `outputs/YYYY-MM-DD/weekly-review.md`
  - Obsidian note: `40-复习计划/YYYY-MM-DD.md`

- [ ] Remove or stop using homework writer entrypoints from CLI-facing paths.
- [ ] Ensure all write paths use validated dates from loaders.
- [ ] Add tests with temporary output and vault roots:
  - Daily training writes student and answer files.
  - Daily training writes Obsidian analysis note.
  - Daily training appends one event block per knowledge note/source batch and dedupes repeats.
  - Weekly review writes Markdown, student worksheet, answer page, and Obsidian note.
  - Student files do not contain answer markers.

Run:

```bash
python3 -m unittest tests.test_study_protocol_writer -v
```

Expected: all writer tests pass.

Commit:

```bash
git add fish_study_wiki/study_protocol_writer.py tests/test_study_protocol_writer.py
git commit -m "Write analysis training records"
```

### Task 5: CLI, Usage Docs, and Removal of Plan Entrypoints

**Files:**
- Modify: `fish_study_wiki/study_protocol_cli.py`
- Modify: `fish_study_wiki/cli.py`
- Modify: `docs/codex-study-task-usage.md`
- Test: `tests/test_study_protocol_cli.py`
- Test: `tests/test_cli.py`

- [ ] Change standalone CLI to expose only:

```bash
python3 -m fish_study_wiki.study_protocol_cli wrong samples/wrong-question-training.json
python3 -m fish_study_wiki.study_protocol_cli weekly-review samples/weekly-review-source.json
```

- [ ] Remove standalone subcommands:

```bash
homework
review-plan
```

- [ ] Change main CLI aliases to expose only:

```bash
python3 -m fish_study_wiki.cli study-wrong samples/wrong-question-training.json
python3 -m fish_study_wiki.cli study-weekly-review samples/weekly-review-source.json
```

- [ ] Remove main CLI aliases:

```bash
study-homework
study-review-plan
```

- [ ] Commands must print generated paths and exit nonzero if quality checks fail.
- [ ] Update usage docs to remove “今日学习计划”, “作业清单预习”, and “家长参考版” as current available workflows.
- [ ] Document:
  - Daily wrong-question photo workflow.
  - Weekly review workflow.
  - Student worksheet and answer page separation.
  - Silent daily analysis and weekly visible analysis.
  - Adaptive difficulty rules.

- [ ] Add CLI tests:
  - `wrong` succeeds and writes student/answer/Obsidian files.
  - `weekly-review` succeeds and writes report/student/answer/Obsidian files.
  - Main CLI aliases dispatch.
  - Removed commands return argparse error.
  - Quality failure returns nonzero and creates no output directory.

Run:

```bash
python3 -m unittest tests.test_study_protocol_cli tests.test_cli -v
```

Expected: CLI tests pass.

Commit:

```bash
git add fish_study_wiki/study_protocol_cli.py fish_study_wiki/cli.py docs/codex-study-task-usage.md tests/test_study_protocol_cli.py tests/test_cli.py
git commit -m "Replace study planning CLI with analysis training"
```

### Task 6: End-to-End Verification and Release-Ready Cleanup

**Files:**
- Verify generated local files under `outputs/YYYY-MM-DD/`
- Verify Obsidian vault writes under `/Users/kwang/Downloads/obsidian/fish-study`

- [ ] Run focused tests:

```bash
python3 -m unittest tests.test_study_protocol_models tests.test_study_protocol_checks tests.test_study_protocol_render tests.test_study_protocol_writer tests.test_study_protocol_cli -v
```

Expected: all focused tests pass.

- [ ] Run full test suite:

```bash
python3 -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] Run wiki gate:

```bash
python3 -m fish_study_wiki.cli verify
```

Expected: `Quality gate passed`.

- [ ] Run sample daily command:

```bash
python3 -m fish_study_wiki.study_protocol_cli wrong samples/wrong-question-training.json
```

Expected paths include:

```text
outputs/2026-06-19/wrong-question-training.html
outputs/2026-06-19/wrong-question-training-answers.html
/Users/kwang/Downloads/obsidian/fish-study/20-错题归因/2026-06-19.md
```

- [ ] Run sample weekly command:

```bash
python3 -m fish_study_wiki.study_protocol_cli weekly-review samples/weekly-review-source.json
```

Expected paths include:

```text
outputs/2026-06-21/weekly-review.md
outputs/2026-06-21/weekly-review.html
outputs/2026-06-21/weekly-review-answers.html
/Users/kwang/Downloads/obsidian/fish-study/40-复习计划/2026-06-21.md
```

- [ ] Confirm student outputs contain no answer markers:

```bash
rg -n "答案|参考答案|解析|解答" outputs/2026-06-19/wrong-question-training.html outputs/2026-06-21/weekly-review.html
```

Expected: no matches.

- [ ] Confirm removed entrypoints are not present in CLI help:

```bash
python3 -m fish_study_wiki.study_protocol_cli --help
python3 -m fish_study_wiki.cli --help
```

Expected: no `homework`, no `review-plan`, no `study-homework`, no `study-review-plan`.

- [ ] Confirm raw source files are untracked:

```bash
git ls-files | rg "\\.(zip|jpg|jpeg|png|pdf|pptx|docx)$|sources/raw" || true
```

Expected: no output.

- [ ] Run formatting gate:

```bash
git diff --check
```

Expected: no output.

- [ ] Commit any final doc or test adjustments:

```bash
git status --short
```

Expected: clean after final commit.

## Acceptance Checklist

- `homework_plan`, `study-homework`, and `today-study-plan` are no longer available public workflows.
- Daily `wrong` workflow generates a student worksheet and separate answer page.
- Weekly `weekly-review` workflow generates an Obsidian report, worksheet, and separate answer page.
- Student worksheets never include answer markers.
- Daily output is grouped by “错误类型 × 知识点 × 题型”, not by original wrong-question explanations.
- Analysis events store diagnosis, confidence, confirmation status, knowledge, problem type, difficulty mix, training questions, results, and review queue data.
- High-confidence diagnosis can enter long-term statistics; medium/low confidence remains pending unless confirmed.
- Adaptive difficulty is represented in data, rendering, answers, weekly report, and tests.
- D+1/D+3/D+7/D+14 review queue behavior is represented in weekly review data and output.
- Full tests, wiki gate, sample commands, entrypoint removal checks, and raw-file checks all pass.
