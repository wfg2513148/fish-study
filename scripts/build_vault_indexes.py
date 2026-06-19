#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fish_study_wiki.cli import main as cli_main
from fish_study_wiki.quality import validate_available_source


def main() -> None:
    raise SystemExit(cli_main(["build"]))


if __name__ == "__main__":
    main()
