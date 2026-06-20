# Multi Photo Subject Workflow Design

## Goal

When a parent or student uploads multiple wrong-question photos in one Codex turn, Codex should identify the subject for each photo, group the batch by subject, run root-cause analysis per subject, and produce subject-specific knowledge explanations and printable training sheets.

## Optimized Scope

This workflow does not turn the Python CLI into an OCR or image classifier. Codex performs photo understanding and subject recognition; the Python project validates structured JSON, groups clusters by subject, renders output files, and writes Obsidian records.

The daily output is a subject-specific wrong-question training sheet, not a formal mock exam PDF. If the user asks for a real mock paper, PDF, gpt-image-2 diagrams, or formal exam format, Codex must switch to `fish-study-exam-paper`.

## Data Model

Add top-level `source_photos`:

```json
{
  "photo_id": "photo-001",
  "label_or_filename": "IMG_0012.jpeg",
  "subject": "数学",
  "confidence": "high",
  "evidence": "题面包含平行线、角度和几何图。",
  "status": "recognized"
}
```

Each cluster may reference photos with:

```json
"source_photo_ids": ["photo-001"]
```

Rules:

- `photo_id` values must be unique.
- `source_photo_ids` must reference existing `source_photos`.
- A cluster may only reference `source_photos.status == "recognized"`.
- A referenced photo subject must match `cluster.subject`.
- `needs_confirmation` or `unknown` photo subjects must appear in `uncertain_items` and must not enter any subject sheet.

## Output

For each run, keep existing aggregate files:

- `wrong-question-training.html`
- `wrong-question-training-answers.html`

Also output per-subject files when matching clusters exist:

- `math-training.html`
- `math-training-answers.html`
- `math-knowledge.md`
- `science-training.html`
- `science-training-answers.html`
- `science-knowledge.md`
- `english-training.html`
- `english-training-answers.html`
- `english-knowledge.md`

The knowledge Markdown is an independent parent/student handoff. It must include knowledge points, root causes, photo evidence, and training advice.

## Parent Experience

The parent still uploads photos and says one sentence:

```text
帮我生成错题知识点和测试题
```

Codex should return a subject summary,待确认项, and Markdown local file links. It should not ask the parent to edit JSON or run commands.
