#!/usr/bin/env bash
# vibe-clean.sh — AI-driven code cleanup using vibe-types skill knowledge
#
# For each (knowledge-file, source-file) pair, asks opencode to apply the
# technique to the source file without changing behavior. Optionally runs a
# build command after each edit and commits the result.
#
# Usage: ./vibe-clean.sh --skill <lang> (--file | --dir | --branch) [OPTIONS]
# Run with --help for full documentation.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Output helpers ─────────────────────────────────────────────────────────────
log()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
info() { printf '    \033[0;37m%s\033[0m\n' "$*"; }
warn() { printf '\033[1;33mWARN: %s\033[0m\n' "$*" >&2; }
err()  { printf '\033[1;31mERR:  %s\033[0m\n' "$*" >&2; }

# ── Language → file extensions ─────────────────────────────────────────────────
declare -A LANG_EXTS=(
  [typescript]=".ts .tsx .mts .cts"
  [python]=".py"
  [rust]=".rs"
  [scala3]=".scala .sc"
  [lean]=".lean"
  [haskell]=".hs"
  [ocaml]=".ml .mli"
  [java]=".java"
)

EXCLUDE_DIRS=(
  node_modules dist build target .git __pycache__
  .next out coverage .cache .tox .eggs .mypy_cache
)

# ── Defaults ───────────────────────────────────────────────────────────────────
OPT_SKILL=""
OPT_SKILL_DIR=""
OPT_FILE=""
OPT_DIR=""
OPT_BRANCH=""
OPT_BUILD=""
OPT_MAX_RETRIES=3
OPT_COMMIT=false
OPT_ONLY=""
OPT_DRY_RUN=false
OPT_PROGRESS=""
OPT_BASE_BRANCH="main"
OPT_CONSOLIDATE=false
OPT_PRINCIPLES=""

usage() {
  cat <<'EOF'
Usage: vibe-clean.sh --skill <lang> (--file <path> | --dir <path> | --branch <name>) [OPTIONS]

Target (exactly one required):
  --file <path>         Refactor a single source file
  --dir <path>          Refactor all source files in a directory (recursive)
  --branch <name>       Refactor files changed in <name> vs. its merge-base

Skill (required):
  --skill <lang>        Language name (typescript, python, rust, scala3, lean, …)
                        Resolves to <script-dir>/plugin/skills/<lang>/
  --skill-dir <path>    Override: explicit path to the skill directory

Build:
  --build <cmd>         Shell command to run after each source-file edit
                        (e.g. "npm run build", "cargo check", "python -m py_compile")
  --max-retries N       Max opencode fix attempts per build failure (default: 3)
                        Each attempt re-runs the build and passes fresh errors back,
                        so attempt 1 may fix test failures, attempt 2 compilation errors, etc.

Git:
  --commit              Create a commit after each successful (knowledge × source) pair
  --base-branch <name>  Base branch for --branch diff (default: main)

Optional:
  --only T01,UC03,...   Process only the listed knowledge file IDs (comma-separated)
  --dry-run             Print the plan without calling opencode or modifying files
  --progress <file>     Progress file path (default: .vibe-clean-progress)
  --consolidate         Run a final coherence pass over each changed file after all
                        techniques are applied, guided by SOLID/DRY/KISS principles
  --principles <file>   Override the default principles with a custom text file
  --help                Show this help

Examples:
  ./vibe-clean.sh --skill typescript --dir ./src --dry-run
  ./vibe-clean.sh --skill python --file app/models.py --build "python -m py_compile app/models.py"
  ./vibe-clean.sh --skill rust --branch feature/refactor --build "cargo check" --commit
  ./vibe-clean.sh --skill typescript --dir ./src --only T01,T02,UC01 --max-retries 5
EOF
}

# ── Argument parsing ───────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --skill)        OPT_SKILL="$2";        shift 2 ;;
    --skill-dir)    OPT_SKILL_DIR="$2";    shift 2 ;;
    --file)         OPT_FILE="$2";         shift 2 ;;
    --dir)          OPT_DIR="$2";          shift 2 ;;
    --branch)       OPT_BRANCH="$2";       shift 2 ;;
    --build)        OPT_BUILD="$2";        shift 2 ;;
    --max-retries)  OPT_MAX_RETRIES="$2";  shift 2 ;;
    --commit)       OPT_COMMIT=true;       shift ;;
    --only)         OPT_ONLY="$2";         shift 2 ;;
    --dry-run)      OPT_DRY_RUN=true;      shift ;;
    --progress)     OPT_PROGRESS="$2";     shift 2 ;;
    --base-branch)  OPT_BASE_BRANCH="$2";  shift 2 ;;
    --consolidate)  OPT_CONSOLIDATE=true;  shift ;;
    --principles)   OPT_PRINCIPLES="$2";   shift 2 ;;
    --help|-h)      usage; exit 0 ;;
    *) err "Unknown option: $1"; printf '\n' >&2; usage >&2; exit 1 ;;
  esac
done

# ── Validation ─────────────────────────────────────────────────────────────────
target_count=0
[[ -n "$OPT_FILE" ]]   && (( target_count++ )) || true
[[ -n "$OPT_DIR" ]]    && (( target_count++ )) || true
[[ -n "$OPT_BRANCH" ]] && (( target_count++ )) || true

if (( target_count == 0 )); then
  err "One of --file, --dir, or --branch is required."
  printf '\n' >&2; usage >&2; exit 1
fi
if (( target_count > 1 )); then
  err "Only one of --file, --dir, or --branch may be specified."; exit 1
fi
if [[ -z "$OPT_SKILL" && -z "$OPT_SKILL_DIR" ]]; then
  err "--skill or --skill-dir is required."
  printf '\n' >&2; usage >&2; exit 1
fi

# Resolve skill directory
SKILL_DIR=""
if [[ -n "$OPT_SKILL_DIR" ]]; then
  SKILL_DIR="$(realpath "$OPT_SKILL_DIR")"
else
  SKILL_DIR="$SCRIPT_DIR/plugin/skills/$OPT_SKILL"
fi

if [[ ! -d "$SKILL_DIR" ]]; then
  err "Skill directory not found: $SKILL_DIR"
  if [[ -n "$OPT_SKILL" && -d "$SCRIPT_DIR/plugin/skills" ]]; then
    available="$(find "$SCRIPT_DIR/plugin/skills" -maxdepth 1 -mindepth 1 -type d -printf '%f\n' 2>/dev/null | sort | tr '\n' ' ')"
    err "Available skills: $available"
  fi
  exit 1
fi

# Require git for --branch and --commit
if [[ -n "$OPT_BRANCH" || "$OPT_COMMIT" == true ]]; then
  if ! git rev-parse --git-dir &>/dev/null; then
    err "--branch and --commit require a git repository."
    exit 1
  fi
fi

PROGRESS_FILE="$(realpath "${OPT_PROGRESS:-.vibe-clean-progress}")"
if ! $OPT_DRY_RUN; then
  touch "$PROGRESS_FILE"
fi

# Fail early if the target repository has uncommitted changes —
# opencode may refuse to run on a dirty working tree.
# The progress file is explicitly excluded from this check.
if ! $OPT_DRY_RUN; then
  _target_for_git_check=""
  [[ -n "$OPT_FILE" ]]   && _target_for_git_check="$(dirname "$(realpath "$OPT_FILE")")"
  [[ -n "$OPT_DIR" ]]    && _target_for_git_check="$(realpath "$OPT_DIR")"
  [[ -n "$OPT_BRANCH" ]] && _target_for_git_check="."

  if [[ -n "$_target_for_git_check" ]]; then
    _target_git_root="$(git -C "$_target_for_git_check" rev-parse --show-toplevel 2>/dev/null)" || true
    if [[ -n "$_target_git_root" ]]; then
      _pf_rel="$(realpath --relative-to="$_target_git_root" "$PROGRESS_FILE" 2>/dev/null)" || _pf_rel=""
      _excl=(); [[ -n "$_pf_rel" ]] && _excl=( -- . ":(exclude)$_pf_rel" )
      if ! git -C "$_target_git_root" diff --quiet "${_excl[@]}" 2>/dev/null || \
         ! git -C "$_target_git_root" diff --cached --quiet "${_excl[@]}" 2>/dev/null; then
        err "Target repository has uncommitted changes: $_target_git_root"
        err "Commit or stash them before running vibe-clean."
        exit 1
      fi
    fi
  fi
fi

# ── Progress tracking ──────────────────────────────────────────────────────────
is_pair_done() {
  [[ -f "$PROGRESS_FILE" ]] && grep -qxF "done $1 $2" "$PROGRESS_FILE"
}

is_knowledge_failed() {
  [[ -f "$PROGRESS_FILE" ]] && grep -qxF "failed $1" "$PROGRESS_FILE"
}

mark_pair_done() {
  printf 'done %s %s\n' "$1" "$2" >> "$PROGRESS_FILE"
}

mark_knowledge_failed() {
  printf 'failed %s\n' "$1" >> "$PROGRESS_FILE"
}

# ── File collection helpers ────────────────────────────────────────────────────

# Populate global FIND_NAME_ARGS for the current language
FIND_NAME_ARGS=()
setup_find_name_args() {
  FIND_NAME_ARGS=()
  local lang="$1"
  if [[ -z "$lang" || -z "${LANG_EXTS[$lang]+_}" ]]; then
    FIND_NAME_ARGS=( -name '*' )
    return
  fi
  local first=true ext
  for ext in ${LANG_EXTS[$lang]}; do
    if $first; then
      FIND_NAME_ARGS+=( -name "*${ext}" )
      first=false
    else
      FIND_NAME_ARGS+=( -o -name "*${ext}" )
    fi
  done
}

# Returns 0 if $1 matches the current language's extensions
file_matches_lang() {
  local f="$1"
  if [[ -z "$OPT_SKILL" || -z "${LANG_EXTS[$OPT_SKILL]+_}" ]]; then
    return 0
  fi
  local ext
  for ext in ${LANG_EXTS[$OPT_SKILL]}; do
    [[ "$f" == *"$ext" ]] && return 0
  done
  return 1
}

collect_source_files() {
  if [[ -n "$OPT_FILE" ]]; then
    realpath "$OPT_FILE"
    return
  fi

  if [[ -n "$OPT_DIR" ]]; then
    local dir
    dir="$(realpath "$OPT_DIR")"
    setup_find_name_args "$OPT_SKILL"

    # Build prune clause: \( -name A -o -name B ... \) -prune
    local -a prune=( \( )
    local first=true excl
    for excl in "${EXCLUDE_DIRS[@]}"; do
      $first && prune+=( -name "$excl" ) || prune+=( -o -name "$excl" )
      first=false
    done
    prune+=( \) -prune )

    find "$dir" \
      "${prune[@]}" \
      -o \( -type f \( "${FIND_NAME_ARGS[@]}" \) -print \) \
    | sort
    return
  fi

  if [[ -n "$OPT_BRANCH" ]]; then
    local git_root merge_base
    git_root="$(git rev-parse --show-toplevel)"
    if ! merge_base="$(git merge-base "$OPT_BRANCH" "$OPT_BASE_BRANCH" 2>&1)"; then
      err "Cannot find merge-base between '$OPT_BRANCH' and '$OPT_BASE_BRANCH'."
      err "Use --base-branch to specify the correct base branch."
      exit 1
    fi
    while IFS= read -r rel; do
      local abs="$git_root/$rel"
      [[ ! -f "$abs" ]] && continue
      file_matches_lang "$abs" && echo "$abs"
    done < <(git diff --name-only "$merge_base" "$OPT_BRANCH" | sort)
    return
  fi
}

collect_knowledge_files() {
  local -a only_ids=()
  if [[ -n "$OPT_ONLY" ]]; then
    IFS=',' read -ra only_ids <<< "$OPT_ONLY"
  fi

  while IFS= read -r -d '' kf; do
    local bn
    bn="$(basename "$kf" .md)"
    [[ "$bn" == "00-overview" ]] && continue

    if (( ${#only_ids[@]} > 0 )); then
      local matched=false id
      for id in "${only_ids[@]}"; do
        [[ "$bn" == "$id" || "$bn" == "${id}-"* ]] && matched=true && break
      done
      $matched || continue
    fi

    realpath "$kf"
  done < <(
    find "$SKILL_DIR/catalog" "$SKILL_DIR/usecases" \
      -maxdepth 1 -name '*.md' -print0 2>/dev/null | sort -z
  )
}

# T01-algebraic-data-types.md → T01
knowledge_id() { basename "$1" .md | cut -d- -f1; }

# Extract the first # heading from a knowledge file
knowledge_title() {
  grep -m1 '^# ' "$1" 2>/dev/null | sed 's/^# //' | tr -d '\r'
}

# Build a GitHub blob URL for a knowledge file, e.g.:
#   https://github.com/jpablo/vibe-types/blob/main/plugin/skills/typescript/catalog/T01-...md
# Returns empty string (exit 1) if the repo has no GitHub remote.
knowledge_github_url() {
  local kfile="$1"
  local git_root remote branch rel_path

  # Always resolve relative to the vibe-types repo, not the target project
  git_root="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null)" || return 1
  remote="$(git -C "$SCRIPT_DIR" remote get-url origin 2>/dev/null)"       || return 1

  # Normalise to bare HTTPS URL: strip .git, convert SSH to HTTPS
  remote="${remote%.git}"
  if [[ "$remote" =~ ^git@github\.com:(.+)$ ]]; then
    remote="https://github.com/${BASH_REMATCH[1]}"
  fi
  [[ "$remote" == *"github.com"* ]] || return 1

  branch="$(git -C "$SCRIPT_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null)" || branch="main"
  [[ "$branch" == "HEAD" ]] && branch="main"   # detached HEAD fallback

  rel_path="$(realpath --relative-to="$git_root" "$kfile" 2>/dev/null)" || return 1
  printf '%s/blob/%s/%s' "$remote" "$branch" "$rel_path"
}

# ── Prompt builders ────────────────────────────────────────────────────────────
build_apply_prompt() {
  local knowledge_file="$1" source_file="$2" prior_diff="${3:-}"

  local prior_section=""
  if [[ -n "$prior_diff" ]]; then
    prior_section="--- CHANGES ALREADY APPLIED TO THIS FILE (by earlier techniques in this run) ---
$prior_diff
--- END PRIOR CHANGES ---

These changes are settled decisions. Build on them — do not revert or contradict them.

"
  fi

  cat <<PROMPT
You are a code quality assistant. Refactor a source file by applying techniques
from a knowledge document.

Rules:
1. Only make changes that genuinely improve the code using the described techniques.
2. Do NOT change observable behavior, public APIs, or test assertions.
3. Prefer minimal, targeted changes over wholesale rewrites.
4. If prior changes are shown, treat them as settled — do not revert or contradict them.

${prior_section}--- KNOWLEDGE: $(basename "$knowledge_file") ---
$(cat "$knowledge_file")
--- END KNOWLEDGE ---

Now edit @$source_file in place. Only change what the knowledge document genuinely warrants; if nothing applies, leave the file untouched.
PROMPT
}

build_fix_prompt() {
  local source_file="$1" build_output="$2"
  cat <<PROMPT
The following build errors occurred after your refactoring of @$source_file.
Fix them while preserving the intent of the previous changes.

--- BUILD ERRORS ---
$build_output
--- END BUILD ERRORS ---

Now edit @$source_file in place to fix the errors above.
PROMPT
}

build_consolidate_prompt() {
  local source_file="$1" changes_diff="$2"

  local principles
  if [[ -n "$OPT_PRINCIPLES" && -f "$OPT_PRINCIPLES" ]]; then
    principles="$(cat "$OPT_PRINCIPLES")"
  else
    principles="$(cat <<'PRINCIPLES'
S — Single Responsibility: each type, function, and module has one clear reason to change.
O — Open/Closed: extend behavior through new types or functions; avoid modifying stable abstractions.
L — Liskov Substitution: subtypes and implementations must honour the contracts of their interfaces.
I — Interface Segregation: keep interfaces narrow; callers should not depend on methods they do not use.
D — Dependency Inversion: high-level modules depend on abstractions, not on concrete implementations.

DRY (Don't Repeat Yourself): extract shared logic and types rather than duplicating them.
KISS (Keep It Simple): prefer the simplest correct solution; avoid unnecessary abstraction.
Cohesion: group related types and functions together; a module should have a single, clear purpose.
PRINCIPLES
)"
  fi

  cat <<PROMPT
You are a code quality assistant performing a final consolidation pass.

Multiple refactoring techniques have been applied to this file one by one. Your task
is to review the result as a whole and produce a final, coherent version.

Goals:
1. Resolve any contradictions or redundancies introduced by the individual passes.
2. Align the overall design with the engineering principles listed below.
3. Ensure the file reads as if it were written with a single, coherent intent.
4. Do NOT change observable behavior, public APIs, or test assertions.
5. If the file is already consistent and well-structured, do not modify it.

--- ENGINEERING PRINCIPLES ---
$principles
--- END PRINCIPLES ---

--- CHANGES MADE IN THIS RUN (for context) ---
$changes_diff
--- END CHANGES ---

Now edit @$source_file in place to make it a coherent whole. If it is already consistent and well-structured, leave it untouched.
PROMPT
}

# ── Main ───────────────────────────────────────────────────────────────────────
main() {
  log "Collecting knowledge files from: $SKILL_DIR"
  local -a knowledge_files
  mapfile -t knowledge_files < <(collect_knowledge_files)

  if (( ${#knowledge_files[@]} == 0 )); then
    err "No knowledge files found in $SKILL_DIR/{catalog,usecases}"
    [[ -n "$OPT_ONLY" ]] && err "(--only filter: '$OPT_ONLY' — verify the IDs match Tnn/UCnn filenames)"
    exit 1
  fi
  info "Found ${#knowledge_files[@]} knowledge file(s)."

  log "Collecting source files..."
  local -a source_files
  mapfile -t source_files < <(collect_source_files)

  if (( ${#source_files[@]} == 0 )); then
    err "No source files found for the given target."
    exit 1
  fi
  info "Found ${#source_files[@]} source file(s)."

  # Dry-run: print plan and exit
  if $OPT_DRY_RUN; then
    log "DRY RUN — no changes will be made"
    local kf sf
    for kf in "${knowledge_files[@]}"; do
      for sf in "${source_files[@]}"; do
        printf '  apply %-45s → %s\n' "$(basename "$kf")" "$sf"
      done
    done
    printf '\n  Total pairs: %d\n' "$(( ${#knowledge_files[@]} * ${#source_files[@]} ))"
    return 0
  fi

  # Snapshot HEAD so we can later diff what vibe-clean has changed per file
  local run_start_head=""
  run_start_head="$(git rev-parse HEAD 2>/dev/null)" || true

  local stat_attempted=0 stat_skipped=0 stat_oc_failures=0
  local stat_build_fixed=0 stat_committed=0 stat_consolidated=0

  local kfile
  for kfile in "${knowledge_files[@]}"; do
    local kid kname
    kid="$(knowledge_id "$kfile")"
    kname="$(basename "$kfile")"

    if is_knowledge_failed "$kfile"; then
      info "Skipping $kname (previously failed — delete '$PROGRESS_FILE' to retry)"
      continue
    fi

    log "Applying: $kname"

    # Redirect source files through fd 3 so opencode doesn't consume stdin
    while IFS= read -r sfile <&3; do
      local sname
      sname="$(basename "$sfile")"

      if is_pair_done "$kfile" "$sfile"; then
        info "  [skip] $sname (already done)"
        (( stat_skipped++ )) || true
        continue
      fi

      info "  → $sname"
      (( stat_attempted++ )) || true

      # APPLY STEP
      # Compute what earlier techniques already changed in this file so the AI
      # can avoid contradictions.
      local prior_diff=""
      if [[ -n "$run_start_head" ]]; then
        if $OPT_COMMIT; then
          prior_diff="$(git diff "$run_start_head"..HEAD -- "$sfile" 2>/dev/null)" || true
        else
          prior_diff="$(git diff HEAD -- "$sfile" 2>/dev/null)" || true
        fi
      fi

      local prompt oc_exit=0
      prompt="$(build_apply_prompt "$kfile" "$sfile" "$prior_diff")"
      opencode run "$prompt" || oc_exit=$?

      if (( oc_exit != 0 )); then
        warn "opencode failed (exit $oc_exit) for $kname × $sname — skipping pair"
        (( stat_oc_failures++ )) || true
        continue
      fi

      # BUILD STEP
      if [[ -n "$OPT_BUILD" ]]; then
        local build_out build_exit=0
        build_out="$(bash -c "$OPT_BUILD" 2>&1)" || build_exit=$?

        if (( build_exit != 0 )); then
          info "    Build failed — attempting fixes (max $OPT_MAX_RETRIES)"
          local fixed=false attempt
          for (( attempt=1; attempt <= OPT_MAX_RETRIES; attempt++ )); do
            info "    Fix attempt $attempt/$OPT_MAX_RETRIES..."
            local fix_prompt fix_exit=0
            fix_prompt="$(build_fix_prompt "$sfile" "$build_out")"
            opencode run "$fix_prompt" || fix_exit=$?
            build_exit=0
            build_out="$(bash -c "$OPT_BUILD" 2>&1)" || build_exit=$?
            if (( build_exit == 0 )); then
              fixed=true
              (( stat_build_fixed++ )) || true
              break
            fi
          done

          if ! $fixed; then
            err "Build still failing after $OPT_MAX_RETRIES attempt(s) — reverting $sname"
            git checkout -- "$sfile" 2>/dev/null \
              || warn "Could not revert $sfile (is it tracked by git?)"
            mark_knowledge_failed "$kfile"
            err ""
            err "Run stopped. Re-run the script to resume from the next knowledge file."
            err "Progress file: $PROGRESS_FILE"
            err ""
            print_summary "$stat_attempted" "$stat_skipped" "$stat_oc_failures" \
                          "$stat_build_fixed" "$stat_committed" \
                          "${#knowledge_files[@]}" "${#source_files[@]}"
            exit 1
          fi
        fi
      fi

      # RECORD STEP
      mark_pair_done "$kfile" "$sfile"

      # COMMIT STEP
      if $OPT_COMMIT; then
        local git_root rel_path
        git_root="$(git rev-parse --show-toplevel 2>/dev/null)" || git_root=""
        if [[ -n "$git_root" ]]; then
          rel_path="$(realpath --relative-to="$git_root" "$sfile" 2>/dev/null)" || rel_path="$sname"
        else
          rel_path="$sname"
        fi
        git add -A 2>/dev/null || true
        git restore --staged "$PROGRESS_FILE" 2>/dev/null || true
        if ! git diff --cached --quiet 2>/dev/null; then
          local ktitle kurl commit_msg
          ktitle="$(knowledge_title "$kfile")"
          [[ -z "$ktitle" ]] && ktitle="$(basename "$kfile" .md)"
          kurl="$(knowledge_github_url "$kfile" 2>/dev/null)" || kurl=""

          commit_msg="cleanup($kid): $ktitle"$'\n'
          [[ -n "$kurl" ]] && commit_msg+=$'\n'"Knowledge: $kurl"
          commit_msg+=$'\n'"Source: $rel_path"

          git commit -m "$commit_msg" \
            || warn "git commit failed for $sname"
          (( stat_committed++ )) || true
        fi
      fi

    done 3< <(printf '%s\n' "${source_files[@]}")

  done  # knowledge files

  # ── CONSOLIDATION PASS ───────────────────────────────────────────────────────
  if $OPT_CONSOLIDATE; then
    log "Consolidation pass — reviewing each changed file as a whole..."

    while IFS= read -r sfile <&3; do
      local sname
      sname="$(basename "$sfile")"

      # Only consolidate files that were actually changed during this run
      local full_diff=""
      if [[ -n "$run_start_head" ]]; then
        if $OPT_COMMIT; then
          full_diff="$(git diff "$run_start_head"..HEAD -- "$sfile" 2>/dev/null)" || true
        else
          full_diff="$(git diff HEAD -- "$sfile" 2>/dev/null)" || true
        fi
      fi

      if [[ -z "$full_diff" ]]; then
        info "  [skip] $sname (unchanged during this run)"
        continue
      fi

      info "  → $sname"

      local con_prompt con_exit=0
      con_prompt="$(build_consolidate_prompt "$sfile" "$full_diff")"
      opencode run "$con_prompt" || con_exit=$?

      if (( con_exit != 0 )); then
        warn "opencode failed during consolidation of $sname — skipping"
        continue
      fi

      # Build check (non-fatal: revert and skip rather than stopping the run)
      if [[ -n "$OPT_BUILD" ]]; then
        local build_out build_exit=0
        build_out="$(bash -c "$OPT_BUILD" 2>&1)" || build_exit=$?

        if (( build_exit != 0 )); then
          info "    Build failed — attempting fixes (max $OPT_MAX_RETRIES)"
          local fixed=false attempt
          for (( attempt=1; attempt <= OPT_MAX_RETRIES; attempt++ )); do
            info "    Fix attempt $attempt/$OPT_MAX_RETRIES..."
            local fix_prompt fix_exit=0
            fix_prompt="$(build_fix_prompt "$sfile" "$build_out")"
            opencode run "$fix_prompt" || fix_exit=$?
            build_exit=0
            build_out="$(bash -c "$OPT_BUILD" 2>&1)" || build_exit=$?
            if (( build_exit == 0 )); then
              fixed=true
              (( stat_build_fixed++ )) || true
              break
            fi
          done

          if ! $fixed; then
            warn "Build still failing after consolidation of $sname — reverting"
            git checkout -- "$sfile" 2>/dev/null || warn "Could not revert $sfile"
            continue
          fi
        fi
      fi

      (( stat_consolidated++ )) || true

      if $OPT_COMMIT; then
        local git_root rel_path
        git_root="$(git rev-parse --show-toplevel 2>/dev/null)" || git_root=""
        if [[ -n "$git_root" ]]; then
          rel_path="$(realpath --relative-to="$git_root" "$sfile" 2>/dev/null)" || rel_path="$sname"
        else
          rel_path="$sname"
        fi
        git add -A 2>/dev/null || true
        git restore --staged "$PROGRESS_FILE" 2>/dev/null || true
        if ! git diff --cached --quiet 2>/dev/null; then
          git commit -m "consolidate: $rel_path" \
            || warn "git commit failed for $sname"
          (( stat_committed++ )) || true
        fi
      fi

    done 3< <(printf '%s\n' "${source_files[@]}")
  fi

  print_summary "$stat_attempted" "$stat_skipped" "$stat_oc_failures" \
                "$stat_build_fixed" "$stat_committed" "$stat_consolidated" \
                "${#knowledge_files[@]}" "${#source_files[@]}"
}

print_summary() {
  local attempted="$1" skipped="$2" oc_failures="$3"
  local build_fixed="$4" committed="$5" consolidated="$6"
  local total_kfiles="$7" total_sfiles="$8"
  log "Complete."
  printf '\n'
  printf '  %-32s %d\n' "Knowledge files:"             "$total_kfiles"
  printf '  %-32s %d\n' "Source files targeted:"       "$total_sfiles"
  printf '  %-32s %d\n' "Pairs attempted:"              "$attempted"
  printf '  %-32s %d\n' "Pairs skipped (resuming):"    "$skipped"
  printf '  %-32s %d\n' "opencode failures:"            "$oc_failures"
  printf '  %-32s %d\n' "Build errors fixed:"           "$build_fixed"
  $OPT_CONSOLIDATE && printf '  %-32s %d\n' "Files consolidated:" "$consolidated"
  $OPT_COMMIT      && printf '  %-32s %d\n' "Commits created:"    "$committed"
  printf '\n'
}

main
