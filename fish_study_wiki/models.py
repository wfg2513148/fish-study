from __future__ import annotations

from dataclasses import dataclass
import re


DEFAULT_LIFECYCLE_STATUS = "active"


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
    confidence: str = "medium"
    last_confirmed: str = ""
    lifecycle_status: str = DEFAULT_LIFECYCLE_STATUS
    supersedes: tuple[str, ...] = ()
    reinforced_by: tuple[str, ...] = ()

    @property
    def safe_filename(self) -> str:
        return safe_markdown_filename(self.title)

    @property
    def graph_id(self) -> str:
        return f"topic:{self.grade}:{self.volume}:{self.subject}:{self.title}"
