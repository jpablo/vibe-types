#!/usr/bin/env bash
# Verify every code snippet in a skill's catalog + usecases markdown docs by
# running verify_markdown.py over each file and aggregating pass/fail.
#
# Usage: verify_docs.sh <skill-dir> <report-project> [extra verify_markdown args...]
#   <skill-dir>       skill name under plugin/skills/ (python, rust, scala3, typescript)
#   <report-project>  project name under projects/ where reports are written
#   extra args        forwarded to verify_markdown.py (e.g. --match-errors)
#
# Exit status: 0 if every file is clean, 1 if any file had failures or tool errors.
set -uo pipefail

skill="${1:?usage: verify_docs.sh <skill-dir> <report-project> [extra args...]}"
proj="${2:?usage: verify_docs.sh <skill-dir> <report-project> [extra args...]}"
shift 2

cd "$(git rev-parse --show-toplevel)"
verify="plugin/skills/verify-markdown-snippets/scripts/verify_markdown.py"
out="projects/$proj/reports/latest"
rm -rf "$out"

fail=0 n=0 bad=0 tool=0
for kind in catalog usecases; do
  for f in "plugin/skills/$skill/$kind"/*.md; do
    [ -e "$f" ] || continue
    n=$((n + 1))
    if python3 "$verify" "$f" --out "$out/$kind" "$@" >/dev/null; then
      echo "  ok    $f"
    else
      rc=$?
      if [ "$rc" -eq 2 ]; then
        echo "  TOOL  $f"
        tool=$((tool + 1))
      else
        echo "  FAIL  $f"
        bad=$((bad + 1))
      fi
      fail=1
    fi
  done
done

echo "checked $n files: $bad with failures, $tool tool-errors; reports in $out"
exit $fail
