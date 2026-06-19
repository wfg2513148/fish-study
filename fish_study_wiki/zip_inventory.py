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


def write_inventory(zip_path: Path, inventory_dir: Path) -> dict[str, int | str]:
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

    return {
        "source_id": source_id,
        "zip_path": str(zip_path),
        "sha256": digest,
        "file_count": len(rows),
        "file_list": f"sources/inventory/{source_id}.files.md",
    }


def rebuild_inventories(raw_dir: Path, inventory_dir: Path) -> list[dict[str, int | str]]:
    summaries = []
    for zip_path in sorted(raw_dir.glob("*.zip")):
        summaries.append(write_inventory(zip_path, inventory_dir))
    write_downloaded_sources(summaries, inventory_dir)
    return summaries


def write_downloaded_sources(
    summaries: list[dict[str, int | str]], inventory_dir: Path
) -> None:
    lines = ["# Downloaded Source Inventory", ""]
    for summary in summaries:
        source_id = summary["source_id"]
        lines.append(f"## {source_id}")
        lines.append("")
        lines.append(f"- ZIP: `{summary['zip_path']}`")
        lines.append(f"- SHA256: `{summary['sha256']}`")
        lines.append(f"- File count: {summary['file_count']}")
        lines.append(f"- File list: `{summary['file_list']}`")
        lines.append("")

    (inventory_dir / "downloaded-sources.md").write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8"
    )
