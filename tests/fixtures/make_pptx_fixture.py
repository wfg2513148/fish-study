from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape
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
      <p:sp><p:txBody><a:p><a:r><a:t>{escape(text)}</a:t></a:r></a:p></p:txBody></p:sp>
    </p:spTree>
  </p:cSld>
</p:sld>""",
            )
