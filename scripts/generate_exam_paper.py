#!/usr/bin/env python3
from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / "templates" / "exam-paper"

SUBJECTS = {
    "math": ("math-grade7.html", "七年级下册数学模拟试卷.pdf"),
    "science": ("science-grade7.html", "七年级下册科学模拟试卷.pdf"),
    "english": ("english-grade7.html", "七年级下册英语模拟试卷.pdf"),
}

MIN_IMAGE_REFS = {
    "math": 3,
    "science": 16,
    "english": 1,
}

PRINT_GUARD_CSS = """
@media print {
  .question,
  .answer-box {
    break-inside: avoid !important;
    page-break-inside: avoid !important;
  }
  .section {
    break-inside: auto !important;
  }
}
"""

PDF_SCRIPT = r"""
const { chromium } = require('playwright');
const [htmlPath, pdfPath, extraCss] = process.argv.slice(1);

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1240, height: 1754 } });
  await page.goto('file://' + htmlPath, { waitUntil: 'networkidle' });
  await page.addStyleTag({ content: extraCss });
  const imageIssues = await page.$$eval('img', (imgs) => {
    const minReadableWidth = 160;
    return imgs.flatMap((img) => {
      const rect = img.getBoundingClientRect();
      const issues = [];
      if (!img.complete || img.naturalWidth === 0 || img.naturalHeight === 0) {
        issues.push(`${img.getAttribute('src')}: failed to load`);
      }
      if (rect.width < minReadableWidth) {
        issues.push(`${img.getAttribute('src')}: rendered width ${Math.round(rect.width)}px is too narrow`);
      }
      return issues;
    });
  });
  if (imageIssues.length > 0) {
    throw new Error('Image validation failed before PDF export:\n' + imageIssues.join('\n'));
  }
  await page.pdf({
    path: pdfPath,
    format: 'A4',
    printBackground: true,
    preferCSSPageSize: true,
    displayHeaderFooter: true,
    headerTemplate: '<div></div>',
    footerTemplate: '<div style="width:100%;font-size:10px;color:#111;text-align:center;margin-bottom:5mm;"><span class="pageNumber"></span>/<span class="totalPages"></span></div>',
    margin: { top: '0mm', right: '0mm', bottom: '9mm', left: '0mm' }
  });
  await browser.close();
})().catch((error) => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
});
"""


class ImageSrcParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.sources: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "img":
            return
        attributes = dict(attrs)
        src = attributes.get("src")
        if src:
            self.sources.append(src)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate reproducible Fish Study formal mock exam PDFs from tracked templates.",
    )
    parser.add_argument(
        "--subject",
        choices=sorted([*SUBJECTS, "all"]),
        default="math",
        help="Subject paper to generate. Use all for the three tracked sample papers.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs" / "codex-session-files",
        help="Directory for final PDF files.",
    )
    parser.add_argument(
        "--preview-dir",
        type=Path,
        default=ROOT / "outputs" / "exam-preview" / "generated",
        help="Directory for copied HTML/CSS/image preview files.",
    )
    return parser.parse_args()


def ensure_template_exists() -> None:
    missing = [
        str(TEMPLATE_DIR / name)
        for name, _ in SUBJECTS.values()
        if not (TEMPLATE_DIR / name).exists()
    ]
    if missing:
        raise SystemExit("Missing exam paper templates:\n" + "\n".join(missing))


def copy_templates(preview_dir: Path) -> None:
    preview_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(TEMPLATE_DIR, preview_dir, dirs_exist_ok=True)


def validate_subject_images(subject: str, html_path: Path) -> None:
    parser = ImageSrcParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    min_refs = MIN_IMAGE_REFS[subject]
    if len(parser.sources) < min_refs:
        raise RuntimeError(
            f"{subject} paper must contain at least {min_refs} local image references; "
            f"found {len(parser.sources)}. Follow templates/exam-paper/figure-manifest.json "
            "and generate missing diagrams with gpt-image-2."
        )
    missing = [
        src
        for src in parser.sources
        if src.startswith(("http://", "https://")) or not (html_path.parent / src).exists()
    ]
    if missing:
        raise RuntimeError(
            "Missing or non-local paper images:\n"
            + "\n".join(missing)
            + "\nUse gpt-image-2 for new diagrams, save them under templates/exam-paper/, "
            "and keep final PDF images local and embedded."
        )


def validate_figure_manifest() -> None:
    manifest_path = TEMPLATE_DIR / "figure-manifest.json"
    if not manifest_path.exists():
        raise RuntimeError("Missing templates/exam-paper/figure-manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for subject, min_refs in MIN_IMAGE_REFS.items():
        subject_rules = manifest.get("subjects", {}).get(subject, {})
        if subject_rules.get("min_image_references") != min_refs:
            raise RuntimeError(
                f"figure manifest min_image_references for {subject} must be {min_refs}"
            )


def export_pdf(html_path: Path, pdf_path: Path) -> None:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        ["node", "-e", PDF_SCRIPT, str(html_path), str(pdf_path), PRINT_GUARD_CSS],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(
            "failed to export PDF with Playwright. "
            "Install Node.js and Playwright, then run `npx playwright install chromium` if needed. "
            f"Details: {detail}"
        )


def generate_subject(subject: str, preview_dir: Path, output_dir: Path) -> Path:
    html_name, pdf_name = SUBJECTS[subject]
    html_path = preview_dir / html_name
    validate_subject_images(subject, html_path)
    pdf_path = output_dir / pdf_name
    export_pdf(html_path, pdf_path)
    return pdf_path


def main() -> int:
    args = parse_args()
    ensure_template_exists()
    validate_figure_manifest()
    copy_templates(args.preview_dir)
    subjects = list(SUBJECTS) if args.subject == "all" else [args.subject]
    for subject in subjects:
        pdf_path = generate_subject(subject, args.preview_dir, args.output_dir)
        print(pdf_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
