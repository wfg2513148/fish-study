# Photo Mark Workflow Design

## Goal

Lower the daily Fish Study workflow difficulty for parents and students. The user uploads marked wrong-question photos in Codex and says one sentence: “帮我生成错题知识点和测试题”.

## Second-Version Decision

The first plan was too broad because it mixed visual recognition, arbitrary color semantics, Python-side OCR, and formal mock-paper PDF generation. The optimized plan keeps the boundary narrow:

- Codex performs photo understanding and visual mark recognition.
- Python receives structured JSON only.
- Only red, yellow, and blue support automatic root-cause mapping.
- Green, mixed colors, glare, unclear marks, and missing color become `unknown` and must go to `uncertain_items`.
- Daily wrong-question sheets remain HTML outputs.
- Formal mock exam PDFs still use `fish-study-exam-paper`.

## Parent Workflow

1. Parent or student marks wrong questions offline.
2. Parent uploads photos in Codex.
3. Parent says: “帮我生成错题知识点和测试题”.
4. Codex uses `fish-study-photo-workflow`.
5. Codex runs `study-context`, reads the photos, creates `wrong_question_training` JSON, runs `study-wrong`, and returns file links.

Parents should not need to see or edit JSON.

## Visual Mark Protocol

Each diagnosis may include:

```json
"visual_mark": {
  "color_detected": "红色圆形贴纸",
  "color_normalized": "red",
  "mark_type": "sticker",
  "evidence": "题号旁有红色圆形贴纸，颜色边界清晰。",
  "confidence": "high"
}
```

Allowed `color_normalized` values:

- `red`: maps to `不会`
- `yellow`: maps to `马虎`
- `blue`: maps to `时间不够`
- `unknown`: maps to `待确认`

Allowed `mark_type` values:

- `sticker`
- `marker`
- `circle`
- `underline`
- `unknown`

## Validation Rules

- `visual_mark.color_normalized` must match `diagnosis.sticker_color`.
- `unknown` must use `primary_reason: "待确认"` and `secondary_reason: "待确认"`.
- `unknown` must use `confirmation_status: "needs_confirmation"`.
- `unknown`, medium-confidence, and low-confidence items must appear in `uncertain_items`.
- Long-term statistics only accept high-confidence `red/yellow/blue` items with `auto` or `confirmed` status.

## Out Of Scope

- Python OCR or color segmentation.
- Automatic semantics for green or arbitrary colors.
- Inferring root cause from mark shape alone.
- Formal mock-paper PDF generation in the daily photo workflow.

