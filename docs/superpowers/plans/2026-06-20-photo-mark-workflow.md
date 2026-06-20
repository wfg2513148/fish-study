# Photo Mark Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let parents upload marked wrong-question photos in Codex and ask one sentence, while Codex handles visual mark interpretation, structured JSON generation, CLI execution, and file delivery.

**Architecture:** Keep multimodal recognition in Codex skills and deterministic validation in Python. Add `visual_mark` metadata to the structured protocol, isolate ambiguous colors as pending items, and keep formal mock-paper PDF generation in the existing exam-paper skill.

**Tech Stack:** Python dataclasses and unittest, argparse CLI, HTML rendering, Codex local skills, Markdown docs.

---

## Task 1: Protocol Model

**Files:**
- Modify: `fish_study_wiki/study_protocol_models.py`
- Modify: `samples/wrong-question-training.json`
- Modify: `tests/test_study_protocol_models.py`

- [x] Add `VisualMark` with `color_detected`, `color_normalized`, `mark_type`, `evidence`, and `confidence`.
- [x] Allow `sticker_color: "unknown"` only with `待确认` reasons.
- [x] Validate visual normalized color matches diagnosis color.
- [x] Add tests for valid visual marks, mismatched colors, and unknown color confirmation rules.

Verify:

```bash
python3 -m unittest tests.test_study_protocol_models -v
```

## Task 2: Deterministic Checks And Persistence

**Files:**
- Modify: `fish_study_wiki/study_protocol_checks.py`
- Modify: `fish_study_wiki/study_protocol_writer.py`
- Modify: `tests/test_study_protocol_checks.py`
- Modify: `tests/test_study_protocol_writer.py`

- [x] Keep unknown colors out of long-term statistics.
- [x] Require unknown or low-confidence items to appear in `uncertain_items`.
- [x] Keep at least one known red/yellow/blue item for automatic daily training.
- [x] Bind default vault output to `settings.VAULT_ROOT`.

Verify:

```bash
python3 -m unittest tests.test_study_protocol_checks tests.test_study_protocol_writer -v
```

## Task 3: Codex Skill And Docs

**Files:**
- Create: `.codex/skills/fish-study-photo-workflow/SKILL.md`
- Modify: `scripts/setup_ai_machine.sh`
- Modify: `README.md`
- Modify: `docs/codex-study-task-usage.md`
- Modify: `docs/ai-installation-setup.md`

- [x] Add a dedicated photo workflow skill.
- [x] Keep formal mock-paper PDF rules in `fish-study-exam-paper`.
- [x] Install all project skills from setup script.
- [x] Make parent-facing docs say “upload photos and ask one sentence”.

Verify:

```bash
python3 /Users/kwang/.codex/skills/.system/skill-creator/scripts/quick_validate.py .codex/skills/fish-study-photo-workflow
bash -n scripts/setup_ai_machine.sh
```

## Task 4: Full Acceptance

Run:

```bash
python3 -m pytest -q
python3 -m fish_study_wiki.cli study-context
python3 -m fish_study_wiki.cli study-wrong samples/wrong-question-training.json --output-root /tmp/fish-study-photo-output --vault-root /tmp/fish-study-photo-vault
python3 -m fish_study_wiki.cli verify
```

Visual acceptance for daily HTML:

- Student sheet is readable on A4.
- Student sheet has no answers.
- Answer sheet has answers, scoring points, and mastery signals.
- No content overlaps or clips in browser screenshot.

Formal mock-paper PDF acceptance remains governed by `docs/exam-paper-output.md` and requires Playwright/PDF visual checks when that workflow is requested.

