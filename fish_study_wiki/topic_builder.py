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


def topic_from_source_file(
    source: SourceRecord, source_file: str, extracted_text: str
) -> TopicNote:
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
