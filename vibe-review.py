#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["unidiff>=0.7"]
# ///
"""vibe-review.py — AI-driven code review using vibe-types skill knowledge.

For each (knowledge-file, changed-file) pair in the branch diff, asks opencode
to identify issues and write inline review comments to a temp JSON file.
Aggregates all comments into a GitHub PR review JSON and optionally posts it.

Usage: python vibe-review.py --skill <lang> [OPTIONS]
Run with --help for full documentation.
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from unidiff import PatchSet
    from unidiff.patch import PatchedFile
except ImportError:
    print("ERR: unidiff not installed. Run: pip install unidiff", file=sys.stderr)
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent.resolve()

# ── Output helpers ─────────────────────────────────────────────────────────────

def log(msg: str)  -> None: print(f"\n\033[1;36m==> {msg}\033[0m")
def info(msg: str) -> None: print(f"    \033[0;37m{msg}\033[0m")
def warn(msg: str) -> None: print(f"\033[1;33mWARN: {msg}\033[0m", file=sys.stderr)
def err(msg: str)  -> None: print(f"\033[1;31mERR:  {msg}\033[0m", file=sys.stderr)

# ── Language → file extensions ─────────────────────────────────────────────────

LANG_EXTS: dict[str, list[str]] = {
    "typescript": [".ts", ".tsx", ".mts", ".cts"],
    "python":     [".py"],
    "rust":       [".rs"],
    "scala3":     [".scala", ".sc"],
    "lean":       [".lean"],
    "haskell":    [".hs"],
    "ocaml":      [".ml", ".mli"],
    "java":       [".java"],
}

# ── Git / gh CLI helpers ───────────────────────────────────────────────────────

def git(*args: str, cwd: str | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        capture_output=True, text=True,
        cwd=cwd or str(Path.cwd()),
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.stdout.strip()


def run_gh(*args: str) -> str:
    result = subprocess.run(["gh", *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.stdout.strip()

# ── Knowledge file helpers ─────────────────────────────────────────────────────

def knowledge_id(kfile: Path) -> str:
    """T01-algebraic-data-types.md → T01"""
    return kfile.stem.split("-")[0]


def knowledge_title(kfile: Path) -> str:
    """Extract the first # heading from a knowledge file."""
    try:
        for line in kfile.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    except Exception:
        pass
    return kfile.stem


def knowledge_github_url(kfile: Path) -> str:
    """Build a GitHub blob URL for the knowledge file, or empty string on failure."""
    try:
        git_root = Path(git("rev-parse", "--show-toplevel", cwd=str(SCRIPT_DIR)))
        remote = git("remote", "get-url", "origin", cwd=str(SCRIPT_DIR))
        remote = remote.removesuffix(".git")
        if remote.startswith("git@github.com:"):
            remote = "https://github.com/" + remote[len("git@github.com:"):]
        if "github.com" not in remote:
            return ""
        branch = git("rev-parse", "--abbrev-ref", "HEAD", cwd=str(SCRIPT_DIR))
        if branch == "HEAD":
            branch = "main"
        rel = kfile.resolve().relative_to(git_root)
        return f"{remote}/blob/{branch}/{rel}"
    except Exception:
        return ""


def collect_knowledge_files(skill_dir: Path, only_ids: list[str]) -> list[Path]:
    files: list[Path] = []
    for subdir in ["catalog", "usecases"]:
        d = skill_dir / subdir
        if d.is_dir():
            files.extend(sorted(d.glob("*.md")))

    result = []
    for kf in files:
        if kf.stem == "00-overview":
            continue
        if only_ids:
            kid = knowledge_id(kf)
            if not any(kid == oid or kf.stem.startswith(f"{oid}-") for oid in only_ids):
                continue
        result.append(kf)
    return result

# ── Diff collection and analysis ───────────────────────────────────────────────

def file_matches_lang(path: str, lang: str) -> bool:
    if lang not in LANG_EXTS:
        return True
    return any(path.endswith(ext) for ext in LANG_EXTS[lang])


def collect_diff_files(branch: str, base_branch: str, lang: str) -> dict[str, PatchedFile]:
    """Return {file_path: PatchedFile} for each changed file matching the language."""
    merge_base = git("merge-base", branch, base_branch)
    full_diff = git("diff", f"{merge_base}...{branch}")
    if not full_diff:
        return {}
    patch = PatchSet(full_diff)
    return {pf.path: pf for pf in patch if file_matches_lang(pf.path, lang)}


def build_valid_lines(pf: PatchedFile) -> set[tuple[int, str]]:
    """Return the set of (line_no, side) pairs that GitHub will accept as comment targets."""
    valid: set[tuple[int, str]] = set()
    for hunk in pf:
        for line in hunk:
            if line.is_added:
                if line.target_line_no is not None:
                    valid.add((line.target_line_no, "RIGHT"))
            elif line.is_removed:
                if line.source_line_no is not None:
                    valid.add((line.source_line_no, "LEFT"))
            else:  # context line — both sides are valid targets
                if line.source_line_no is not None:
                    valid.add((line.source_line_no, "LEFT"))
                if line.target_line_no is not None:
                    valid.add((line.target_line_no, "RIGHT"))
    return valid


def format_diff_for_prompt(pf: PatchedFile) -> str:
    """
    Render a PatchedFile as an annotated diff where every line is tagged with
    [L<n>] / [R<n>] / [L<n>|R<n>] so the model can identify valid comment targets.
    """
    lines = [f"--- a/{pf.source_file}", f"+++ b/{pf.target_file}"]
    for hunk in pf:
        lines.append(
            f"@@ -{hunk.source_start},{hunk.source_length}"
            f" +{hunk.target_start},{hunk.target_length} @@"
        )
        for line in hunk:
            content = line.value.rstrip("\n")
            if line.is_added:
                lines.append(f"+[R{line.target_line_no}] {content}")
            elif line.is_removed:
                lines.append(f"-[L{line.source_line_no}] {content}")
            else:
                lines.append(f" [L{line.source_line_no}|R{line.target_line_no}] {content}")
    return "\n".join(lines)

# ── Prompt builders ────────────────────────────────────────────────────────────

def build_review_prompt(
    kfile: Path,
    file_path: str,
    formatted_diff: str,
    tmp_json: Path,
) -> str:
    kid    = knowledge_id(kfile)
    ktitle = knowledge_title(kfile)
    kurl   = knowledge_github_url(kfile)
    citation = f"[{kid} · {ktitle}]({kurl})" if kurl else f"[{kid} · {ktitle}]"

    return f"""You are a code reviewer. Review the diff below using the knowledge document.
Write your findings to @{tmp_json}.

The file must contain a valid JSON array. Each element must have exactly:
  {{ "line": <integer>, "side": "RIGHT" or "LEFT", "body": "<your comment>" }}

Rules:
1. Only use line numbers annotated [R<n>] (side "RIGHT") or [L<n>] (side "LEFT") in the diff.
2. Begin every "body" with the citation: {citation}
3. Keep each comment focused: state the issue, explain why it matters, suggest the fix (2–4 sentences).
4. Only flag genuine issues. Write [] if nothing in this diff warrants a comment.
5. You MAY comment on context lines (unchanged code visible in the diff) if refactoring that
   surrounding code would make the reviewed changes simpler, clearer, or more correct.

--- KNOWLEDGE: {kfile.name} ---
{kfile.read_text(encoding="utf-8")}
--- END KNOWLEDGE ---

--- DIFF: {file_path} ---
{formatted_diff}
--- END DIFF ---

Now write the JSON array to @{tmp_json}. Write [] if you find nothing worth flagging.
"""


def build_summary_prompt(comments: list[dict], tmp_md: Path) -> str:
    by_file: dict[str, int] = {}
    for c in comments:
        by_file[c["path"]] = by_file.get(c["path"], 0) + 1
    file_lines = "\n".join(
        f"  - {path}: {n} comment(s)" for path, n in sorted(by_file.items())
    )
    return f"""You are a code reviewer. Write the opening paragraph for a pull request review.
Write a concise Markdown summary (3–5 sentences) to @{tmp_md}.

The summary should:
- Describe the main themes found across the review
- Note the total number of comments and which files were most affected
- Be professional and constructive in tone
- NOT repeat individual findings (those appear as inline comments)

Files reviewed:
{file_lines}

Total inline comments: {len(comments)}

Write your Markdown summary to @{tmp_md}. The file should contain plain Markdown text only.
"""

# ── opencode invocation ────────────────────────────────────────────────────────

def run_opencode(prompt: str) -> int:
    return subprocess.run(["opencode", "run", prompt]).returncode

# ── GitHub helpers ─────────────────────────────────────────────────────────────

def gh_detect_pr() -> str | None:
    try:
        return run_gh("pr", "view", "--json", "number", "-q", ".number")
    except Exception:
        return None


def post_review(output_path: Path, pr_number: str) -> None:
    repo = run_gh("repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner")
    run_gh("api", f"repos/{repo}/pulls/{pr_number}/reviews", "--input", str(output_path))

# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="vibe-review.py",
        description="AI-driven code review using vibe-types skill knowledge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python vibe-review.py --skill typescript --dry-run
  python vibe-review.py --skill typescript --no-post --output /tmp/review.json
  python vibe-review.py --skill python --branch feature/my-branch --only T13,UC08
  python vibe-review.py --skill typescript --pr 42
""",
    )
    p.add_argument("--skill",       metavar="LANG", help="Language name (typescript, python, rust, …)")
    p.add_argument("--skill-dir",   metavar="PATH", help="Override skill directory path")
    p.add_argument("--branch",      metavar="NAME", help="Branch to review (default: current branch)")
    p.add_argument("--base-branch", metavar="NAME", default="main",
                   help="Base branch for diff (default: main)")
    p.add_argument("--output",      metavar="FILE", default="vibe-review.json",
                   help="Output JSON path (default: vibe-review.json)")
    p.add_argument("--no-post",     action="store_true", help="Skip GitHub posting")
    p.add_argument("--pr",          metavar="N",    help="Explicit PR number (overrides auto-detection)")
    p.add_argument("--only",        metavar="IDs",
                   help="Comma-separated knowledge file IDs to process (e.g. T01,UC08)")
    p.add_argument("--dry-run",     action="store_true", help="Print plan without calling opencode")
    return p.parse_args()

# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()

    if not args.skill and not args.skill_dir:
        err("--skill or --skill-dir is required.")
        sys.exit(1)

    skill_dir = (
        Path(args.skill_dir).resolve()
        if args.skill_dir
        else SCRIPT_DIR / "plugin" / "skills" / args.skill
    )
    if not skill_dir.is_dir():
        err(f"Skill directory not found: {skill_dir}")
        skills_root = SCRIPT_DIR / "plugin" / "skills"
        if skills_root.is_dir():
            available = " ".join(sorted(p.name for p in skills_root.iterdir() if p.is_dir()))
            err(f"Available skills: {available}")
        sys.exit(1)

    # Resolve branch
    branch = args.branch
    if not branch:
        try:
            branch = git("rev-parse", "--abbrev-ref", "HEAD")
        except RuntimeError as e:
            err(f"Could not determine current branch: {e}")
            sys.exit(1)
    if branch == "HEAD":
        err("Detached HEAD state — pass --branch explicitly.")
        sys.exit(1)

    # Knowledge files
    only_ids = [x.strip() for x in args.only.split(",")] if args.only else []
    log(f"Collecting knowledge files from: {skill_dir}")
    knowledge_files = collect_knowledge_files(skill_dir, only_ids)
    if not knowledge_files:
        err(f"No knowledge files found in {skill_dir}/{{catalog,usecases}}")
        if args.only:
            err(f"(--only filter: '{args.only}' — verify the IDs match Tnn/UCnn filenames)")
        sys.exit(1)
    info(f"Found {len(knowledge_files)} knowledge file(s).")

    # Changed files
    log(f"Collecting changed files ({branch} vs {args.base_branch})...")
    try:
        diff_files = collect_diff_files(branch, args.base_branch, args.skill or "")
    except RuntimeError as e:
        err(str(e))
        sys.exit(1)
    if not diff_files:
        err(f"No changed {args.skill or ''} files found between {branch} and {args.base_branch}.")
        sys.exit(1)
    info(f"Found {len(diff_files)} changed file(s).")

    # Dry run
    if args.dry_run:
        log("DRY RUN — no changes will be made")
        total = len(knowledge_files) * len(diff_files)
        for kf in knowledge_files:
            for fp in diff_files:
                print(f"  review  {kf.name:<50} → {fp}")
        print(f"\n  Total pairs: {total}")
        return

    # HEAD commit of the review branch (required by GitHub for inline comments)
    try:
        commit_id = git("rev-parse", branch)
    except RuntimeError:
        commit_id = ""

    all_comments: list[dict] = []
    stat_pairs       = 0
    stat_oc_failures = 0
    stat_discarded   = 0

    with tempfile.TemporaryDirectory(prefix="vibe-review-") as tmpdir:
        tmp_path = Path(tmpdir)

        for kfile in knowledge_files:
            log(f"Reviewing with: {kfile.name}")

            for file_path, pf in diff_files.items():
                fname = Path(file_path).name
                info(f"  → {fname}")
                stat_pairs += 1

                valid_lines = build_valid_lines(pf)
                if not valid_lines:
                    info("    [skip] no diff lines to comment on")
                    continue

                formatted_diff = format_diff_for_prompt(pf)

                # Seed the temp file so opencode has a target to overwrite
                safe_name = f"{knowledge_id(kfile)}-{fname}.json"
                tmp_json = tmp_path / safe_name
                tmp_json.write_text("[]", encoding="utf-8")

                prompt   = build_review_prompt(kfile, file_path, formatted_diff, tmp_json)
                oc_exit  = run_opencode(prompt)

                if oc_exit != 0:
                    warn(f"opencode failed (exit {oc_exit}) for {kfile.name} × {fname}")
                    stat_oc_failures += 1
                    continue

                # Parse opencode's output
                try:
                    raw = json.loads(tmp_json.read_text(encoding="utf-8"))
                    if not isinstance(raw, list):
                        raise ValueError("expected a JSON array")
                except Exception as e:
                    warn(f"Bad JSON from opencode for {kfile.name} × {fname}: {e}")
                    stat_oc_failures += 1
                    continue

                # Validate and collect comments
                added = 0
                for item in raw:
                    if not isinstance(item, dict):
                        continue
                    line = item.get("line")
                    side = item.get("side", "RIGHT")
                    body = str(item.get("body", "")).strip()
                    if not body or not isinstance(line, int):
                        continue
                    if (line, side) not in valid_lines:
                        warn(f"    Discarding line {line} ({side}) — not in diff window")
                        stat_discarded += 1
                        continue
                    all_comments.append({"path": file_path, "line": line, "side": side, "body": body})
                    added += 1

                if added:
                    info(f"    {added} comment(s) added")

        # Sort by file → line → side
        all_comments.sort(key=lambda c: (c["path"], c["line"], c["side"]))

        # Generate review summary body
        review_body = ""
        if all_comments:
            log("Generating review summary...")
            tmp_md = tmp_path / "summary.md"
            tmp_md.write_text("", encoding="utf-8")
            if run_opencode(build_summary_prompt(all_comments, tmp_md)) == 0:
                review_body = tmp_md.read_text(encoding="utf-8").strip()
        if not review_body:
            n_files = len({c["path"] for c in all_comments})
            review_body = (
                f"vibe-types review: {len(all_comments)} comment(s) across {n_files} file(s)."
            )

    # Assemble GitHub PR review JSON
    review: dict = {
        "body":     review_body,
        "event":    "COMMENT",
        "comments": all_comments,
    }
    if commit_id:
        review["commit_id"] = commit_id

    output_path = Path(args.output)
    output_path.write_text(json.dumps(review, indent=2), encoding="utf-8")
    log(f"Review written to: {output_path}")

    # Auto-post
    if not args.no_post:
        pr_number = args.pr or gh_detect_pr()
        if pr_number:
            log(f"Posting review to PR #{pr_number}...")
            try:
                post_review(output_path, pr_number)
                log("Posted successfully.")
            except RuntimeError as e:
                err(f"Failed to post review: {e}")
                info(f"Post manually: gh api repos/OWNER/REPO/pulls/{pr_number}/reviews --input {output_path}")
        else:
            info("No open PR detected for this branch — skipping auto-post.")
            info(f"Post manually: gh api repos/OWNER/REPO/pulls/N/reviews --input {output_path}")

    # Summary
    log("Complete.")
    print()
    print(f"  {'Knowledge files:':<32} {len(knowledge_files)}")
    print(f"  {'Source files reviewed:':<32} {len(diff_files)}")
    print(f"  {'Pairs processed:':<32} {stat_pairs}")
    print(f"  {'opencode failures:':<32} {stat_oc_failures}")
    print(f"  {'Comments discarded (bad lines):':<32} {stat_discarded}")
    print(f"  {'Comments in review:':<32} {len(all_comments)}")
    print()


if __name__ == "__main__":
    main()
