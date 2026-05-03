#!/usr/bin/env bash
# generate-rules.sh — Drive opencode to generate ESLint rules from vibe-types knowledge files.
#
# For each knowledge file in the TypeScript catalog, this script:
#   1. Runs an analysis pass (opencode reads the knowledge file and writes a JSON manifest
#      listing every detectable antipattern and its ESLint rule spec).
#   2. For each syntactic/type-aware rule in the manifest, runs a generation pass
#      (opencode writes the rule file, test file, and patches src/index.ts).
#
# Progress is tracked in a text file so interrupted runs resume where they left off.
#
# Usage: ./generate-rules.sh [--only T01,T02,...] [--dry-run] [--progress <file>] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$SCRIPT_DIR/plugin/skills/typescript"
PLUGIN_DIR="$SCRIPT_DIR/eslint-plugin"
WORK_DIR="$SCRIPT_DIR/.vibe-eslint-work"

# ── Output helpers ─────────────────────────────────────────────────────────────
log()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
info() { printf '    \033[0;37m%s\033[0m\n' "$*"; }
warn() { printf '\033[1;33mWARN: %s\033[0m\n' "$*" >&2; }
err()  { printf '\033[1;31mERR:  %s\033[0m\n' "$*" >&2; }

# ── Defaults ───────────────────────────────────────────────────────────────────
OPT_ONLY=""
OPT_DRY_RUN=false
OPT_PROGRESS=""

usage() {
  cat <<'EOF'
Usage: generate-rules.sh [OPTIONS]

Generate ESLint rules for the vibe-types TypeScript plugin by running opencode
against each knowledge file in plugin/skills/typescript/catalog/ and usecases/.

Options:
  --only T01,T02,...   Process only the listed knowledge file IDs (comma-separated)
  --dry-run            Print the plan without calling opencode or modifying files
  --progress <file>    Progress file path (default: .vibe-eslint-progress)
  --help               Show this help

Examples:
  ./generate-rules.sh --only T01 --dry-run
  ./generate-rules.sh --only T01,T13,T34
  ./generate-rules.sh
EOF
}

# ── Argument parsing ───────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --only)       OPT_ONLY="$2";      shift 2 ;;
    --dry-run)    OPT_DRY_RUN=true;   shift ;;
    --progress)   OPT_PROGRESS="$2";  shift 2 ;;
    --help|-h)    usage; exit 0 ;;
    *) err "Unknown option: $1"; printf '\n' >&2; usage >&2; exit 1 ;;
  esac
done

# ── Validation ─────────────────────────────────────────────────────────────────
if [[ ! -d "$SKILL_DIR" ]]; then
  err "TypeScript skill directory not found: $SKILL_DIR"
  exit 1
fi
if [[ ! -d "$PLUGIN_DIR" ]]; then
  err "Plugin directory not found: $PLUGIN_DIR"
  err "Run this script from the vibe-types repository root."
  exit 1
fi
if ! command -v python3 &>/dev/null; then
  err "python3 is required for JSON manifest parsing."
  exit 1
fi
if ! $OPT_DRY_RUN && ! command -v opencode &>/dev/null; then
  err "opencode is required. Install it or use --dry-run."
  exit 1
fi

PROGRESS_FILE="$(realpath "${OPT_PROGRESS:-.vibe-eslint-progress}")"
if ! $OPT_DRY_RUN; then
  mkdir -p "$WORK_DIR"
  touch "$PROGRESS_FILE"
fi

# ── Progress helpers ───────────────────────────────────────────────────────────
is_analyzed()  { [[ -f "$PROGRESS_FILE" ]] && grep -qxF "analyzed $1"       "$PROGRESS_FILE"; }
is_generated() { [[ -f "$PROGRESS_FILE" ]] && grep -qxF "generated $1 $2"   "$PROGRESS_FILE"; }
is_skipped()   { [[ -f "$PROGRESS_FILE" ]] && grep -qxF "skipped $1 $2"     "$PROGRESS_FILE"; }

mark_analyzed()  { printf 'analyzed %s\n'     "$1"     >> "$PROGRESS_FILE"; }
mark_generated() { printf 'generated %s %s\n' "$1" "$2" >> "$PROGRESS_FILE"; }
mark_skipped()   { printf 'skipped %s %s\n'   "$1" "$2" >> "$PROGRESS_FILE"; }

# ── Knowledge file helpers ─────────────────────────────────────────────────────
knowledge_id() { basename "$1" .md | cut -d- -f1; }

matches_only_filter() {
  local kid="$1"
  [[ -z "$OPT_ONLY" ]] && return 0
  local id
  IFS=',' read -ra ids <<< "$OPT_ONLY"
  for id in "${ids[@]}"; do
    [[ "$kid" == "$id" ]] && return 0
  done
  return 1
}

# ── Manifest helpers ───────────────────────────────────────────────────────────

# Print tab-separated rule_name<TAB>detectability lines from manifest JSON
manifest_entries() {
  local manifest="$1"
  python3 - <<PYEOF
import json, sys
with open("$manifest") as f:
    try:
        entries = json.load(f)
    except json.JSONDecodeError as e:
        print(f"JSON parse error in $manifest: {e}", file=sys.stderr)
        sys.exit(1)
if not isinstance(entries, list):
    print("Manifest must be a JSON array", file=sys.stderr)
    sys.exit(1)
for e in entries:
    name = e.get("rule_name", "")
    det  = e.get("detectability", "")
    if name and det:
        print(f"{name}\t{det}")
PYEOF
}

# Extract a single rule entry as pretty-printed JSON
manifest_entry_json() {
  local manifest="$1" rule_name="$2"
  python3 - <<PYEOF
import json, sys
with open("$manifest") as f:
    entries = json.load(f)
for e in entries:
    if e.get("rule_name") == "$rule_name":
        print(json.dumps(e, indent=2))
        sys.exit(0)
print(f"Rule '$rule_name' not found in manifest", file=sys.stderr)
sys.exit(1)
PYEOF
}

# ── Collect knowledge files ────────────────────────────────────────────────────
log "Collecting knowledge files from: $SKILL_DIR"

mapfile -t knowledge_files < <(
  {
    find "$SKILL_DIR/catalog"  -maxdepth 1 -name '*.md' -print0 2>/dev/null
    find "$SKILL_DIR/usecases" -maxdepth 1 -name '*.md' -print0 2>/dev/null
  } | sort -z | xargs -0 realpath
)

if (( ${#knowledge_files[@]} == 0 )); then
  err "No knowledge files found in $SKILL_DIR/{catalog,usecases}"
  exit 1
fi

# Apply --only filter
filtered_files=()
for kf in "${knowledge_files[@]}"; do
  kid="$(knowledge_id "$kf")"
  [[ "$kid" == "00" ]] && continue
  matches_only_filter "$kid" && filtered_files+=("$kf")
done

if (( ${#filtered_files[@]} == 0 )); then
  err "No knowledge files match the --only filter: $OPT_ONLY"
  exit 1
fi

info "Found ${#filtered_files[@]} knowledge file(s) to process."

# Dry-run: just print the list
if $OPT_DRY_RUN; then
  log "DRY RUN — no changes will be made"
  for kf in "${filtered_files[@]}"; do
    printf '  %s\n' "$(basename "$kf")"
  done
  printf '\n'
  return 0 2>/dev/null || exit 0
fi

# ── Main loop ──────────────────────────────────────────────────────────────────
stat_analyzed=0
stat_already_analyzed=0
stat_generated=0
stat_already_generated=0
stat_skipped=0
stat_failures=0

analyze_prompt_template="$(cat "$PLUGIN_DIR/prompts/analyze-knowledge-file.md")"
generate_prompt_template="$(cat "$PLUGIN_DIR/prompts/generate-rule.md")"

for kfile in "${filtered_files[@]}"; do
  kid="$(knowledge_id "$kfile")"
  slug="$(basename "$kfile" .md)"
  manifest="$WORK_DIR/${slug}.json"

  log "[$kid] $(basename "$kfile")"

  # ── ANALYSIS STEP ──────────────────────────────────────────────────────────
  if is_analyzed "$kfile"; then
    info "  [skip] analysis already done → $manifest"
    (( stat_already_analyzed++ )) || true
  else
    info "  Analyzing..."
    analysis_prompt="${analyze_prompt_template}

--- KNOWLEDGE FILE: $(basename "$kfile") ---
$(cat "$kfile")
--- END KNOWLEDGE FILE ---

Write the manifest JSON array to this exact file path: ${manifest}"

    oc_exit=0
    opencode run "$analysis_prompt" || oc_exit=$?

    if (( oc_exit != 0 )); then
      warn "  opencode failed (exit $oc_exit) during analysis — skipping file"
      (( stat_failures++ )) || true
      continue
    fi

    if [[ ! -f "$manifest" ]]; then
      warn "  opencode completed but manifest not found at: $manifest"
      warn "  Skipping — file will be retried on next run."
      (( stat_failures++ )) || true
      continue
    fi

    mark_analyzed "$kfile"
    (( stat_analyzed++ )) || true
    info "  Analysis complete → $manifest"
  fi

  # ── GENERATION STEP ────────────────────────────────────────────────────────
  if [[ ! -f "$manifest" ]]; then
    warn "  Manifest missing: $manifest — run without --only to re-analyze"
    continue
  fi

  while IFS=$'\t' read -r rule_name detectability; do
    [[ -z "$rule_name" ]] && continue

    if [[ "$detectability" == "intent-based" ]]; then
      if ! is_skipped "$kfile" "$rule_name"; then
        info "  [intent-based, skip] $rule_name"
        mark_skipped "$kfile" "$rule_name"
        (( stat_skipped++ )) || true
      fi
      continue
    fi

    if is_generated "$kfile" "$rule_name"; then
      info "  [skip] $rule_name (already generated)"
      (( stat_already_generated++ )) || true
      continue
    fi

    info "  → generating: $rule_name ($detectability)"

    rule_entry_json=""
    rule_entry_json="$(manifest_entry_json "$manifest" "$rule_name")" || {
      warn "  Could not extract entry for $rule_name from manifest — skipping"
      (( stat_failures++ )) || true
      continue
    }

    # Read current index.ts so the model can patch it correctly
    current_index="$(cat "$PLUGIN_DIR/src/index.ts")"

    gen_prompt="${generate_prompt_template}

--- RULE SPEC ---
${rule_entry_json}
--- END RULE SPEC ---

--- CURRENT eslint-plugin/src/index.ts ---
${current_index}
--- END CURRENT index.ts ---

Plugin directory (absolute path): ${PLUGIN_DIR}"

    oc_exit=0
    opencode run "$gen_prompt" || oc_exit=$?

    if (( oc_exit != 0 )); then
      warn "  opencode failed (exit $oc_exit) for rule $rule_name — will retry on next run"
      (( stat_failures++ )) || true
    else
      mark_generated "$kfile" "$rule_name"
      (( stat_generated++ )) || true
    fi

  done < <(manifest_entries "$manifest" 2>/dev/null || true)

done

# ── Summary ────────────────────────────────────────────────────────────────────
log "Complete."
printf '\n'
printf '  %-34s %d\n' "Knowledge files processed:"      "${#filtered_files[@]}"
printf '  %-34s %d\n' "Files analyzed (this run):"      "$stat_analyzed"
printf '  %-34s %d\n' "Files already analyzed:"         "$stat_already_analyzed"
printf '  %-34s %d\n' "Rules generated (this run):"     "$stat_generated"
printf '  %-34s %d\n' "Rules already generated:"        "$stat_already_generated"
printf '  %-34s %d\n' "Rules skipped (intent-based):"   "$stat_skipped"
printf '  %-34s %d\n' "Failures (will retry):"          "$stat_failures"
printf '\n'
printf '  Progress file: %s\n'  "$PROGRESS_FILE"
printf '  Work directory: %s\n' "$WORK_DIR"
printf '\n'
