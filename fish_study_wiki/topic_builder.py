from __future__ import annotations

from datetime import date
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
    source: SourceRecord,
    source_file: str,
    extracted_text: str,
    confirmed_on: str | None = None,
) -> TopicNote:
    has_text = bool(extracted_text.strip())
    return TopicNote(
        title=clean_title(source_file),
        subject=source.subject,
        grade=source.grade,
        volume=source.volume,
        version=source.version,
        source_id=source.source_id,
        source_file=source_file,
        status="extracted" if has_text else "source_index",
        summary=summarize_text(extracted_text),
        confidence="high" if has_text else "medium",
        last_confirmed=confirmed_on or date.today().isoformat(),
    )
