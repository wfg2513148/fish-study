---
name: fish-study-photo-workflow
description: Use when a parent or student uploads wrong-question photos in Codex and asks for knowledge points, root-cause analysis, practice questions, or a daily wrong-question training sheet. Handles visual color marks, stickers, marker circles/underlines, Fish Study JSON, CLI execution, and local file delivery.
---

# Fish Study Photo Workflow

Turn marked wrong-question photos into Fish Study training outputs while keeping the user path simple: the parent or student uploads photos and says one sentence such as “帮我生成错题知识点和测试题”.

## Boundary

- Codex performs visual recognition from uploaded photos.
- The Python CLI only validates structured JSON, renders materials, and writes Obsidian records.
- Do not ask the parent to write or edit JSON.
- Do not use this skill for formal mock exam PDFs; use `fish-study-exam-paper` for real paper format, gpt-image-2 diagrams, PDF export, and PDF visual checks.

## Workflow

1. Confirm the current Fish Study repo root with `pwd`.
2. Run:

```bash
python3 -m fish_study_wiki.cli study-context
```

3. Read each uploaded photo visually:
   - transcribe the wrong question enough to identify subject, problem type, and knowledge point;
   - inspect visible marks near each question;
   - record the mark color, mark type, and visual evidence.
4. Normalize colors:
   - red -> `red` -> `不会`;
   - yellow -> `yellow` -> `马虎`;
   - blue -> `blue` -> `时间不够`;
   - green, orange, purple, mixed colors, glare, unclear colors, or no clear mark -> `unknown` and `待确认`.
5. Generate `wrong_question_training` JSON under `outputs/photo-workflow/YYYY-MM-DD-wrong-question-training.json`.
6. Run:

```bash
python3 -m fish_study_wiki.cli study-wrong outputs/photo-workflow/YYYY-MM-DD-wrong-question-training.json
```

7. Return the generated student sheet, answer sheet, and Obsidian note paths as Markdown absolute local file links.

## Visual Mark JSON

Each diagnosis should include `visual_mark`:

```json
{
  "sticker_color": "red",
  "primary_reason": "不会",
  "secondary_reason": "概念不清",
  "evidence": "题目中把原子核和电子层位置写反。",
  "confidence": "high",
  "confirmation_status": "confirmed",
  "visual_mark": {
    "color_detected": "红色圆形贴纸",
    "color_normalized": "red",
    "mark_type": "sticker",
    "evidence": "题号旁有红色圆形贴纸，颜色边界清晰。",
    "confidence": "high"
  }
}
```

Allowed values:

- `color_normalized`: `red`, `yellow`, `blue`, `unknown`
- `mark_type`: `sticker`, `marker`, `circle`, `underline`, `unknown`
- `confidence`: `high`, `medium`, `low`

Rules:

- `visual_mark.color_normalized` must match `diagnosis.sticker_color`.
- `unknown` must use `primary_reason: "待确认"` and `secondary_reason: "待确认"`.
- `unknown` must use `confirmation_status: "needs_confirmation"` and must appear in `uncertain_items`.
- `medium` or `low` confidence items must appear in `uncertain_items`.
- Only high-confidence `red/yellow/blue` items with `auto` or `confirmed` status may enter long-term statistics.

## Parent-Facing Output

Keep the final response short:

- Say which subjects and knowledge points were found.
- Say which items need confirmation because the photo or color mark was unclear.
- Link the student sheet and answer sheet.
- Do not expose the JSON unless the user asks.

Use absolute Markdown links:

```md
[wrong-question-training.html](/absolute/path/to/fish-study/outputs/2026-06-20/wrong-question-training.html)
```

## Verification

Before finishing:

```bash
python3 -m fish_study_wiki.cli study-context
python3 -m fish_study_wiki.cli study-wrong <generated-json>
python3 -m pytest -q
```

For generated daily HTML sheets, visually inspect the rendered page when practical:

- A4 layout is readable.
- Student sheet contains no answers or explanations.
- Answer sheet contains answers, scoring points, and mastery signals.
- No text overlaps or clipped question content.

If the user asks for formal mock papers or PDF output, switch to `fish-study-exam-paper` and run the stricter PDF visual-recognition checks required there.
