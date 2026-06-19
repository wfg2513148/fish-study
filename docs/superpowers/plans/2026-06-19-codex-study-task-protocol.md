# Codex Study Task Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved Codex 学习任务执行协议 so structured photo interpretations can be turned into printable student materials, parent references, Obsidian records, and quality self-checks.

**Architecture:** Keep image recognition in the Codex Desktop conversation and make the repository responsible for deterministic processing after recognition. The implementation accepts structured JSON for homework plans, wrong-question reviews, and sticker-based review planning, validates it, renders student/parent outputs, writes Obsidian records, and exposes CLI commands for repeatable tests.

**Tech Stack:** Python 3 standard library, Markdown, HTML, JSON, unittest, existing fish-study Obsidian vault paths.

---

## Scope

This plan implements the execution layer for the already approved design:

- `docs/superpowers/specs/2026-06-19-codex-study-task-protocol-design.md`

It does not implement image OCR, handwriting recognition, or automatic answer solving from photographs. Codex Desktop will still read photos in chat and convert them into the structured JSON format defined by the protocol.

## File Structure

- Create `fish_study_wiki/study_protocol_models.py`: dataclasses and JSON loaders for homework, wrong-question review, and review-plan inputs.
- Create `fish_study_wiki/study_protocol_checks.py`: quality checks for student-answer leakage, knowledge links, low-confidence flags, printable paths, and sticker rules.
- Create `fish_study_wiki/study_protocol_render.py`: deterministic HTML and Markdown renderers.
- Create `fish_study_wiki/study_protocol_writer.py`: output writer for `outputs/YYYY-MM-DD/*.html`, parent references, and Obsidian notes.
- Create `fish_study_wiki/study_protocol_cli.py`: CLI commands `homework`, `wrong`, and `review-plan`.
- Modify `fish_study_wiki/cli.py`: add subcommands `study-homework`, `study-wrong`, and `study-review-plan` that delegate to the protocol CLI.
- Create `samples/homework-plan.json`, `samples/wrong-question-review.json`, `samples/review-plan-source.json`: runnable structured examples.
- Create tests: `tests/test_study_protocol_models.py`, `tests/test_study_protocol_checks.py`, `tests/test_study_protocol_render.py`, `tests/test_study_protocol_writer.py`, `tests/test_study_protocol_cli.py`.
- Create `docs/codex-study-task-usage.md`: operational guide for real Codex Desktop use.

---

### Task 1: Data Models and JSON Loading

**Files:**
- Create: `fish_study_wiki/study_protocol_models.py`
- Create: `samples/homework-plan.json`
- Create: `samples/wrong-question-review.json`
- Create: `samples/review-plan-source.json`
- Test: `tests/test_study_protocol_models.py`

- [ ] Define dataclasses for `KnowledgeMatch`, `HomeworkItem`, `HomeworkPlan`, `WrongQuestionItem`, `WrongQuestionReview`, and `ReviewPlanSource`.
- [ ] Add loaders that reject unknown `task_type` values and normalize sticker colors to `red`, `yellow`, `blue`.
- [ ] Add tests proving sample JSON loads and invalid task types fail.
- [ ] Commit: `Add study protocol data models`.

### Task 2: Quality Self-Checks

**Files:**
- Create: `fish_study_wiki/study_protocol_checks.py`
- Test: `tests/test_study_protocol_checks.py`

- [ ] Implement checks from the design: no answers in student output, at least one knowledge link or `待定位`, low-confidence items flagged, printable path present, wrong-question sticker rules used.
- [ ] Return structured check rows with `passed`, `code`, and `message`.
- [ ] Add tests for passing homework, missing knowledge, low-confidence flagging, answer leakage, and unknown sticker color.
- [ ] Commit: `Add study protocol quality checks`.

### Task 3: Student and Parent Renderers

**Files:**
- Create: `fish_study_wiki/study_protocol_render.py`
- Test: `tests/test_study_protocol_render.py`

- [ ] Render homework student HTML with A4 CSS, knowledge preview, warm-up area, task list, and self-check area.
- [ ] Render wrong-question student HTML with knowledge review, color-specific strategy, variation questions, and no answers.
- [ ] Render parent Markdown references with estimated time, check order, answers/reference notes when provided, and low-confidence warnings.
- [ ] Render review-plan Markdown for 3-7 day review planning from red/yellow/blue counts.
- [ ] Add tests proving student HTML does not contain answer sections and parent Markdown does.
- [ ] Commit: `Render study protocol outputs`.

### Task 4: Output and Obsidian Writers

**Files:**
- Create: `fish_study_wiki/study_protocol_writer.py`
- Test: `tests/test_study_protocol_writer.py`

- [ ] Write homework output to `outputs/YYYY-MM-DD/today-study-plan.html`.
- [ ] Write wrong-question output to `outputs/YYYY-MM-DD/wrong-question-review.html`.
- [ ] Write parent references next to the HTML as Markdown.
- [ ] Write Obsidian daily plan records to `30-每日学习计划/YYYY-MM-DD.md`.
- [ ] Write Obsidian wrong-question records to `20-错题归因/YYYY-MM-DD.md`.
- [ ] Append wrong-question records to matched knowledge notes without duplicating the same dated block.
- [ ] Add tests using temporary output and vault directories.
- [ ] Commit: `Write study outputs and Obsidian records`.

### Task 5: CLI Integration

**Files:**
- Create: `fish_study_wiki/study_protocol_cli.py`
- Modify: `fish_study_wiki/cli.py`
- Test: `tests/test_study_protocol_cli.py`

- [ ] Add CLI commands:
  - `python3 -m fish_study_wiki.study_protocol_cli homework samples/homework-plan.json`
  - `python3 -m fish_study_wiki.study_protocol_cli wrong samples/wrong-question-review.json`
  - `python3 -m fish_study_wiki.study_protocol_cli review-plan samples/review-plan-source.json`
- [ ] Add main CLI aliases:
  - `python3 -m fish_study_wiki.cli study-homework samples/homework-plan.json`
  - `python3 -m fish_study_wiki.cli study-wrong samples/wrong-question-review.json`
  - `python3 -m fish_study_wiki.cli study-review-plan samples/review-plan-source.json`
- [ ] Commands must print generated paths and exit nonzero if quality checks fail.
- [ ] Add CLI dispatch tests.
- [ ] Commit: `Add study protocol CLI`.

### Task 6: Usage Guide and End-to-End Verification

**Files:**
- Create: `docs/codex-study-task-usage.md`
- Generated locally: `outputs/2026-06-19/*`
- Generated in vault: `/Users/kwang/Downloads/obsidian/fish-study/30-每日学习计划/2026-06-19.md`, `/Users/kwang/Downloads/obsidian/fish-study/20-错题归因/2026-06-19.md`

- [ ] Document how Codex Desktop should convert photo understanding into JSON and run the commands.
- [ ] Document that student outputs contain no answers and parent references stay separate.
- [ ] Run all tests: `python3 -m unittest discover -s tests -v`.
- [ ] Run wiki gate: `python3 -m fish_study_wiki.cli verify`.
- [ ] Run all three sample commands.
- [ ] Confirm generated student HTML files exist and parent references exist.
- [ ] Confirm Obsidian notes exist.
- [ ] Confirm raw ZIP files are still untracked.
- [ ] Commit docs and generated sample metadata if appropriate; do not commit raw photos or ZIPs.

## Acceptance

- All six tasks are implemented.
- Full test suite passes.
- CLI sample commands work end to end.
- Student HTML contains no answer sections.
- Parent Markdown is separate and may contain answers/reference notes.
- Obsidian records are written for daily plans, wrong-question reviews, and review plans.
- Low-confidence and `待定位` items are surfaced instead of hidden.
- GitHub private repo is pushed with no tracked raw ZIPs, photos, or full教材/课件 files.
