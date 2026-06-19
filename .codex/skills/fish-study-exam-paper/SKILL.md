# Fish Study Exam Paper Output

Use this skill when the user asks to generate, refine, review, or deliver Fish Study mock exam papers, especially when they mention real paper format, PDF, images, visual inspection, or Codex file delivery.

## Goal

Produce independent, print-ready exam papers that look like real school papers and are stable to open on another device.

## Assumptions

- The project root is `/Users/kwang/fish-study`.
- Generated files live under `outputs/` and are not committed.
- Source materials and copyrighted originals stay local and are not committed.
- If a question needs a drawing or diagram, generate a real image with `gpt-image-2`; do not use placeholders.

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
- Store images locally under `outputs/exam-preview/assets/`.
- Use black-and-white textbook/workbook style unless the user asks otherwise.
- Avoid long generated text inside images.
- Check image dimensions visually and by DOM measurement.
- Fix images that render too narrow before exporting PDF.

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
[math-grade7-mock-paper.pdf](/Users/kwang/fish-study/outputs/codex-session-files/math-grade7-mock-paper.pdf)
```

Do not rely on plain paths, `127.0.0.1`, or `/mnt/data` first.

## Reference

Full project notes: `docs/exam-paper-output.md`.
