#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VAULT="${FISH_STUDY_VAULT_ROOT:-$HOME/Downloads/obsidian/fish-study}"
PROJECT_SKILLS_DIR="$ROOT/.codex/skills"
GPT_IMAGE_SKILL="$HOME/.codex/skills/gpt-image-2/SKILL.md"

ok() {
  printf 'OK: %s\n' "$1"
}

warn() {
  printf 'WARN: %s\n' "$1" >&2
}

need_command() {
  local name="$1"
  local hint="$2"
  if command -v "$name" >/dev/null 2>&1; then
    ok "$name found: $(command -v "$name")"
  else
    warn "$name missing. $hint"
  fi
}

mkdir -p \
  "$ROOT/sources/raw" \
  "$ROOT/sources/extracted" \
  "$ROOT/outputs" \
  "$VAULT" \
  "$HOME/.codex/skills"

if compgen -G "$PROJECT_SKILLS_DIR/*/SKILL.md" >/dev/null; then
  for skill_src in "$PROJECT_SKILLS_DIR"/*/SKILL.md; do
    skill_name="$(basename "$(dirname "$skill_src")")"
    skill_dir="$HOME/.codex/skills/$skill_name"
    mkdir -p "$skill_dir"
    cp "$skill_src" "$skill_dir/SKILL.md"
    ok "installed $skill_name skill to $skill_dir/SKILL.md"
  done
else
  warn "no project skills found under $PROJECT_SKILLS_DIR"
fi

if [[ -f "$GPT_IMAGE_SKILL" ]]; then
  ok "gpt-image-2 skill found: $GPT_IMAGE_SKILL"
else
  warn "gpt-image-2 skill missing. Sync it to $GPT_IMAGE_SKILL and restart Codex before generating illustrated exam papers."
fi

need_command "python3" "Install Python 3.11+."
need_command "node" "Install Node.js 20+."
need_command "npm" "Install npm with Node.js."
need_command "codex" "Install and log in to Codex CLI/Desktop."
need_command "git" "Install Git."
need_command "curl" "Install curl."
need_command "shasum" "Install Perl Digest tools or use sha256sum and adjust docs."

if [[ "$(uname -s)" == "Darwin" ]]; then
  need_command "sips" "macOS normally includes sips."
  need_command "qlmanage" "macOS normally includes qlmanage."
else
  warn "not macOS; replace sips/qlmanage PDF preview checks with equivalent Linux tools."
fi

if command -v python3 >/dev/null 2>&1; then
  python3 - <<'PY'
import importlib.util

for module, install in [
    ("pypdf", "python3 -m pip install --user pypdf"),
    ("pytest", "python3 -m pip install --user pytest"),
]:
    if importlib.util.find_spec(module):
        print(f"OK: Python module {module} found")
    else:
        print(f"WARN: Python module {module} missing. Install with: {install}")
PY
else
  warn "skip Python module checks because python3 is missing."
fi

if command -v node >/dev/null 2>&1; then
  node - <<'NODE' 2>/dev/null || warn "node check failed; install Node.js before PDF/visual workflows."
try {
  require.resolve("playwright");
  console.log("OK: Node module playwright found");
} catch (error) {
  console.error("WARN: Node module playwright missing. If the repo is under $HOME, run: npm install --prefix \"$HOME\" playwright. Otherwise install Playwright where this repo's node process can resolve it.");
}
NODE
else
  warn "skip Node module checks because node is missing."
fi

printf '\nNext checks:\n'
printf '  cd %s\n' "$ROOT"
printf '  python3 -m pytest -q\n'
printf '  python3 -m fish_study_wiki.cli study-context\n'
printf '  scripts/init_vault.sh\n'
printf '  scripts/download_sources.sh\n'
