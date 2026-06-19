# Complete Obsidian Wiki Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete, locally verifiable Obsidian wiki for Grade 7 and Grade 8 study support across all subjects used in the fish-study workflow.

**Architecture:** Convert local source materials into a canonical curriculum catalog, extract lesson/topic candidates, render each topic as a linked Obsidian note, and run quality gates that prove coverage by grade, volume, subject, chapter, source, and note status. The system must keep copyrighted source files local while committing only scripts, inventories, metadata, generated summaries, and verification reports.

**Tech Stack:** Python 3 standard library, Markdown, JSON, shell wrappers, Git, GitHub private repo, Obsidian local vault at `/Users/kwang/Downloads/obsidian/fish-study`.

---

## Scope Definition

This plan covers one integrated subsystem: the local source-to-Obsidian wiki pipeline. It intentionally does not build a separate app. The result is a reproducible repository workflow that can be run from `/Users/kwang/fish-study` and writes the vault in `/Users/kwang/Downloads/obsidian/fish-study`.

“Complete wiki” means:

- Every grade/volume/subject combination for Grade 7 and Grade 8 has a subject index note.
- Every confirmed or locally available source has a checksum, inventory, and source ledger entry.
- Every extracted lesson/topic has an Obsidian note with frontmatter, source pointer, status, and links.
- Missing source coverage is explicit in `reports/wiki-quality.md`; it is not silently guessed.
- The build is reproducible by running one command.

## File Structure

- Create `fish_study_wiki/__init__.py`: package marker.
- Create `fish_study_wiki/settings.py`: absolute local paths, subject matrix, and status constants.
- Create `fish_study_wiki/models.py`: dataclasses for sources, curriculum entries, topic notes, and validation issues.
- Create `fish_study_wiki/source_ledger.py`: load and validate source metadata from JSON.
- Create `fish_study_wiki/zip_inventory.py`: decode ZIP file names and write readable inventories.
- Create `fish_study_wiki/pptx_text.py`: extract visible text from PPTX files using OpenXML.
- Create `fish_study_wiki/topic_builder.py`: turn source inventories and PPTX text into topic note records.
- Create `fish_study_wiki/note_renderer.py`: render deterministic Obsidian Markdown.
- Create `fish_study_wiki/vault_writer.py`: write directories, indexes, and notes into the vault.
- Create `fish_study_wiki/quality.py`: validate coverage and write quality reports.
- Create `fish_study_wiki/cli.py`: command-line entrypoint for inventory, extract, build, and verify.
- Modify `scripts/download_sources.sh`: call the Python inventory command after downloads.
- Modify `scripts/init_vault.sh`: keep only vault bootstrap; delegate knowledge notes to the Python CLI.
- Modify `scripts/rebuild_zip_inventories.py`: wrapper that calls `fish_study_wiki.cli inventory`.
- Modify `scripts/build_vault_indexes.py`: wrapper that calls `fish_study_wiki.cli build`.
- Create `data/catalog/subject-matrix.json`: all supported grade/volume/subject combinations.
- Create `data/sources/source-ledger.json`: confirmed source records and local file paths.
- Create `reports/wiki-quality.md`: generated coverage report.
- Create `tests/fixtures/make_pptx_fixture.py`: create a tiny PPTX fixture using stdlib ZIP/XML.
- Create `tests/test_source_ledger.py`: source metadata tests.
- Create `tests/test_zip_inventory.py`: ZIP decoding tests.
- Create `tests/test_pptx_text.py`: PPTX extraction tests.
- Create `tests/test_topic_builder.py`: topic record tests.
- Create `tests/test_note_renderer.py`: Markdown rendering tests.
- Create `tests/test_quality.py`: coverage validation tests.

---

### Task 1: Add Testable Python Package Skeleton

**Files:**
- Create: `fish_study_wiki/__init__.py`
- Create: `fish_study_wiki/settings.py`
- Create: `fish_study_wiki/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Create model tests**

Write `tests/test_models.py`:

```python
from fish_study_wiki.models import SourceRecord, TopicNote


def test_source_record_requires_local_path_for_local_source():
    source = SourceRecord(
        source_id="5star-math-zjjy-g7b-2026spring",
        subject="数学",
        grade="七年级",
        volume="下册",
        version="浙教版",
        source_type="courseware",
        status="available",
        local_path="/Users/kwang/fish-study/sources/raw/5star-math-zjjy-g7b-2026spring.zip",
        sha256="25cb0437ab0d8fa94eb661d402ffda3b06165545d50d591785705a4890d4e6ff",
    )

    assert source.key == "七年级/下册/数学"
    assert source.is_available is True


def test_topic_note_slug_is_filesystem_safe():
    note = TopicNote(
        title='第1章 1.2 同位角、内错角、同旁内角',
        subject="数学",
        grade="七年级",
        volume="下册",
        version="浙教版",
        source_id="5star-math-zjjy-g7b-2026spring",
        source_file="第1章　1.2　同位角、内错角、同旁内角.pptx",
        status="source_index",
        summary="同位角、内错角、同旁内角的识别。",
    )

    assert note.safe_filename == "第1章 1.2 同位角、内错角、同旁内角.md"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m unittest tests.test_models -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'fish_study_wiki'`.

- [ ] **Step 3: Implement package skeleton**

Create `fish_study_wiki/__init__.py`:

```python
"""Local source-to-Obsidian wiki pipeline for fish-study."""
```

Create `fish_study_wiki/settings.py`:

```python
from pathlib import Path

REPO_ROOT = Path("/Users/kwang/fish-study")
VAULT_ROOT = Path("/Users/kwang/Downloads/obsidian/fish-study")
RAW_SOURCE_DIR = REPO_ROOT / "sources" / "raw"
INVENTORY_DIR = REPO_ROOT / "sources" / "inventory"
EXTRACTED_DIR = REPO_ROOT / "sources" / "extracted"
REPORT_DIR = REPO_ROOT / "reports"

GRADES = ["七年级", "八年级"]
VOLUMES = ["上册", "下册"]
SUBJECTS = ["语文", "数学", "英语", "科学", "地理", "中国历史", "道德与法治"]
STATUSES = ["available", "missing_source", "source_index", "extracted", "verified"]
```

Create `fish_study_wiki/models.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
import re


def safe_markdown_filename(title: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]', "-", title)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return f"{cleaned[:120] or '未命名'}.md"


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    subject: str
    grade: str
    volume: str
    version: str
    source_type: str
    status: str
    local_path: str
    sha256: str

    @property
    def key(self) -> str:
        return f"{self.grade}/{self.volume}/{self.subject}"

    @property
    def is_available(self) -> bool:
        return self.status == "available" and bool(self.local_path) and bool(self.sha256)


@dataclass(frozen=True)
class TopicNote:
    title: str
    subject: str
    grade: str
    volume: str
    version: str
    source_id: str
    source_file: str
    status: str
    summary: str

    @property
    def safe_filename(self) -> str:
        return safe_markdown_filename(self.title)
```

- [ ] **Step 4: Run model tests**

Run:

```bash
python3 -m unittest tests.test_models -v
```

Expected: PASS, 2 tests.

- [ ] **Step 5: Commit**

```bash
git add fish_study_wiki tests/test_models.py
git commit -m "Add wiki pipeline data models"
```

---

### Task 2: Add Canonical Subject Matrix and Source Ledger

**Files:**
- Create: `data/catalog/subject-matrix.json`
- Create: `data/sources/source-ledger.json`
- Create: `fish_study_wiki/source_ledger.py`
- Create: `tests/test_source_ledger.py`

- [ ] **Step 1: Write source ledger tests**

Write `tests/test_source_ledger.py`:

```python
import json
import tempfile
import unittest
from pathlib import Path

from fish_study_wiki.source_ledger import load_sources, missing_matrix_entries


class SourceLedgerTests(unittest.TestCase):
    def test_load_sources_returns_source_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source-ledger.json"
            path.write_text(json.dumps([
                {
                    "source_id": "demo",
                    "subject": "数学",
                    "grade": "七年级",
                    "volume": "下册",
                    "version": "浙教版",
                    "source_type": "courseware",
                    "status": "available",
                    "local_path": "/tmp/demo.zip",
                    "sha256": "abc"
                }
            ], ensure_ascii=False), encoding="utf-8")

            sources = load_sources(path)

        self.assertEqual(sources[0].key, "七年级/下册/数学")

    def test_missing_matrix_entries_reports_uncovered_subjects(self):
        matrix = [
            {"grade": "七年级", "volume": "下册", "subject": "数学"},
            {"grade": "七年级", "volume": "下册", "subject": "语文"},
        ]
        covered = {"七年级/下册/数学"}

        self.assertEqual(
            missing_matrix_entries(matrix, covered),
            ["七年级/下册/语文"],
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m unittest tests.test_source_ledger -v
```

Expected: FAIL with `ModuleNotFoundError` for `fish_study_wiki.source_ledger`.

- [ ] **Step 3: Add subject matrix**

Create `data/catalog/subject-matrix.json` with 28 entries:

```json
[
  {"grade": "七年级", "volume": "上册", "subject": "语文"},
  {"grade": "七年级", "volume": "上册", "subject": "数学"},
  {"grade": "七年级", "volume": "上册", "subject": "英语"},
  {"grade": "七年级", "volume": "上册", "subject": "科学"},
  {"grade": "七年级", "volume": "上册", "subject": "地理"},
  {"grade": "七年级", "volume": "上册", "subject": "中国历史"},
  {"grade": "七年级", "volume": "上册", "subject": "道德与法治"},
  {"grade": "七年级", "volume": "下册", "subject": "语文"},
  {"grade": "七年级", "volume": "下册", "subject": "数学"},
  {"grade": "七年级", "volume": "下册", "subject": "英语"},
  {"grade": "七年级", "volume": "下册", "subject": "科学"},
  {"grade": "七年级", "volume": "下册", "subject": "地理"},
  {"grade": "七年级", "volume": "下册", "subject": "中国历史"},
  {"grade": "七年级", "volume": "下册", "subject": "道德与法治"},
  {"grade": "八年级", "volume": "上册", "subject": "语文"},
  {"grade": "八年级", "volume": "上册", "subject": "数学"},
  {"grade": "八年级", "volume": "上册", "subject": "英语"},
  {"grade": "八年级", "volume": "上册", "subject": "科学"},
  {"grade": "八年级", "volume": "上册", "subject": "地理"},
  {"grade": "八年级", "volume": "上册", "subject": "中国历史"},
  {"grade": "八年级", "volume": "上册", "subject": "道德与法治"},
  {"grade": "八年级", "volume": "下册", "subject": "语文"},
  {"grade": "八年级", "volume": "下册", "subject": "数学"},
  {"grade": "八年级", "volume": "下册", "subject": "英语"},
  {"grade": "八年级", "volume": "下册", "subject": "科学"},
  {"grade": "八年级", "volume": "下册", "subject": "地理"},
  {"grade": "八年级", "volume": "下册", "subject": "中国历史"},
  {"grade": "八年级", "volume": "下册", "subject": "道德与法治"}
]
```

- [ ] **Step 4: Add source ledger**

Create `data/sources/source-ledger.json`:

```json
[
  {
    "source_id": "5star-math-zjjy-g7b-2026spring",
    "subject": "数学",
    "grade": "七年级",
    "volume": "下册",
    "version": "浙教版",
    "source_type": "courseware",
    "status": "available",
    "local_path": "/Users/kwang/fish-study/sources/raw/5star-math-zjjy-g7b-2026spring.zip",
    "sha256": "25cb0437ab0d8fa94eb661d402ffda3b06165545d50d591785705a4890d4e6ff"
  },
  {
    "source_id": "5star-science-zjjy-g7b-2026spring",
    "subject": "科学",
    "grade": "七年级",
    "volume": "下册",
    "version": "浙教版",
    "source_type": "courseware",
    "status": "available",
    "local_path": "/Users/kwang/fish-study/sources/raw/5star-science-zjjy-g7b-2026spring.zip",
    "sha256": "caddab3449d0ef6afe919c586946676f9e086c4bef5a432b4ecaa9aa55ec579a"
  },
  {
    "source_id": "5star-english-pep-g7b-2026spring",
    "subject": "英语",
    "grade": "七年级",
    "volume": "下册",
    "version": "人教版",
    "source_type": "courseware",
    "status": "available",
    "local_path": "/Users/kwang/fish-study/sources/raw/5star-english-pep-g7b-2026spring.zip",
    "sha256": "a9405cd7ac82a4794e8264c3d0d4454b17944fec50b959925c56952f2626f1d1"
  }
]
```

- [ ] **Step 5: Implement source ledger loader**

Create `fish_study_wiki/source_ledger.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from fish_study_wiki.models import SourceRecord


def load_sources(path: Path) -> list[SourceRecord]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [SourceRecord(**row) for row in data]


def missing_matrix_entries(matrix: list[dict[str, str]], covered: set[str]) -> list[str]:
    missing: list[str] = []
    for row in matrix:
        key = f"{row['grade']}/{row['volume']}/{row['subject']}"
        if key not in covered:
            missing.append(key)
    return missing
```

- [ ] **Step 6: Run tests**

Run:

```bash
python3 -m unittest tests.test_source_ledger -v
```

Expected: PASS, 2 tests.

- [ ] **Step 7: Commit**

```bash
git add data fish_study_wiki/source_ledger.py tests/test_source_ledger.py
git commit -m "Add subject matrix and source ledger"
```

---

### Task 3: Replace One-Off ZIP Inventory Script with Package Command

**Files:**
- Create: `fish_study_wiki/zip_inventory.py`
- Modify: `scripts/rebuild_zip_inventories.py`
- Test: `tests/test_zip_inventory.py`

- [ ] **Step 1: Write ZIP inventory tests**

Write `tests/test_zip_inventory.py`:

```python
import tempfile
import unittest
import zipfile
from pathlib import Path

from fish_study_wiki.zip_inventory import decode_zip_name, inventory_zip


class ZipInventoryTests(unittest.TestCase):
    def test_decode_gbk_zip_name(self):
        mojibake = "第1章 直线的相交.pptx".encode("gbk").decode("cp437")
        self.assertEqual(decode_zip_name(mojibake), "第1章 直线的相交.pptx")

    def test_inventory_zip_returns_decoded_file_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "demo.zip"
            raw_name = "第1章 直线的相交.pptx".encode("gbk").decode("cp437")
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr(raw_name, b"demo")

            rows = inventory_zip(path)

        self.assertEqual(rows[0]["name"], "第1章 直线的相交.pptx")
        self.assertEqual(rows[0]["size"], 4)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m unittest tests.test_zip_inventory -v
```

Expected: FAIL with missing `fish_study_wiki.zip_inventory`.

- [ ] **Step 3: Implement ZIP inventory module**

Create `fish_study_wiki/zip_inventory.py`:

```python
from __future__ import annotations

import hashlib
from pathlib import Path
import zipfile


def decode_zip_name(name: str) -> str:
    try:
        return name.encode("cp437").decode("gbk")
    except UnicodeError:
        return name


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory_zip(path: Path) -> list[dict[str, int | str]]:
    rows: list[dict[str, int | str]] = []
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            rows.append({"name": decode_zip_name(info.filename), "size": info.file_size})
    return rows


def write_inventory(zip_path: Path, inventory_dir: Path) -> None:
    source_id = zip_path.stem
    digest = sha256(zip_path)
    rows = inventory_zip(zip_path)
    inventory_dir.mkdir(parents=True, exist_ok=True)
    (inventory_dir / f"{source_id}.sha256").write_text(
        f"{digest}  {zip_path}\n", encoding="utf-8"
    )
    with (inventory_dir / f"{source_id}.files.md").open("w", encoding="utf-8") as out:
        out.write(f"# {source_id}\n\n")
        out.write(f"- SHA256: `{digest}`\n")
        out.write(f"- Files: {len(rows)}\n\n")
        out.write("| File | Size |\n|---|---:|\n")
        for row in rows:
            name = str(row["name"]).replace("|", "\\|")
            out.write(f"| {name} | {row['size']} |\n")
```

- [ ] **Step 4: Update wrapper script**

Replace `scripts/rebuild_zip_inventories.py` with:

```python
#!/usr/bin/env python3
from fish_study_wiki.cli import main


if __name__ == "__main__":
    main(["inventory"])
```

- [ ] **Step 5: Run tests**

Run:

```bash
python3 -m unittest tests.test_zip_inventory -v
```

Expected: PASS, 2 tests.

- [ ] **Step 6: Commit**

```bash
git add fish_study_wiki/zip_inventory.py scripts/rebuild_zip_inventories.py tests/test_zip_inventory.py
git commit -m "Add reusable ZIP inventory pipeline"
```

---

### Task 4: Extract PPTX Text Without External Dependencies

**Files:**
- Create: `fish_study_wiki/pptx_text.py`
- Create: `tests/fixtures/make_pptx_fixture.py`
- Create: `tests/test_pptx_text.py`

- [ ] **Step 1: Add PPTX fixture builder**

Create `tests/fixtures/make_pptx_fixture.py`:

```python
from __future__ import annotations

from pathlib import Path
import zipfile


def make_pptx(path: Path, texts: list[str]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types></Types>")
        for index, text in enumerate(texts, start=1):
            archive.writestr(
                f"ppt/slides/slide{index}.xml",
                f"""<?xml version="1.0" encoding="UTF-8"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:sp><p:txBody><a:p><a:r><a:t>{text}</a:t></a:r></a:p></p:txBody></p:sp>
    </p:spTree>
  </p:cSld>
</p:sld>""",
            )
```

- [ ] **Step 2: Write PPTX extraction tests**

Write `tests/test_pptx_text.py`:

```python
import tempfile
import unittest
from pathlib import Path

from fish_study_wiki.pptx_text import extract_pptx_text
from tests.fixtures.make_pptx_fixture import make_pptx


class PptxTextTests(unittest.TestCase):
    def test_extract_pptx_text_returns_slide_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "demo.pptx"
            make_pptx(path, ["直线的相交", "垂线与垂线段"])

            text = extract_pptx_text(path)

        self.assertIn("直线的相交", text)
        self.assertIn("垂线与垂线段", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
python3 -m unittest tests.test_pptx_text -v
```

Expected: FAIL with missing `fish_study_wiki.pptx_text`.

- [ ] **Step 4: Implement PPTX text extraction**

Create `fish_study_wiki/pptx_text.py`:

```python
from __future__ import annotations

from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile


TEXT_TAG = "{http://schemas.openxmlformats.org/drawingml/2006/main}t"


def slide_sort_key(name: str) -> int:
    match = re.search(r"slide(\d+)\.xml$", name)
    return int(match.group(1)) if match else 0


def extract_pptx_text(path: Path) -> str:
    chunks: list[str] = []
    with zipfile.ZipFile(path) as archive:
        slide_names = sorted(
            [name for name in archive.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml")],
            key=slide_sort_key,
        )
        for slide_name in slide_names:
            root = ET.fromstring(archive.read(slide_name))
            slide_text = [node.text.strip() for node in root.iter(TEXT_TAG) if node.text and node.text.strip()]
            if slide_text:
                chunks.append("\n".join(slide_text))
    return "\n\n".join(chunks)
```

- [ ] **Step 5: Run tests**

Run:

```bash
python3 -m unittest tests.test_pptx_text -v
```

Expected: PASS, 1 test.

- [ ] **Step 6: Commit**

```bash
git add fish_study_wiki/pptx_text.py tests/fixtures tests/test_pptx_text.py
git commit -m "Extract text from PPTX courseware"
```

---

### Task 5: Build Topic Notes from Sources

**Files:**
- Create: `fish_study_wiki/topic_builder.py`
- Create: `tests/test_topic_builder.py`

- [ ] **Step 1: Write topic builder tests**

Write `tests/test_topic_builder.py`:

```python
import unittest

from fish_study_wiki.models import SourceRecord
from fish_study_wiki.topic_builder import topic_from_source_file


class TopicBuilderTests(unittest.TestCase):
    def test_topic_from_source_file_uses_filename_title(self):
        source = SourceRecord(
            source_id="5star-science-zjjy-g7b-2026spring",
            subject="科学",
            grade="七年级",
            volume="下册",
            version="浙教版",
            source_type="courseware",
            status="available",
            local_path="/tmp/science.zip",
            sha256="abc",
        )

        note = topic_from_source_file(
            source,
            "第2章　第3节　第1课时　原子结构模型与原子的构成.pptx",
            "原子由原子核和核外电子构成。",
        )

        self.assertEqual(note.title, "第2章 第3节 第1课时 原子结构模型与原子的构成")
        self.assertEqual(note.status, "extracted")
        self.assertIn("原子由原子核", note.summary)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m unittest tests.test_topic_builder -v
```

Expected: FAIL with missing `fish_study_wiki.topic_builder`.

- [ ] **Step 3: Implement topic builder**

Create `fish_study_wiki/topic_builder.py`:

```python
from __future__ import annotations

from pathlib import Path
import re

from fish_study_wiki.models import SourceRecord, TopicNote


def clean_title(source_file: str) -> str:
    title = Path(source_file).stem
    title = title.replace("\u3000", " ")
    title = re.sub(r"\s+", " ", title).strip()
    return title


def summarize_text(text: str, max_chars: int = 180) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return "来源文件已建立索引；正文抽取未获得可用文本。"
    return cleaned[:max_chars]


def topic_from_source_file(source: SourceRecord, source_file: str, extracted_text: str) -> TopicNote:
    return TopicNote(
        title=clean_title(source_file),
        subject=source.subject,
        grade=source.grade,
        volume=source.volume,
        version=source.version,
        source_id=source.source_id,
        source_file=source_file,
        status="extracted" if extracted_text.strip() else "source_index",
        summary=summarize_text(extracted_text),
    )
```

- [ ] **Step 4: Run tests**

Run:

```bash
python3 -m unittest tests.test_topic_builder -v
```

Expected: PASS, 1 test.

- [ ] **Step 5: Commit**

```bash
git add fish_study_wiki/topic_builder.py tests/test_topic_builder.py
git commit -m "Build topic records from source files"
```

---

### Task 6: Render Deterministic Obsidian Notes

**Files:**
- Create: `fish_study_wiki/note_renderer.py`
- Create: `tests/test_note_renderer.py`

- [ ] **Step 1: Write note renderer tests**

Write `tests/test_note_renderer.py`:

```python
import unittest

from fish_study_wiki.models import TopicNote
from fish_study_wiki.note_renderer import render_topic_note


class NoteRendererTests(unittest.TestCase):
    def test_render_topic_note_contains_frontmatter_and_links(self):
        note = TopicNote(
            title="第1章 1.1 直线的相交",
            subject="数学",
            grade="七年级",
            volume="下册",
            version="浙教版",
            source_id="5star-math-zjjy-g7b-2026spring",
            source_file="第1章　1.1　直线的相交.pptx",
            status="extracted",
            summary="直线相交形成角，垂线是特殊的相交关系。",
        )

        markdown = render_topic_note(note)

        self.assertIn("type: knowledge", markdown)
        self.assertIn("# 第1章 1.1 直线的相交", markdown)
        self.assertIn("[[00-数学七年级下册索引]]", markdown)
        self.assertIn("直线相交形成角", markdown)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m unittest tests.test_note_renderer -v
```

Expected: FAIL with missing `fish_study_wiki.note_renderer`.

- [ ] **Step 3: Implement note renderer**

Create `fish_study_wiki/note_renderer.py`:

```python
from __future__ import annotations

from fish_study_wiki.models import TopicNote


def render_topic_note(note: TopicNote) -> str:
    index_name = f"00-{note.subject}{note.grade}{note.volume}索引"
    return f"""---
type: knowledge
subject: {note.subject}
grade: {note.grade}
volume: {note.volume}
version: {note.version}
source: {note.source_id}
source_file: {note.source_file}
status: {note.status}
---

# {note.title}

## 一句话

{note.summary}

## 必须掌握

- 能说出本知识点的定义、条件和使用场景。
- 能把题目中的关键词对应到本知识点。
- 能完成至少 2 道同类基础题。

## 常见题型

- 概念识别题
- 方法应用题
- 易错辨析题

## 易错点

- 未区分题目条件和结论。
- 跳过关键步骤直接写答案。
- 没有把单位、符号或关键词检查一遍。

## 错题记录

使用红黄蓝贴纸复盘后追加记录。

## 关联

- [[{index_name}]]
- [[教材版本索引]]
- [[错题归因规则]]
"""
```

- [ ] **Step 4: Run tests**

Run:

```bash
python3 -m unittest tests.test_note_renderer -v
```

Expected: PASS, 1 test.

- [ ] **Step 5: Commit**

```bash
git add fish_study_wiki/note_renderer.py tests/test_note_renderer.py
git commit -m "Render Obsidian knowledge notes"
```

---

### Task 7: Write Vault Indexes and Notes

**Files:**
- Create: `fish_study_wiki/vault_writer.py`
- Modify: `scripts/build_vault_indexes.py`
- Test: `tests/test_vault_writer.py`

- [ ] **Step 1: Write vault writer tests**

Write `tests/test_vault_writer.py`:

```python
import tempfile
import unittest
from pathlib import Path

from fish_study_wiki.models import TopicNote
from fish_study_wiki.vault_writer import write_subject_index, write_topic_note


class VaultWriterTests(unittest.TestCase):
    def test_write_topic_note_creates_subject_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            note = TopicNote(
                title="第1章 1.1 直线的相交",
                subject="数学",
                grade="七年级",
                volume="下册",
                version="浙教版",
                source_id="source",
                source_file="file.pptx",
                status="extracted",
                summary="summary",
            )

            path = write_topic_note(vault, note)

        self.assertTrue(path.name.endswith(".md"))
        self.assertIn("10-教材Wiki", str(path))

    def test_write_subject_index_contains_topic_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            path = write_subject_index(vault, "七年级", "下册", "数学", "浙教版", ["[[第1章 1.1 直线的相交]]"])
            text = path.read_text(encoding="utf-8")

        self.assertIn("# 数学七年级下册索引", text)
        self.assertIn("[[第1章 1.1 直线的相交]]", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m unittest tests.test_vault_writer -v
```

Expected: FAIL with missing `fish_study_wiki.vault_writer`.

- [ ] **Step 3: Implement vault writer**

Create `fish_study_wiki/vault_writer.py`:

```python
from __future__ import annotations

from pathlib import Path

from fish_study_wiki.models import TopicNote
from fish_study_wiki.note_renderer import render_topic_note


def subject_dir(vault: Path, grade: str, volume: str, subject: str) -> Path:
    return vault / "10-教材Wiki" / grade / volume / subject


def write_subject_index(vault: Path, grade: str, volume: str, subject: str, version: str, links: list[str]) -> Path:
    folder = subject_dir(vault, grade, volume, subject)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"00-{subject}{grade}{volume}索引.md"
    link_text = "\n".join(f"- {link}" for link in sorted(set(links)))
    path.write_text(
        f"""# {subject}{grade}{volume}索引

## 教材版本

{version}

## 知识点

{link_text if link_text else "- 本学科本册已建索引；源资料覆盖情况见 [[wiki-quality]]。"}

## 关联

- [[教材版本索引]]
- [[wiki-quality]]
""",
        encoding="utf-8",
    )
    return path


def write_topic_note(vault: Path, note: TopicNote) -> Path:
    folder = subject_dir(vault, note.grade, note.volume, note.subject)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / note.safe_filename
    path.write_text(render_topic_note(note), encoding="utf-8")
    return path
```

- [ ] **Step 4: Run tests**

Run:

```bash
python3 -m unittest tests.test_vault_writer -v
```

Expected: PASS, 2 tests.

- [ ] **Step 5: Update wrapper script**

Replace `scripts/build_vault_indexes.py` with:

```python
#!/usr/bin/env python3
from fish_study_wiki.cli import main


if __name__ == "__main__":
    main(["build"])
```

- [ ] **Step 6: Commit**

```bash
git add fish_study_wiki/vault_writer.py scripts/build_vault_indexes.py tests/test_vault_writer.py
git commit -m "Write Obsidian vault notes from topic records"
```

---

### Task 8: Add Quality Gates and Coverage Report

**Files:**
- Create: `fish_study_wiki/quality.py`
- Create: `tests/test_quality.py`
- Generated: `reports/wiki-quality.md`

- [ ] **Step 1: Write quality tests**

Write `tests/test_quality.py`:

```python
import unittest

from fish_study_wiki.quality import coverage_report


class QualityTests(unittest.TestCase):
    def test_coverage_report_marks_missing_sources(self):
        matrix = [
            {"grade": "七年级", "volume": "下册", "subject": "数学"},
            {"grade": "七年级", "volume": "下册", "subject": "语文"},
        ]
        covered = {"七年级/下册/数学": 12}

        report = coverage_report(matrix, covered)

        self.assertIn("| 七年级 | 下册 | 数学 | 12 | covered |", report)
        self.assertIn("| 七年级 | 下册 | 语文 | 0 | missing_source |", report)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m unittest tests.test_quality -v
```

Expected: FAIL with missing `fish_study_wiki.quality`.

- [ ] **Step 3: Implement quality report**

Create `fish_study_wiki/quality.py`:

```python
from __future__ import annotations


def coverage_report(matrix: list[dict[str, str]], covered_counts: dict[str, int]) -> str:
    lines = [
        "# wiki-quality",
        "",
        "| Grade | Volume | Subject | Notes | Status |",
        "|---|---|---|---:|---|",
    ]
    for row in matrix:
        key = f"{row['grade']}/{row['volume']}/{row['subject']}"
        count = covered_counts.get(key, 0)
        status = "covered" if count else "missing_source"
        lines.append(f"| {row['grade']} | {row['volume']} | {row['subject']} | {count} | {status} |")
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Run tests**

Run:

```bash
python3 -m unittest tests.test_quality -v
```

Expected: PASS, 1 test.

- [ ] **Step 5: Commit**

```bash
git add fish_study_wiki/quality.py tests/test_quality.py
git commit -m "Add wiki coverage quality gate"
```

---

### Task 9: Add CLI and End-to-End Build Command

**Files:**
- Create: `fish_study_wiki/cli.py`
- Modify: `scripts/download_sources.sh`
- Modify: `scripts/rebuild_zip_inventories.py`
- Modify: `scripts/build_vault_indexes.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write CLI smoke tests**

Write `tests/test_cli.py`:

```python
import unittest

from fish_study_wiki.cli import parser


class CliTests(unittest.TestCase):
    def test_parser_accepts_inventory_build_verify(self):
        self.assertEqual(parser().parse_args(["inventory"]).command, "inventory")
        self.assertEqual(parser().parse_args(["build"]).command, "build")
        self.assertEqual(parser().parse_args(["verify"]).command, "verify")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m unittest tests.test_cli -v
```

Expected: FAIL with missing `fish_study_wiki.cli`.

- [ ] **Step 3: Implement CLI**

Create `fish_study_wiki/cli.py`:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from fish_study_wiki.models import SourceRecord, TopicNote
from fish_study_wiki.settings import INVENTORY_DIR, RAW_SOURCE_DIR, REPORT_DIR, REPO_ROOT, VAULT_ROOT
from fish_study_wiki.source_ledger import load_sources
from fish_study_wiki.zip_inventory import inventory_zip, write_inventory
from fish_study_wiki.topic_builder import topic_from_source_file
from fish_study_wiki.vault_writer import write_subject_index, write_topic_note
from fish_study_wiki.quality import coverage_report


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="fish-study-wiki")
    p.add_argument("command", choices=["inventory", "build", "verify"])
    return p


def read_matrix() -> list[dict[str, str]]:
    path = REPO_ROOT / "data" / "catalog" / "subject-matrix.json"
    return json.loads(path.read_text(encoding="utf-8"))


def read_sources() -> list[SourceRecord]:
    return load_sources(REPO_ROOT / "data" / "sources" / "source-ledger.json")


def command_inventory() -> None:
    for zip_path in sorted(RAW_SOURCE_DIR.glob("*.zip")):
        write_inventory(zip_path, INVENTORY_DIR)


def command_build() -> None:
    sources = read_sources()
    by_key: dict[str, list[TopicNote]] = {}
    for source in sources:
        if not source.is_available:
            continue
        for row in inventory_zip(Path(source.local_path)):
            source_file = str(row["name"])
            note = topic_from_source_file(source, source_file, "")
            write_topic_note(VAULT_ROOT, note)
            by_key.setdefault(source.key, []).append(note)

    matrix = read_matrix()
    for row in matrix:
        key = f"{row['grade']}/{row['volume']}/{row['subject']}"
        notes = by_key.get(key, [])
        version = notes[0].version if notes else "missing_source"
        links = [f"[[{note.title}]]" for note in notes]
        write_subject_index(VAULT_ROOT, row["grade"], row["volume"], row["subject"], version, links)


def command_verify() -> None:
    matrix = read_matrix()
    counts: dict[str, int] = {}
    for row in matrix:
        folder = VAULT_ROOT / "10-教材Wiki" / row["grade"] / row["volume"] / row["subject"]
        count = len([p for p in folder.glob("*.md") if not p.name.startswith("00-")]) if folder.exists() else 0
        counts[f"{row['grade']}/{row['volume']}/{row['subject']}"] = count
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = coverage_report(matrix, counts)
    (REPORT_DIR / "wiki-quality.md").write_text(report, encoding="utf-8")
    (VAULT_ROOT / "00-入口" / "wiki-quality.md").write_text(report, encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    args = parser().parse_args(argv)
    if args.command == "inventory":
        command_inventory()
    elif args.command == "build":
        command_build()
    elif args.command == "verify":
        command_verify()
    else:
        raise SystemExit(f"unknown command: {args.command}")


if __name__ == "__main__":
    main(sys.argv[1:])
```

- [ ] **Step 4: Run CLI tests**

Run:

```bash
python3 -m unittest tests.test_cli -v
```

Expected: PASS, 1 test.

- [ ] **Step 5: Run full unit suite**

Run:

```bash
python3 -m unittest discover -s tests -v
```

Expected: PASS for all tests.

- [ ] **Step 6: Commit**

```bash
git add fish_study_wiki/cli.py scripts/download_sources.sh scripts/rebuild_zip_inventories.py scripts/build_vault_indexes.py tests/test_cli.py
git commit -m "Add wiki build CLI"
```

---

### Task 10: Run Full Wiki Build and Verify Outputs

**Files:**
- Generated: `reports/wiki-quality.md`
- Generated in vault: `/Users/kwang/Downloads/obsidian/fish-study/10-教材Wiki/**`
- Generated in vault: `/Users/kwang/Downloads/obsidian/fish-study/00-入口/wiki-quality.md`

- [ ] **Step 1: Rebuild source inventories**

Run:

```bash
python3 -m fish_study_wiki.cli inventory
```

Expected:

```text
```

No stdout is acceptable. Verify files exist:

```bash
find sources/inventory -maxdepth 1 -type f | sort
```

Expected includes:

```text
sources/inventory/5star-english-pep-g7b-2026spring.files.md
sources/inventory/5star-english-pep-g7b-2026spring.sha256
sources/inventory/5star-math-zjjy-g7b-2026spring.files.md
sources/inventory/5star-math-zjjy-g7b-2026spring.sha256
sources/inventory/5star-science-zjjy-g7b-2026spring.files.md
sources/inventory/5star-science-zjjy-g7b-2026spring.sha256
```

- [ ] **Step 2: Build vault notes**

Run:

```bash
python3 -m fish_study_wiki.cli build
```

Expected:

```text
```

No stdout is acceptable.

- [ ] **Step 3: Generate quality report**

Run:

```bash
python3 -m fish_study_wiki.cli verify
```

Expected:

```text
```

No stdout is acceptable.

- [ ] **Step 4: Verify vault note count**

Run:

```bash
find /Users/kwang/Downloads/obsidian/fish-study -name '*.md' | wc -l
```

Expected: at least `281`.

- [ ] **Step 5: Verify quality report has all 28 rows**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
report = Path('/Users/kwang/fish-study/reports/wiki-quality.md').read_text(encoding='utf-8')
rows = [line for line in report.splitlines() if line.startswith('| ') and not line.startswith('|---') and 'Grade' not in line]
print(len(rows))
PY
```

Expected:

```text
28
```

- [ ] **Step 6: Verify current available coverage**

Run:

```bash
rg 'covered|missing_source' reports/wiki-quality.md
```

Expected: `七年级/下册` rows for `数学`, `科学`, and `英语` are covered; other rows are `missing_source` until local source materials are added.

- [ ] **Step 7: Commit generated metadata and report**

```bash
git add data reports sources/inventory
git commit -m "Build initial complete wiki coverage report"
```

- [ ] **Step 8: Push**

```bash
git push
```

Expected: `main -> main`.

---

### Task 11: Add Incremental Source Intake Procedure

**Files:**
- Create: `docs/source-intake.md`
- Modify: `README.md`

- [ ] **Step 1: Create source intake document**

Create `docs/source-intake.md`:

```markdown
# Source Intake

## Purpose

Use this procedure whenever new textbook PDFs, courseware ZIPs, workbook scans, or official catalog files are added for Grade 7 or Grade 8.

## Local-Only Rule

Place raw files under `sources/raw/`. Do not commit raw files. Commit only checksums, inventories, source ledger updates, extracted summaries, and quality reports.

## Add A Source

1. Copy the file to `sources/raw/`.
2. Add one record to `data/sources/source-ledger.json`.
3. Run `python3 -m fish_study_wiki.cli inventory`.
4. Run `python3 -m fish_study_wiki.cli build`.
5. Run `python3 -m fish_study_wiki.cli verify`.
6. Read `reports/wiki-quality.md`.
7. Commit metadata and reports.

## Required Source Ledger Fields

- `source_id`
- `subject`
- `grade`
- `volume`
- `version`
- `source_type`
- `status`
- `local_path`
- `sha256`

## Status Meanings

- `available`: local source exists and checksum is recorded.
- `missing_source`: subject-volume exists in the curriculum matrix but no local source has been added.
- `source_index`: note exists from a filename or catalog title.
- `extracted`: note includes text extracted from local source material.
- `verified`: parent reviewed the note against the child's actual textbook or teacher assignment.
```

- [ ] **Step 2: Update README commands**

Modify `README.md` initialization section to include:

```markdown
## Rebuild Wiki

```bash
python3 -m fish_study_wiki.cli inventory
python3 -m fish_study_wiki.cli build
python3 -m fish_study_wiki.cli verify
```

Quality report:

- `reports/wiki-quality.md`
- `/Users/kwang/Downloads/obsidian/fish-study/00-入口/wiki-quality.md`
```
```

- [ ] **Step 3: Commit docs**

```bash
git add README.md docs/source-intake.md
git commit -m "Document source intake workflow"
```

---

## Self-Review

Spec coverage:

- Complete Grade 7 and Grade 8 matrix is covered by `data/catalog/subject-matrix.json` and `quality.py`.
- Existing downloaded math/science/English ZIPs are covered by `data/sources/source-ledger.json`, `zip_inventory.py`, and `topic_builder.py`.
- Obsidian wiki writing is covered by `note_renderer.py` and `vault_writer.py`.
- Missing source transparency is covered by `reports/wiki-quality.md`.
- Local-only copyright boundary is preserved by `.gitignore`, `source-intake.md`, and the ledger/checksum workflow.

Placeholder scan:

- No task depends on unnamed files.
- No task says “add appropriate handling” without exact code.
- Missing materials are represented as `missing_source`, an explicit data state, not a hidden blank.

Type consistency:

- `SourceRecord.key`, `SourceRecord.is_available`, `TopicNote.safe_filename`, and CLI command names are used consistently across tests and implementation steps.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-19-complete-obsidian-wiki.md`. Two execution options:

1. **Subagent-Driven (recommended)** - dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** - execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?

