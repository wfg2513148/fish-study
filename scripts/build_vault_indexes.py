#!/usr/bin/env python3
from __future__ import annotations

import io
import sys
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fish_study_wiki import settings
from fish_study_wiki.models import SourceRecord
from fish_study_wiki.pptx_text import extract_pptx_text
from fish_study_wiki.source_ledger import load_sources
from fish_study_wiki.topic_builder import topic_from_source_file
from fish_study_wiki.vault_writer import topic_link, write_subject_index, write_topic_note
from fish_study_wiki.zip_inventory import decode_zip_name, sha256


def validate_available_source(source: SourceRecord) -> Path:
    if source.status != "available":
        raise ValueError(f"source {source.source_id} is not marked available")
    if not source.local_path:
        raise ValueError(f"available source {source.source_id} has no local_path")
    if not source.sha256:
        raise ValueError(f"available source {source.source_id} has no sha256")

    zip_path = Path(source.local_path)
    if not zip_path.exists():
        raise FileNotFoundError(
            f"available source {source.source_id} file not found: {zip_path}"
        )

    actual = sha256(zip_path)
    if actual != source.sha256:
        raise ValueError(
            f"available source {source.source_id} sha256 mismatch: "
            f"expected {source.sha256}, got {actual}"
        )
    return zip_path


def available_sources_with_paths() -> list[tuple[SourceRecord, Path]]:
    ledger_path = ROOT / "data" / "sources" / "source-ledger.json"
    sources = [
        source for source in load_sources(ledger_path) if source.status == "available"
    ]
    return [(source, validate_available_source(source)) for source in sources]


def source_topics() -> dict[tuple[str, str, str], tuple[str, list[str]]]:
    grouped: dict[tuple[str, str, str], tuple[str, list[str]]] = {}
    for source, zip_path in available_sources_with_paths():
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
