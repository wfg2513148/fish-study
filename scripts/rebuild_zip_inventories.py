#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "sources" / "raw"
INV_DIR = ROOT / "sources" / "inventory"


def decode_name(name: str) -> str:
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


def main() -> None:
    INV_DIR.mkdir(parents=True, exist_ok=True)
    summary_lines = ["# Downloaded Source Inventory", ""]

    for zip_path in sorted(RAW_DIR.glob("*.zip")):
        source_id = zip_path.stem
        digest = sha256(zip_path)
        (INV_DIR / f"{source_id}.sha256").write_text(
            f"{digest}  {zip_path}\n", encoding="utf-8"
        )

        files_path = INV_DIR / f"{source_id}.files.md"
        with zipfile.ZipFile(zip_path) as archive:
            rows = []
            for info in archive.infolist():
                if info.is_dir():
                    continue
                rows.append((decode_name(info.filename), info.file_size))

        with files_path.open("w", encoding="utf-8") as out:
            out.write(f"# {source_id}\n\n")
            out.write(f"- SHA256: `{digest}`\n")
            out.write(f"- Files: {len(rows)}\n\n")
            out.write("| File | Size |\n|---|---:|\n")
            for name, size in rows:
                out.write(f"| {name.replace('|', '\\|')} | {size} |\n")

        summary_lines.append(f"## {source_id}")
        summary_lines.append("")
        summary_lines.append(f"- ZIP: `{zip_path}`")
        summary_lines.append(f"- SHA256: `{digest}`")
        summary_lines.append(f"- File count: {len(rows)}")
        summary_lines.append(f"- File list: `sources/inventory/{source_id}.files.md`")
        summary_lines.append("")

    (INV_DIR / "downloaded-sources.md").write_text(
        "\n".join(summary_lines).rstrip() + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()

