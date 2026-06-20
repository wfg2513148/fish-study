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
- Student paper must not contain answers or explanations.

For math:

- Include enough writing space for solution questions.
- Geometry or chart images must be readable and not too narrow.

For science:

- Use many diagram-based questions.
- Prefer clean black-and-white line art suitable for printing.
- Compress images for mobile-safe PDF size after generation.

For English:

- Reading, map, table, or scene images must be wide enough to read.
- Keep long text in HTML, not inside generated images.

## Image Rules

- Use `gpt-image-2` for all required diagrams.
- Follow `templates/exam-paper/figure-manifest.json` for subject minimums, existing figure purposes, and prompt rules.
- Store newly generated images locally under `outputs/exam-preview/assets/` while drafting.
- For a reusable sample or stable template image, move the final local image into `templates/exam-paper/assets/` or `templates/exam-paper/mobile/science-assets/` and update the corresponding HTML template.
- Use black-and-white textbook/workbook style unless the user asks otherwise.
- Avoid long generated text inside images.
- Check image dimensions visually and by DOM measurement.
- Fix images that render too narrow before exporting PDF.
- Knowledge-point explanations should also be illustrated when the concept is visual, spatial, structural, experimental, map-based, chart-based, or process-based.
- Put diagrams next to the matching knowledge point or question; do not hide them in a separate appendix.

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

## Delivery Rule

When sending generated files in the Codex conversation, use Markdown links with absolute local paths:

```md
[七年级下册数学模拟试卷.pdf](/absolute/path/to/fish-study/outputs/codex-session-files/七年级下册数学模拟试卷.pdf)
```

Do not rely on plain paths, `127.0.0.1`, or `/mnt/data` first.

## Reference

Full project notes: `docs/exam-paper-output.md`.
