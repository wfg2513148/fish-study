#!/usr/bin/env python3
"""Validate science source-photo A4 paper artifacts before delivery.

This script checks structural invariants that repeatedly caused regressions:
source figure traceability, figure ownership, option/subquestion confusion, and
PDF/rendered-page evidence. It does not replace human visual review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse


BAD_HTML_TOKENS = [
    "<svg",
    "data:image",
    "gpt-image-figures",
    "source-stack",
]

BLOCKING_STATUSES = {"fail", "failed", "uncertain", "needs_human_review", "pending"}
REQUIRED_FIGURE_FIELDS = {
    "figure_id",
    "question_id",
    "source_photo",
    "source_sha256",
    "source_crop_bbox",
    "cleaned_path",
    "cleaned_sha256",
    "belongs_to",
    "render_near",
    "must_preserve_details",
    "verification_status",
}


class PaperHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.images: list[dict] = []
        self.in_question = False
        self.current_question: int | None = None
        self.in_qno = False
        self.in_parts = False
        self.part_index = 0
        self.current_part: int | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        classes = set((attrs_dict.get("class") or "").split())
        lowered = tag.lower()
        if lowered == "article" and "question" in classes:
            self.in_question = True
            self.current_question = None
            self.in_parts = False
            self.part_index = 0
            self.current_part = None
        elif self.in_question and lowered == "span" and "q-no" in classes:
            self.in_qno = True
        elif self.in_question and lowered == "ol" and "parts" in classes:
            self.in_parts = True
            self.part_index = 0
            self.current_part = None
        elif self.in_question and self.in_parts and lowered == "li":
            self.part_index += 1
            self.current_part = self.part_index

        if lowered != "img":
            return
        src = attrs_dict.get("src")
        if src:
            self.images.append(
                {
                    "src": src,
                    "question_id": self.current_question,
                    "part": self.current_part,
                }
            )

    def handle_data(self, data: str) -> None:
        if not self.in_qno:
            return
        match = re.search(r"(\d+)", data)
        if match:
            self.current_question = int(match.group(1))

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered == "span":
            self.in_qno = False
        elif lowered == "li":
            self.current_part = None
        elif lowered == "ol":
            self.in_parts = False
            self.current_part = None
        elif lowered == "article":
            self.in_question = False
            self.current_question = None
            self.in_parts = False
            self.current_part = None


def fail(message: str) -> None:
    raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def path_from_src(src: str, base_dir: Path) -> Path:
    parsed = urlparse(src)
    if parsed.scheme == "file":
        return Path(unquote(parsed.path)).resolve()
    if parsed.scheme:
        fail(f"remote or unsupported image source is not allowed: {src}")
    return (base_dir / unquote(src)).resolve()


def image_dimensions(path: Path) -> tuple[int, int] | None:
    with path.open("rb") as handle:
        header = handle.read(24)
        if len(header) >= 24 and header.startswith(b"\x89PNG\r\n\x1a\n"):
            return int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")
        if len(header) >= 2 and header[:2] == b"\xff\xd8":
            handle.seek(2)
            while True:
                marker_start = handle.read(1)
                if not marker_start:
                    return None
                if marker_start != b"\xff":
                    continue
                marker = handle.read(1)
                while marker == b"\xff":
                    marker = handle.read(1)
                if marker in {b"\xd8", b"\xd9"}:
                    continue
                length_data = handle.read(2)
                if len(length_data) != 2:
                    return None
                length = int.from_bytes(length_data, "big")
                if length < 2:
                    return None
                if marker and marker[0] in {
                    0xC0,
                    0xC1,
                    0xC2,
                    0xC3,
                    0xC5,
                    0xC6,
                    0xC7,
                    0xC9,
                    0xCA,
                    0xCB,
                    0xCD,
                    0xCE,
                    0xCF,
                }:
                    segment = handle.read(length - 2)
                    if len(segment) < 5:
                        return None
                    return int.from_bytes(segment[3:5], "big"), int.from_bytes(segment[1:3], "big")
                handle.seek(length - 2, 1)
    return None


def load_manifest(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    figures = data.get("figures")
    if not isinstance(figures, list) or not figures:
        fail("manifest must contain a non-empty figures list")
    declared_count = data.get("figure_count")
    if declared_count is not None and declared_count != len(figures):
        fail(f"manifest figure_count={declared_count} but figures has {len(figures)} entries")
    return figures


def validate_manifest(figures: list[dict], fail_on_source_limited: bool) -> dict[Path, dict]:
    cleaned_to_figure: dict[Path, dict] = {}
    seen_ids: set[str] = set()
    for index, figure in enumerate(figures, start=1):
        missing = sorted(REQUIRED_FIGURE_FIELDS - figure.keys())
        if missing:
            fail(f"manifest figure #{index} missing fields: {', '.join(missing)}")
        figure_id = str(figure["figure_id"])
        if figure_id in seen_ids:
            fail(f"duplicate figure_id in manifest: {figure_id}")
        seen_ids.add(figure_id)

        status = str(figure["verification_status"])
        if status in BLOCKING_STATUSES:
            fail(f"figure {figure_id} has blocking verification_status={status}")
        if status == "source_limited" and fail_on_source_limited:
            fail(f"figure {figure_id} is source_limited")
        if status == "source_limited" and not figure.get("issues"):
            fail(f"source_limited figure {figure_id} must explain issues")

        source = Path(str(figure["source_photo"]))
        if not source.exists():
            fail(f"source photo missing for {figure_id}: {source}")
        expected_hash = str(figure["source_sha256"])
        actual_hash = sha256(source)
        if actual_hash != expected_hash:
            fail(f"source hash mismatch for {figure_id}: expected {expected_hash}, got {actual_hash}")
        source_dimensions = image_dimensions(source)

        bbox = figure["source_crop_bbox"]
        for field in ("left", "top", "right", "bottom"):
            if field not in bbox or not isinstance(bbox[field], int):
                fail(f"figure {figure_id} has invalid bbox field: {field}")
        if bbox["left"] >= bbox["right"] or bbox["top"] >= bbox["bottom"]:
            fail(f"figure {figure_id} bbox has non-positive size")
        if (bbox["right"] - bbox["left"]) < 20 or (bbox["bottom"] - bbox["top"]) < 20:
            fail(f"figure {figure_id} bbox is suspiciously small")
        if source_dimensions:
            width, height = source_dimensions
            if bbox["left"] < 0 or bbox["top"] < 0 or bbox["right"] > width or bbox["bottom"] > height:
                fail(f"figure {figure_id} bbox is outside source image bounds {width}x{height}")

        details = figure["must_preserve_details"]
        if not isinstance(details, list) or not details:
            fail(f"figure {figure_id} must list must_preserve_details")
        if str(figure["render_near"]).strip() in {"", "near question", "after question"}:
            fail(f"figure {figure_id} needs a precise render_near anchor")

        cleaned = Path(str(figure["cleaned_path"])).resolve()
        if cleaned in cleaned_to_figure:
            fail(f"duplicate cleaned_path in manifest: {cleaned}")
        if not cleaned.exists() or cleaned.stat().st_size == 0:
            fail(f"cleaned image missing or empty for {figure_id}: {cleaned}")
        cleaned_hash = sha256(cleaned)
        expected_cleaned_hash = str(figure["cleaned_sha256"])
        if cleaned_hash != expected_cleaned_hash:
            fail(
                f"cleaned image hash mismatch for {figure_id}: "
                f"expected {expected_cleaned_hash}, got {cleaned_hash}"
            )
        dimensions = image_dimensions(cleaned)
        if dimensions and (dimensions[0] < 40 or dimensions[1] < 40):
            fail(f"cleaned image too small for {figure_id}: {dimensions[0]}x{dimensions[1]}")
        cleaned_to_figure[cleaned] = figure
    return cleaned_to_figure


def expected_subquestion(figure: dict) -> int | None:
    text = f"{figure.get('render_near', '')} {figure.get('belongs_to', '')}"
    match = re.search(r"(?:inside|after)_subquestion_(\d+)", text)
    if match:
        return int(match.group(1))
    match = re.search(r"\bsubquestion_(\d+)\b", text)
    if match:
        return int(match.group(1))
    return None


def validate_image_context(image: dict, figure: dict) -> None:
    figure_id = str(figure["figure_id"])
    actual_question = image["question_id"]
    try:
        expected_question = int(figure["question_id"])
    except (TypeError, ValueError):
        fail(f"figure {figure_id} has non-numeric question_id")
    if actual_question != expected_question:
        fail(
            f"figure {figure_id} rendered under question {actual_question}, "
            f"expected question {expected_question}"
        )

    expected_part = expected_subquestion(figure)
    actual_part = image["part"]
    if expected_part is not None and actual_part != expected_part:
        fail(f"figure {figure_id} rendered under subquestion {actual_part}, expected {expected_part}")
    if expected_part is None and str(figure["render_near"]).startswith("after_stem") and actual_part is not None:
        fail(f"figure {figure_id} should render after stem, but appeared inside subquestion {actual_part}")


def validate_html(html_path: Path, cleaned_to_figure: dict[Path, dict]) -> list[Path]:
    html = html_path.read_text(encoding="utf-8")
    lowered = html.lower()
    for token in BAD_HTML_TOKENS:
        if token.lower() in lowered:
            fail(f"forbidden HTML token remains: {token}")
    if re.search(r"background-image\s*:", lowered):
        fail("background-image is not allowed in source-photo papers")
    for css_url in re.findall(r"url\(([^)]+)\)", html, flags=re.I):
        stripped = css_url.strip("\"' \t\r\n")
        if stripped.startswith("data:") or re.search(r"\.(?:png|jpe?g|webp|gif|svg)(?:[?#].*)?$", stripped, re.I):
            fail(f"CSS image url bypasses manifest: {stripped}")

    empty_part_patterns = [
        r'<ol\s+class="parts"\s*>\s*</ol>',
        r'<ol\s+class="parts"\s*>\s*<li>\s*(?:<span\s+class="answer-line"\s*>\s*</span>)?\s*</li>\s*</ol>',
    ]
    for pattern in empty_part_patterns:
        if re.search(pattern, html, flags=re.I | re.S):
            fail("empty subquestion marker remains")
    if re.search(r'<ol\s+class="parts"\s*>\s*<li>\s*A\.', html, flags=re.I):
        fail("multiple-choice options appear to be rendered as subquestions")
    if re.search(r'>\s*[A-D]\.\s*[A-D]\s*<', html):
        fail("confusing option label like A.A / B.B remains")

    parser = PaperHTMLParser()
    parser.feed(html)
    image_paths = [path_from_src(image["src"], html_path.parent) for image in parser.images]
    if not image_paths:
        fail("HTML contains no images")

    used_counts: dict[Path, int] = {}
    for image, path in zip(parser.images, image_paths):
        if path not in cleaned_to_figure:
            fail(f"HTML image has no manifest entry: {path}")
        validate_image_context(image, cleaned_to_figure[path])
        used_counts[path] = used_counts.get(path, 0) + 1
    for path, figure in cleaned_to_figure.items():
        count = used_counts.get(path, 0)
        if count != 1:
            fail(f"manifest figure {figure['figure_id']} appears {count} times in HTML, expected once")
    return image_paths


def validate_pdf(pdf_path: Path, expected_images: int) -> int:
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        fail(f"PDF missing or empty: {pdf_path}")
    try:
        from pypdf import PdfReader
    except Exception as error:  # pragma: no cover - environment dependent
        fail(f"pypdf is required for PDF validation: {error}")

    reader = PdfReader(str(pdf_path))
    page_count = len(reader.pages)
    if page_count <= 0:
        fail("PDF has no pages")
    image_count = 0
    for index, page in enumerate(reader.pages, start=1):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        if not (590 <= width <= 600 and 835 <= height <= 850):
            fail(f"PDF page {index} is not A4-sized: {width:.2f}x{height:.2f} pt")
        text = page.extract_text() or ""
        expected_footer = f"{index}/{page_count}"
        if expected_footer not in text:
            fail(f"PDF page {index} missing extractable footer {expected_footer}")
        try:
            image_count += len(page.images)
        except Exception:
            pass
    if image_count < expected_images:
        fail(f"PDF contains {image_count} images, expected at least {expected_images}")
    return page_count


def validate_render_dir(render_dir: Path, pdf_path: Path, page_count: int) -> None:
    if not render_dir.exists():
        fail(f"rendered page directory missing: {render_dir}")
    pages = sorted(render_dir.glob("page-*.png"))
    expected_names = [f"page-{index:02d}.png" for index in range(1, page_count + 1)]
    actual_names = [page.name for page in pages]
    if actual_names != expected_names:
        fail(f"rendered page images must exactly match PDF pages: expected {expected_names}, got {actual_names}")
    pdf_mtime = pdf_path.stat().st_mtime
    for index, page in enumerate(pages, start=1):
        if page.stat().st_size == 0:
            fail(f"rendered page image is empty: {page}")
        if page.stat().st_mtime < pdf_mtime:
            fail(f"rendered page image is older than PDF: {page}")
        dimensions = image_dimensions(page)
        if not dimensions:
            fail(f"rendered page image is not a readable PNG/JPEG: {page}")
        width, height = dimensions
        if width < 700 or height < 900:
            fail(f"rendered page image {index} is too small: {width}x{height}")
        ratio = height / width
        if not (1.37 <= ratio <= 1.46):
            fail(f"rendered page image {index} is not A4 ratio: {width}x{height}")
        if page.stat().st_size < 30_000:
            fail(f"rendered page image {index} is suspiciously small/blank: {page.stat().st_size} bytes")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--html", required=True, type=Path)
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--render-dir", required=True, type=Path)
    parser.add_argument(
        "--fail-on-source-limited",
        action="store_true",
        help="Treat source_limited figures as blocking instead of documented source limitations.",
    )
    args = parser.parse_args()

    figures = load_manifest(args.manifest)
    cleaned_to_figure = validate_manifest(figures, args.fail_on_source_limited)
    validate_html(args.html, cleaned_to_figure)
    page_count = validate_pdf(args.pdf, expected_images=len(cleaned_to_figure))
    validate_render_dir(args.render_dir, args.pdf, page_count)
    print(
        "OK: science source paper artifacts validated "
        f"({len(figures)} manifest figures, {page_count} PDF pages)."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
