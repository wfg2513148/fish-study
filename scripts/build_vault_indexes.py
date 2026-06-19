#!/usr/bin/env python3
from __future__ import annotations

import io
import sys
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fish_study_wiki import settings
from fish_study_wiki.pptx_text import extract_pptx_text
from fish_study_wiki.source_ledger import load_sources
from fish_study_wiki.topic_builder import topic_from_source_file
from fish_study_wiki.vault_writer import topic_link, write_subject_index, write_topic_note
from fish_study_wiki.zip_inventory import decode_zip_name


def source_topics() -> dict[tuple[str, str, str], tuple[str, list[str]]]:
    grouped: dict[tuple[str, str, str], tuple[str, list[str]]] = {}
    ledger_path = ROOT / "data" / "sources" / "source-ledger.json"
    for source in load_sources(ledger_path):
        if not source.is_available:
            continue
        zip_path = Path(source.local_path)
        if not zip_path.exists():
            continue

        key = (source.grade, source.volume, source.subject)
        version, links = grouped.setdefault(key, (source.version, []))
        with zipfile.ZipFile(zip_path) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                source_file = decode_zip_name(info.filename)
                if not source_file.lower().endswith(".pptx"):
                    continue
                extracted_text = extract_pptx_text(io.BytesIO(archive.read(info)))
                note = topic_from_source_file(source, source_file, extracted_text)
                write_topic_note(settings.VAULT_ROOT, note)
                links.append(topic_link(note))
        grouped[key] = (version, links)
    return grouped


def make_subject_indexes(grouped: dict[tuple[str, str, str], tuple[str, list[str]]]) -> None:
    for grade in settings.GRADES:
        for volume in settings.VOLUMES:
            for subject in settings.SUBJECTS:
                version, links = grouped.get((grade, volume, subject), ("待确认或待补齐。", []))
                write_subject_index(settings.VAULT_ROOT, grade, volume, subject, version, links)


def main() -> None:
    grouped = source_topics()
    make_subject_indexes(grouped)
    print(f"Built vault indexes under {settings.VAULT_ROOT}")


if __name__ == "__main__":
    main()
