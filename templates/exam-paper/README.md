# Exam Paper Templates

This directory is the tracked source of truth for the current Fish Study formal mock-paper format.

Do not rebuild the paper CSS from memory. Use these templates first, then edit only the subject content or image references required by the task.

## Files

- `exam.css`: A4 formal exam-paper layout, seal line, header, info fields, notice box, section titles, answer boxes, figure sizing, and print pagination guards.
- `math-grade7.html`: current reproducible math sample paper.
- `science-grade7.html`: current reproducible science sample paper using compressed local images for mobile-safe PDF size.
- `english-grade7.html`: current reproducible English sample paper.
- `figure-manifest.json`: image minimums, existing figure purposes, and `gpt-image-2` prompt rules.
- `assets/`: local math and English images embedded by the templates.
- `mobile/science-assets/`: compressed local science images embedded by the science template.

The generator fails if required images are missing. Current minimum image references:

- math: 3
- science: 16
- English: 1

The stable paper templates keep choice questions at 60% by question count:

- math: 15 choice questions out of 25 total questions
- science: 18 choice questions out of 30 total questions
- English: 27 choice-style questions out of 45 total question items

## Generate PDFs

From the repository root:

```bash
python3 scripts/generate_exam_paper.py --subject math
python3 scripts/generate_exam_paper.py --subject science
python3 scripts/generate_exam_paper.py --subject english
```

Or generate all three:

```bash
python3 scripts/generate_exam_paper.py --subject all
```

Final PDFs are written to:

```text
outputs/codex-session-files/
```

Default PDF filenames are Chinese:

```text
七年级下册数学模拟试卷.pdf
七年级下册科学模拟试卷.pdf
七年级下册英语模拟试卷.pdf
```

The copied HTML/CSS/image preview bundle is written to:

```text
outputs/exam-preview/generated/
```

Both output directories remain ignored by Git. The reproducible source files in this directory are committed.
