# Fish Study Exam Paper Output

Use this skill when the user asks to generate, refine, review, or deliver Fish Study mock exam papers, especially when they mention real paper format, PDF, images, visual inspection, or Codex file delivery.

## Goal

Produce independent, print-ready exam papers that look like real school papers and are stable to open on another device.

## Assumptions

- The project root is the current Fish Study git checkout. Do not assume `/Users/kwang/fish-study`; confirm with `pwd` or the user's active workspace when needed.
- The tracked paper format source lives under `templates/exam-paper/`.
- Generated files live under `outputs/` and are not committed.
- Source materials and copyrighted originals stay local and are not committed.
- If a question needs a drawing or diagram, generate a real image with `gpt-image-2`; do not use placeholders.

## Reproducible Template Rule

When the user asks for the current formal mock-paper format, start from the tracked templates and script:

```bash
python3 scripts/generate_exam_paper.py --subject math
python3 scripts/generate_exam_paper.py --subject science
python3 scripts/generate_exam_paper.py --subject english
```

Use `--subject all` to generate the three tracked sample papers.

Do not recreate the exam CSS or HTML shell from scratch unless the user explicitly asks for a redesign. The stable layout, image sizing, print pagination, and local image references are recorded in:

- `templates/exam-paper/exam.css`
- `templates/exam-paper/math-grade7.html`
- `templates/exam-paper/science-grade7.html`
- `templates/exam-paper/english-grade7.html`
- `templates/exam-paper/figure-manifest.json`
- `scripts/generate_exam_paper.py`

`outputs/exam-preview/` is only a preview/export workspace. It is ignored by Git and cannot be used as the source of truth on another machine.

The generator validates that local images exist before exporting PDF. Current minimum image references:

- math: at least 3.
- science: at least 16.
- English: at least 1.

If validation fails, do not remove image requirements to make the script pass. Generate or restore the missing diagrams with `gpt-image-2`, then rerun the generator.

## Required Paper Standard

Each subject paper must be independent and use formal exam structure:

- A4 page.
- Main title with grade, semester, subject, and mock-paper label.
- Edition/source direction, total score, and suggested time.
- Name, class, score, and time fields.
- Sealing line or equivalent formal exam marker.
- Notice box.
- Section headers with question count, score per question, and total score.
- Realistic question mix, not toy examples.
- About 60% of questions must be choice questions. Count by question items: a question with an options block counts as choice.
- Student paper must not contain answers or explanations.
- Question numbers and subquestion numbers must use distinct forms. Main
  question numbers use `1.` / `2.` / `3.` and stay on the same line as the
  stem text. Subquestion numbers use `1）` / `2）` / `3）`; do not render them as
  the same dotted style as main question numbers.
- Do not create empty subquestion markers for questions that have no
  subquestions. Multiple-choice options are not subquestions; render them in an
  options block with clear A/B/C/D labels. If an option's content is itself a
  table row label such as A/B/C/D, clarify visually so it does not read like
  `A.A` / `B.B`.

For math:

- Include enough writing space for solution questions.
- Geometry or chart images must be readable and not too narrow.

For science:

- Use many diagram-based questions.
- Prefer clean black-and-white line art suitable for printing.
- Compress images for mobile-safe PDF size after generation.
- For science source-photo papers, use a source-first workflow instead of a
  generic math-paper template. Extract the original questions into a structured
  model before rendering: `question_id`, `stem`, `figures`, `subquestions`,
  `options`, and `tables`.
- Treat `subquestions` and multiple-choice `options` as different layout
  concepts. A question with no subquestions must not get an empty `1）` marker.
- Keep diagrams close to the exact stem or subquestion that references them.
  When a science question has multiple figures, split them by ownership rather
  than stacking all images after the stem. For example, render a `图1`
  apparatus after the stem, render A-D graph options inside the subquestion that
  asks for A-D, and render `图2` near the later subquestion that says `如图2`.

For English:

- Reading, map, table, or scene images must be wide enough to read.
- Keep long text in HTML, not inside generated images.

## Image Rules

- Use `gpt-image-2` for all required diagrams.
- Follow `templates/exam-paper/figure-manifest.json` for subject minimums, existing figure purposes, and prompt rules.
- When the user provides source screenshots for a science original-question
  paper, do not default to generated diagrams. Prefer cropping and cleaning the
  original source figure: remove phone UI, card shadows, and low-contrast
  background while preserving source geometry, labels, option letters, graph
  axes, table values, object counts, and experiment-control relationships.
- For source-photo reconstruction papers, treat the original figure as a locked
  contract. Preserve the original meaning, object count, grouping, labels, data
  values, axis names, relative positions, and experiment-control relationships.
- Do not allow the image model to invent a new diagram, add explanatory text,
  omit key objects, simplify controlled experiments, or change table/graph
  values. Only improve line clarity, print contrast, alignment, and A4
  readability when the question intent remains unchanged.
- Text inside reconstructed source figures must be limited to text that appears
  in the original figure, and Chinese labels must stay in Chinese.
- Each source figure must have a manifest entry with source path, source hash,
  crop bbox, cleaned local image path, cleaned image hash, owning
  question/subquestion, intended render location, must-preserve details, and
  verification status. If the screenshot itself omits a key region, mark it as
  source-limited and do not invent the missing content.
- Before delivery, visually compare every reconstructed source figure against
  the source photo or a locked detail manifest. Regenerate any figure whose key
  details do not match.
- Store newly generated images locally under `outputs/exam-preview/assets/` while drafting.
- For a reusable sample or stable template image, move the final local image into `templates/exam-paper/assets/` or `templates/exam-paper/mobile/science-assets/` and update the corresponding HTML template.
- Use black-and-white textbook/workbook style unless the user asks otherwise.
- Avoid long generated text inside images.
- Check image dimensions visually and by DOM measurement.
- Fix images that render too narrow before exporting PDF.
- Knowledge-point explanations should also be illustrated when the concept is visual, spatial, structural, experimental, map-based, chart-based, or process-based.
- Put diagrams next to the matching knowledge point or question; do not hide them in a separate appendix.

## Science Source-Photo Workflow

When the user provides science screenshots and asks for an A4 paper, original
question extraction, source-photo reconstruction, or format verification, use
this workflow as a hard contract:

1. Inventory inputs before rendering. Record each source screenshot path, hash,
   visible question range, and any low-confidence or missing region.
2. Build a structured question model before HTML/PDF: `question_id`, `stem`,
   `type`, `figures`, `tables`, `subquestions`, and `options`. Multiple-choice
   options must never be stored as subquestions.
3. Build a source-figure manifest that drives validation, not just notes. Every
   final `<img>` must map to exactly one manifest entry, and every manifest
   entry intended for the paper must appear exactly once in the HTML/PDF.
   Include both `source_sha256` and `cleaned_sha256`, and reject bbox values
   that are outside the source image or suspiciously small.
4. Use precise render anchors such as `after_stem`,
   `inside_subquestion_4`, or `after_options_table`; avoid vague placement like
   "near question". Complex science questions must split figure ownership by
   stem/subquestion/option block.
5. Preserve OCR-sensitive details: units, superscripts/subscripts, arrows,
   brackets, graph axes, tick labels, table rows/columns, option letters, figure
   numbers, Chinese labels, and experiment variables/control groups.
6. If a source screenshot omits key content, mark the figure `source_limited`
   and continue only by preserving visible source content. Do not fill missing
   regions from memory or generated diagrams unless the user explicitly asks.

### Science Source-Photo Stop Rules

Do not deliver the PDF if any of these are true:

- A source figure appears in HTML without a manifest entry, or a required
  manifest figure is absent from HTML/PDF.
- A source or cleaned figure hash does not match the manifest, or the figure
  renders under the wrong question/subquestion anchor.
- A source figure was replaced by inline SVG, `data:image/svg`, a generated
  image, a CSS background/image URL, or an old asset path without an explicit
  user request.
- A question without subquestions renders an empty `1）` marker.
- Multiple-choice options render as subquestions, or table-row options read as
  confusing labels like `A.A` / `B.B`.
- Multi-figure science questions use a generic stack that obscures which
  figure belongs to which subquestion.
- Final PDF pages have not been rendered to images and visually checked. For
  short science PDFs, inspect every page; otherwise inspect every page that
  contains figures, tables, option diagrams, or dense labels.

## PDF Rules

Final delivery must be PDF, not HTML.

- Images must be embedded in the PDF.
- Do not rely on remote images.
- Add footer page numbers in `current/total` format, for example `1/5`.
- Prefer Playwright `page.pdf` with browser PDF footer variables:

```html
<div style="width:100%;font-size:10px;color:#111;text-align:center;margin-bottom:5mm;">
  <span class="pageNumber"></span>/<span class="totalPages"></span>
</div>
```

- Do not stamp page numbers by editing raw PDF content streams unless there is no alternative; some viewers can extract that text but fail to render it.

## Verification Checklist

Before responding:

1. Use Playwright screenshots to inspect layout.
2. Confirm no broken images.
3. Confirm image widths are readable, especially math figure A, English maps, and science diagrams.
4. Export PDF with embedded images.
5. Use `pypdf` to verify page count, image count, and footer text on every page.
6. Use `qlmanage -t` or another renderer to make high-resolution previews and visually confirm footer page numbers are actually visible.
7. Keep science PDF small enough for mobile opening; compress science images if needed.
8. For science source-photo papers, run source-layout checks before delivery:
   no inline SVG or generated-image substitute for source figures unless
   explicitly requested; no old image paths; no empty subquestion markers; no
   `source-stack` style that hides figure ownership; no multiple-choice options
   rendered as subquestions; no confusing `A.A` / `B.B` option labels.
9. Render final PDF pages to images and inspect the pages containing complex
   science figures. Verify question numbers are inline with stems, subquestion
   numbers use `1）`, options use A/B/C/D blocks, and all figure labels,
   option letters, axes, units, table text, and diagram captions remain readable.
10. For science source-photo papers, run
    `scripts/validate_science_source_paper.py` against the manifest, HTML, PDF,
    and rendered page directory. This validator must pass before delivery; it
    checks manifest hashes, bbox bounds, image/question/subquestion ownership,
    PDF A4/page-footers, and rendered page freshness.

## Delivery Rule

When sending generated files in the Codex conversation, use Markdown links with absolute local paths:

```md
[七年级下册数学模拟试卷.pdf](/absolute/path/to/fish-study/outputs/codex-session-files/七年级下册数学模拟试卷.pdf)
```

Do not rely on plain paths, `127.0.0.1`, or `/mnt/data` first.

## Reference

Full project notes: `docs/exam-paper-output.md`.
