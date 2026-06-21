# Knowledge Card Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a student-facing knowledge-card output that extracts knowledge points from wrong questions, sorts them by learning order, removes question/diagnosis noise, and uses knowledge-focused illustrations.

**Architecture:** Keep the existing wrong-question training and answer outputs unchanged. Add a separate knowledge-card renderer and make the writer use it for per-subject `*-knowledge.md/pdf` outputs. The old diagnosis-heavy knowledge rendering may remain available for internal use, but student-facing knowledge PDFs must use the new renderer.

**Tech Stack:** Python dataclasses and render helpers in `fish_study_wiki`, Playwright PDF export through `write_pdf_from_html`, unit tests with `unittest`/`pytest`.

---

## File Structure

- Modify `fish_study_wiki/study_protocol_render.py`: add knowledge-card extraction, sorting, clean markdown/html rendering, and support for injected gpt-image-2 diagram assets.
- Add `fish_study_wiki/knowledge_card_images.py`: generate knowledge-card image assets through the `gpt-image-2` skill before PDF export.
- Modify `fish_study_wiki/study_protocol_writer.py`: route subject knowledge outputs to the new knowledge-card renderer.
- Modify `tests/test_study_protocol_render.py`: assert cards are deduped, ordered by knowledge order, and free of diagnosis/source words.
- Modify `tests/test_study_protocol_writer.py`: assert generated `*-knowledge.md/pdf` use knowledge-card wording.
- Modify `.codex/skills/fish-study-photo-workflow/SKILL.md`: document the knowledge-card rule for future runs.

## Task 1: Add Knowledge Card Renderer

**Files:**
- Modify: `fish_study_wiki/study_protocol_render.py`
- Test: `tests/test_study_protocol_render.py`

- [ ] Add tests that call `render_subject_knowledge_cards_markdown` and `render_subject_knowledge_cards_html`.
- [ ] Tests must verify:
  - duplicate `KnowledgeMatch.note` values render once;
  - `待定位` and low-confidence knowledge do not render as cards;
  - forbidden words such as `photo-`, `照片`, `错因`, `依据`, `训练建议`, `难度梯度`, `第1题` do not appear;
  - rendered order follows `grade/volume/chapter/note`, not cluster order;
  - HTML contains local `<img>` diagrams marked as `data-generator="gpt-image-2"`;
- [ ] Implement `render_subject_knowledge_cards_markdown(training, subject)`.
- [ ] Implement `render_subject_knowledge_cards_html(training, subject)`.
- [ ] Add helpers:
  - `_subject_knowledge_card_items`.
  - `_knowledge_sort_key`.
  - `_knowledge_category_rank`.
  - `_knowledge_card_body`.
  - `_knowledge_card_image`.
- [ ] `_subject_knowledge_card_items` may read `training.clusters[*].matched_knowledge` only for extraction; card body and diagram helpers must accept `KnowledgeMatch.note` or a `KnowledgeMatch`, not `AnalysisCluster`, `Diagnosis`, source photos, prompts, or answers.
- [ ] `_knowledge_card_body` must include more than a concept sentence: core definition, formulas/relationships, application steps or tricks, targeted review focus, pitfalls, and a self-check question.
- [ ] The targeted review focus may be informed by internal error type, but must not expose diagnosis/color/source/question wording in the card.
- [ ] `_knowledge_card_image` must consume local gpt-image-2 image paths keyed by knowledge point, not by original `problem_type`, and must not include original figure paths or source-photo IDs.
- [ ] Do not use hand-made SVG/CSS placeholders for student-facing knowledge-card diagrams.
- [ ] Run `python3 -m pytest tests/test_study_protocol_render.py -q`.

## Task 2: Route Writer Outputs To Knowledge Cards

**Files:**
- Modify: `fish_study_wiki/study_protocol_writer.py`
- Test: `tests/test_study_protocol_writer.py`

- [ ] Import the new knowledge-card render functions.
- [ ] Generate knowledge-card image assets through `gpt-image-2` before rendering subject knowledge Markdown/PDF.
- [ ] Change `_write_subject_training_outputs` so `knowledge_markdown` and `knowledge_pdf` use knowledge-card renderers.
- [ ] Update writer tests so `science-knowledge.md/pdf` and `math-knowledge.md/pdf` contain `知识点复习卡`, and do not contain source or diagnosis wording.
- [ ] Update writer tests so knowledge PDFs contain embedded image objects.
- [ ] Run `python3 -m pytest tests/test_study_protocol_writer.py -q`.

## Task 3: Update Workflow Skill

**Files:**
- Modify: `.codex/skills/fish-study-photo-workflow/SKILL.md`

- [ ] Add a “Knowledge Card Rule” section.
- [ ] State that knowledge cards are ordered by learning sequence, not question/photo order.
- [ ] State that cards must not include photo/source/question/diagnosis wording.
- [ ] State that illustrations must be generated for the knowledge point and not reused from original questions.
- [ ] State that student-facing knowledge-card illustrations must use `gpt-image-2`, not SVG/CSS placeholders.
- [ ] State that internal error types can guide the `复习重点`, but the card must not expose diagnosis terms.
- [ ] Sync to `/Users/kwang/.codex/skills/fish-study-photo-workflow/SKILL.md`.

## Task 4: End-To-End Validation

**Files:**
- No source changes unless validation reveals a defect.

- [ ] Run `python3 -m pytest tests/test_study_protocol_render.py tests/test_study_protocol_writer.py -q`.
- [ ] Run `python3 -m pytest -q`.
- [ ] Run the existing sample workflow:

```bash
python3 -m fish_study_wiki.study_protocol_cli wrong samples/wrong-question-training.json --output-root /tmp/fish-study-knowledge-card-output --vault-root /tmp/fish-study-knowledge-card-vault
```

- [ ] Inspect generated knowledge markdown for forbidden words:

```bash
rg -n "photo-|照片|来源|文件名|第[0-9一二三四五六七八九十]+题|本题|本次错题|这道题|题目中|根据照片|错因|依据|诊断|训练建议|难度梯度|红色|黄色|蓝色|sticker|source_batch|question_id" /tmp/fish-study-knowledge-card-output/*/*-knowledge.md
```

Expected: no matches.

- [ ] Extract generated knowledge PDF text and run the same forbidden-word check against PDF text.
- [ ] Verify generated knowledge PDFs exist, contain `知识点复习卡`, contain formulas/relationships/steps, and include embedded diagrams.
- [ ] If creating user-facing PDFs in the active session, copy them into `outputs/codex-session-files/` and return exact filename Markdown links.

## Self-Review

- The plan covers extraction, sorting, card cleanup, illustration rules, writer routing, skill documentation, and validation.
- It avoids changing training/answer worksheet semantics.
- It does not require new persistent JSON schema fields; the renderer derives cards from existing `KnowledgeMatch` values.
