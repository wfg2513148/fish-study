# Multi Photo Subject Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Support one Codex upload batch containing photos from multiple subjects, with subject-specific root-cause analysis, knowledge explanations, and printable training sheets.

**Architecture:** Codex handles photo vision and subject recognition. Python extends the structured protocol with minimal photo metadata, validates subject/photo references, and writes aggregate plus per-subject PDF outputs using existing HTML renderers as internal print templates.

**Tech Stack:** Python dataclasses, JSON validation, unittest/pytest, existing HTML/Markdown renderers, Codex skills.

---

## Task 1: Model Multi-Photo Source Metadata

**Files:**
- Modify: `fish_study_wiki/study_protocol_models.py`
- Modify: `samples/wrong-question-training.json`
- Modify: `tests/test_study_protocol_models.py`

- [x] Add `SourcePhoto`.
- [x] Add `source_photos` to `WrongQuestionTraining`.
- [x] Add `source_photo_ids` to `AnalysisCluster`.
- [x] Validate duplicate photo ids, unknown references, pending photo references, and subject mismatches.

Verify:

```bash
python3 -m unittest tests.test_study_protocol_models -v
```

## Task 2: Check Pending Photo Isolation

**Files:**
- Modify: `fish_study_wiki/study_protocol_checks.py`
- Modify: `tests/test_study_protocol_checks.py`

- [x] Add a check that pending or unknown subject photos appear in `uncertain_items`.
- [x] Keep pending photos out of any subject-specific output.

Verify:

```bash
python3 -m unittest tests.test_study_protocol_checks -v
```

## Task 3: Render Per-Subject Knowledge And Training Outputs

**Files:**
- Modify: `fish_study_wiki/study_protocol_render.py`
- Modify: `fish_study_wiki/study_protocol_writer.py`
- Modify: `fish_study_wiki/study_protocol_cli.py`
- Modify: `tests/test_study_protocol_render.py`
- Modify: `tests/test_study_protocol_writer.py`
- Modify: `tests/test_study_protocol_cli.py`

- [x] Reuse existing training sheet and answer renderers with subject-filtered training objects.
- [x] Add `render_subject_knowledge_markdown`.
- [x] Write per-subject `*-training.pdf`, `*-training-answers.pdf`, and `*-knowledge.md`.
- [x] Print subject output paths from CLI.

Verify:

```bash
python3 -m unittest tests.test_study_protocol_render tests.test_study_protocol_writer tests.test_study_protocol_cli -v
```

## Task 4: Update Skills And User Docs

**Files:**
- Modify: `.codex/skills/fish-study-photo-workflow/SKILL.md`
- Modify: `README.md`
- Modify: `docs/codex-study-task-usage.md`
- Modify: `docs/parent-user-manual.md`

- [x] Document multi-photo multi-subject behavior.
- [x] Use “分学科训练卷”, not “模拟试卷”, for daily PDF outputs.
- [x] Preserve formal mock-paper PDF boundary in `fish-study-exam-paper`.

Verify:

```bash
/tmp/fish-study-skill-validate-venv/bin/python /Users/kwang/.codex/skills/.system/skill-creator/scripts/quick_validate.py .codex/skills/fish-study-photo-workflow
```

## Task 5: Full Acceptance

Run:

```bash
python3 -m pytest -q
python3 -m fish_study_wiki.cli study-wrong samples/wrong-question-training.json --output-root /tmp/fish-study-multi-subject-output --vault-root /tmp/fish-study-multi-subject-vault
python3 -m fish_study_wiki.cli verify
git diff --check
```

Visual acceptance:

- Render aggregate and subject-specific PDF with Playwright.
- Confirm student sheets are readable, not clipped, and contain no answers.
- Confirm answer sheets contain answers and scoring points.
- Confirm knowledge Markdown contains subject, knowledge points, root causes, photo evidence, and training advice.
