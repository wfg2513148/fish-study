from __future__ import annotations

from pathlib import Path
from typing import BinaryIO
import re
import xml.etree.ElementTree as ET
import zipfile


TEXT_TAG = "{http://schemas.openxmlformats.org/drawingml/2006/main}t"
SLIDE_RE = re.compile(r"^ppt/slides/slide(\d+)\.xml$")


def slide_sort_key(name: str) -> int:
    match = SLIDE_RE.match(name)
    return int(match.group(1)) if match else 0


def extract_pptx_text(path: str | Path | BinaryIO) -> str:
    chunks: list[str] = []
    with zipfile.ZipFile(path) as archive:
        slide_names = sorted(
            [name for name in archive.namelist() if SLIDE_RE.match(name)],
            key=slide_sort_key,
        )
        for slide_name in slide_names:
            root = ET.fromstring(archive.read(slide_name))
            slide_text = [
                node.text.strip()
                for node in root.iter(TEXT_TAG)
                if node.text and node.text.strip()
            ]
            if slide_text:
                chunks.append("\n".join(slide_text))
    return "\n\n".join(chunks)
