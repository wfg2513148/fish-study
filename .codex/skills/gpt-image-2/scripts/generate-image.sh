#!/usr/bin/env bash
# Generate an image via Hermes openai-codex gpt-image-2 OAuth provider.
# Usage: ./generate-image.sh "prompt" [output_path] [size]

set -euo pipefail

PROMPT="${1:?Usage: $0 \"prompt\" [output_path] [size]}"
OUTPUT="${2:-/tmp/generated-image-$(date +%s).png}"
SIZE="${3:-1536x1024}"
HERMES_PYTHON="${HERMES_PYTHON:-$HOME/.hermes/hermes-agent/venv/bin/python}"

if [[ ! -x "$HERMES_PYTHON" ]]; then
  echo "ERROR: Hermes Python not found at $HERMES_PYTHON" >&2
  exit 1
fi

case "$SIZE" in
  1536x1024) ASPECT_RATIO="landscape" ;;
  1024x1024) ASPECT_RATIO="square" ;;
  1024x1536) ASPECT_RATIO="portrait" ;;
  *)
    echo "ERROR: unsupported size '$SIZE'. Use 1536x1024, 1024x1024, or 1024x1536." >&2
    exit 1
    ;;
esac

echo "Generating image with gpt-image-2 via Hermes openai-codex"
echo "Size: $SIZE | Output: $OUTPUT"

"$HERMES_PYTHON" - "$PROMPT" "$OUTPUT" "$ASPECT_RATIO" <<'PY'
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

prompt, output, aspect_ratio = sys.argv[1], sys.argv[2], sys.argv[3]
plugin_path = Path.home() / ".hermes/hermes-agent/plugins/image_gen/openai-codex/__init__.py"

spec = importlib.util.spec_from_file_location("hermes_openai_codex_image", plugin_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

provider = module.OpenAICodexImageGenProvider()
if not provider.is_available():
    print(
        "ERROR: Hermes openai-codex image provider is unavailable. "
        "Run `hermes auth codex` and verify Hermes dependencies.",
        file=sys.stderr,
    )
    sys.exit(1)

result = provider.generate(prompt, aspect_ratio=aspect_ratio)
if not result.get("success"):
    print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr)
    sys.exit(1)

source = Path(result["image"])
target = Path(output).expanduser()
target.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(source, target)
print(f"SAVED: {target} ({os.path.getsize(target):,} bytes)")
PY
