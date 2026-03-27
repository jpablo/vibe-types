#!/usr/bin/env bash
# Detect project language and inject the matching vibe-types quick index.
# Runs as a SessionStart hook — outputs JSON with additionalContext.
# Snippets live in skills/<lang>/quick-index.md alongside each SKILL.md.

set -euo pipefail

SKILLS_DIR="${CLAUDE_PLUGIN_ROOT}/skills"

langs=()

# Detect languages from files in the working directory
if compgen -G "*.py" >/dev/null 2>&1 || [ -f pyproject.toml ] || [ -f setup.py ]; then
  langs+=(python)
fi
if [ -f Cargo.toml ] || compgen -G "*.rs" >/dev/null 2>&1; then
  langs+=(rust)
fi
if [ -f lakefile.lean ] || compgen -G "*.lean" >/dev/null 2>&1; then
  langs+=(lean)
fi
if [ -f build.sbt ] || [ -f build.sc ] || [ -f project.scala ] || compgen -G "*.scala" >/dev/null 2>&1; then
  langs+=(scala3)
fi

# If no language detected, exit silently (no context to inject)
if [ ${#langs[@]} -eq 0 ]; then
  exit 0
fi

# Concatenate quick-index files for detected languages
context=""
sep=""
for lang in "${langs[@]}"; do
  file="${SKILLS_DIR}/${lang}/quick-index.md"
  if [ -f "$file" ]; then
    context+="${sep}$(cat "$file")"
    sep=$'\n\n'
  fi
done

# Build JSON using python for reliable escaping
python3 -c "
import json, sys
ctx = sys.stdin.read()
ctx += '\n\nWhen a topic ID is referenced (e.g. T13-null-safety), read the full guide from the vibe-types plugin skill catalog for detailed patterns and examples.'
print(json.dumps({
  'hookSpecificOutput': {
    'hookEventName': 'SessionStart',
    'additionalContext': ctx
  }
}, indent=2))
" <<< "$context"

exit 0
