---
name: fish-study-photo-workflow
description: Use when a parent or student uploads one or more wrong-question photos in Codex and asks for knowledge points, root-cause analysis, practice questions, or a daily wrong-question training sheet. Handles multi-photo subject detection, visual color marks, stickers, marker circles/underlines, Fish Study JSON, CLI execution, and local file delivery.
---

# Fish Study Photo Workflow

Turn marked wrong-question photos into Fish Study training outputs while keeping the user path simple: the parent or student uploads one or more photos and says one sentence such as “帮我生成错题知识点和测试题”.

## Boundary

- Codex performs visual recognition from uploaded photos.
- The Python CLI only validates structured JSON, renders materials, and writes Obsidian records.
- Do not ask the parent to write or edit JSON.
- Do not use this skill for formal mock exam PDFs; use `fish-study-exam-paper` for real paper format, gpt-image-2 diagrams, PDF export, and PDF visual checks.
- Knowledge-point explanations should be illustrated when the concept is visual, spatial, experimental, structural, map-based, chart-based, or process-based.

## Workflow

1. Confirm the current Fish Study repo root with `pwd`.
2. Run:

```bash
python3 -m fish_study_wiki.cli study-context
```

3. Read each uploaded photo visually:
   - transcribe the wrong question enough to identify subject, problem type, and knowledge point;
   - assign a stable `photo_id` such as `photo-001`;
   - infer the subject for that photo: `数学`, `科学`, `英语`, or `unknown`;
   - inspect visible marks near each question;
   - record the mark color, mark type, and visual evidence.
4. Normalize colors:
   - red -> `red` -> `不会`;
   - yellow -> `yellow` -> `马虎`;
   - blue -> `blue` -> `时间不够`;
   - green, orange, purple, mixed colors, glare, unclear colors, or no clear mark -> `unknown` and `待确认`.
5. Generate `wrong_question_training` JSON under `outputs/photo-workflow/YYYY-MM-DD-wrong-question-training.json`.
   - Add top-level `source_photos`.
   - Add `source_photo_ids` to each analysis cluster.
   - Group clusters by subject. Do not mix different subjects into one cluster.
   - Put unknown-subject or low-confidence photos into `uncertain_items`; do not reference them from clusters.
6. Run:

```bash
python3 -m fish_study_wiki.cli study-wrong outputs/photo-workflow/YYYY-MM-DD-wrong-question-training.json
```

7. Export generated daily materials to PDF, copy delivery PDFs into
   `outputs/codex-session-files/`, and return links using the exact local-file
   link contract below.

## Illustrated Knowledge Rule

Daily knowledge explanations must not become plain text dumps when diagrams would make the concept easier to understand.

- For math, add diagrams for geometry, coordinate systems, transformations, charts, and word-problem quantity relationships.
- For science, add diagrams for apparatus, biological structures, matter models, physical processes, charts, and experiment variables.
- For English, add maps, route sketches, timetables, classroom scenes, or reading-context images when they support comprehension.
- Use `gpt-image-2` for new diagrams; use black-and-white workbook style unless the user asks otherwise.
- Keep long explanation text in Markdown or HTML, not inside the image.
- Put each diagram next to the matching knowledge point or training question.
- Save user-facing illustrated PDFs under `outputs/codex-session-files/` and deliver them with exact filename Markdown links.

If the user asks for a real mock exam, use `fish-study-exam-paper`; that workflow enforces `templates/exam-paper/figure-manifest.json`, local image existence, image readability, and PDF embedding.

## Knowledge Card Rule

Student-facing knowledge cards are generated from the current batch of wrong
questions, but they must teach the knowledge point rather than describe the
wrong-question record.

- Extract cards from confirmed `matched_knowledge` in the current batch.
- Filter `待定位`, low-confidence, and unorderable knowledge points from the
  student-facing card set.
- Deduplicate by knowledge-point name so the same point appears once.
- Sort by learning order, using `grade -> volume -> chapter -> note` and then
  concept/property/method/application order; never sort by photo order,
  question order, color, or diagnosis order.
- Each card must include the knowledge-point name, core definition or
  structure, key formula/rule/relationship, application steps or solution
  tricks, common pitfalls, a self-check prompt, and an independent diagram when
  helpful.
- Knowledge-card diagrams must be generated with `gpt-image-2` through
  `~/.codex/skills/gpt-image-2/scripts/generate-image.sh`; do not use hand-made
  SVG, CSS shapes, screenshots, or placeholder diagrams for student-facing
  knowledge cards.
- Do not draw for decoration. Classify each card image need as `required`,
  `optional`, or `omit`; omit images for concepts where a diagram would be
  generic, misleading, or less useful than text.
- Each generated image must have a prompt spec with `visual_goal`, `must_show`,
  `must_not_show`, `allowed_labels`, and `common_misconception`.
- Each generated image needs a visual review: it must accurately show the
  knowledge relationship, avoid misleading arrows or symbols, keep Chinese
  labels readable, avoid crowding/cropping on A4, and contain no chapter,
  section, lesson, question, source, or diagnosis text. If it remains
  unacceptable after 1-2 retries, delete it and render the card without an
  image.
- When Chinese labels are useful, integrate short labels with the diagram
  objects by placing them near the relevant part and using leader lines or
  arrows. Do not add detached top/bottom overlay explanation boxes, long text
  panels, or decorative captions inside the image. If the image does not
  support the core knowledge point after labels, omit it.
- Knowledge-card image prompts, image alt text, and image captions must use a
  concept-only title; do not include textbook locating labels such as `第几章`,
  `第几节`, `第几课时`, or `专题编号` in images or image captions.
- Diagrams are based on the knowledge point itself, not on the original
  question figure. They may simplify or clarify the concept, but must not
  include original photo IDs, filenames, question numbers, source labels,
  diagnosis evidence, sticker colors, or training advice.
- During early targeted generation, internal error types may guide the
  explanation focus, but the card should phrase this as a student-facing
  `复习重点` instead of exposing diagnosis wording.
- The student-facing card text must not contain photo/source/question/diagnosis
  wording such as `photo-`, `照片`, `来源`, `第1题`, `本题`, `这道题`, `错因`,
  `依据`, `诊断`, `训练建议`, `难度梯度`, `红色`, `黄色`, or `蓝色`.
- If a student can read the card without seeing the original wrong question and
  still explain what to remember, how to calculate or judge, and what to avoid,
  the card is acceptable.

## Multi-Photo Subject JSON

Use `source_photos` whenever the user uploads photos:

```json
{
  "source_photos": [
    {
      "photo_id": "photo-001",
      "label_or_filename": "science-red-sticker.jpg",
      "subject": "科学",
      "confidence": "high",
      "evidence": "题干包含原子结构、质子、中子和电子。",
      "status": "recognized"
    },
    {
      "photo_id": "photo-002",
      "label_or_filename": "unclear-green-mark.jpg",
      "subject": "unknown",
      "confidence": "low",
      "evidence": "只拍到局部题干和绿色标注，无法稳定判断学科。",
      "status": "needs_confirmation"
    }
  ],
  "uncertain_items": [
    "photo-002 unclear-green-mark.jpg 学科待确认"
  ]
}
```

Rules:

- `subject`: `数学`, `科学`, `英语`, or `unknown`.
- `status`: `recognized`, `needs_confirmation`, or `excluded`.
- Any `unknown`, `medium`, `low`, or `needs_confirmation` photo must appear in `uncertain_items`.
- `source_photo_ids` may reference only recognized photos from the same subject as the cluster.
- Daily outputs are “分学科训练卷”, not formal “模拟试卷”.

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
- Link the aggregate student PDF, per-subject student PDFs, answer PDFs, and knowledge-note PDFs.
- Do not expose the JSON unless the user asks.

Use the Codex local-file delivery contract:

- Put every user-facing PDF, and any ZIP bundle, under
  `outputs/codex-session-files/`.
- Use Markdown links whose visible label is the exact filename, not descriptive
  text.
- Point each link to the absolute local path.
- Do not wrap file links in code fences or backticks.
- Do not use plain paths, `127.0.0.1` URLs, `/mnt/data` paths, or links to
  ordinary dated output folders for user delivery.
- This filename-label pattern is required for files to open reliably from the
  Codex/iPhone conversation UI.

Correct:

```md
[2026-06-20-science-training.pdf](/Users/kwang/fish-study/outputs/codex-session-files/2026-06-20-science-training.pdf)
```

Incorrect:

```md
[科学训练卷 PDF](/Users/kwang/fish-study/outputs/2026-06-20/science-training.pdf)
```

## Verification

Before finishing:

```bash
python3 -m fish_study_wiki.cli study-context
python3 -m fish_study_wiki.cli study-wrong <generated-json>
python3 -m pytest -q
```

For generated daily PDF sheets, visually inspect the rendered page when practical:

- A4 layout is readable.
- Student sheet contains no answers or explanations.
- Answer sheet contains answers, scoring points, and mastery signals.
- No text overlaps or clipped question content.
- Delivery copies exist in `outputs/codex-session-files/`.
- Final links use exact PDF filenames as labels and absolute paths to
  `outputs/codex-session-files/`.

If the user asks for formal mock papers or PDF output, switch to `fish-study-exam-paper` and run the stricter PDF visual-recognition checks required there.
