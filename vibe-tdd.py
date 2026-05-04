#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""vibe-tdd.py — AI-driven TDD snippet improvement using vibe-types skill knowledge.

For each (knowledge-file, code-snippet) pair in a markdown Technical Design Document,
asks opencode to check whether the knowledge applies and suggest an improved snippet.
Improvements are applied sequentially per snippet.

In-place mode (default): snippets are rewritten one at a time, last-to-first, so
earlier offsets remain valid throughout the run. With --commit, each improved snippet
is committed immediately after it is written back.

Summary mode (--output FILE): no file is modified; a standalone report listing all
suggested improvements is written to FILE for the user to review and apply manually.

Usage: python vibe-tdd.py --file design.md [OPTIONS]
Run with --help for full documentation.
"""

import argparse
import difflib
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()

# ── Output helpers ─────────────────────────────────────────────────────────────

def log(msg: str)  -> None: print(f"\n\033[1;36m==> {msg}\033[0m")
def info(msg: str) -> None: print(f"    \033[0;37m{msg}\033[0m")
def warn(msg: str) -> None: print(f"\033[1;33mWARN: {msg}\033[0m", file=sys.stderr)
def err(msg: str)  -> None: print(f"\033[1;31mERR:  {msg}\033[0m", file=sys.stderr)

# ── Fence language tag → skill name ───────────────────────────────────────────

FENCE_TO_SKILL: dict[str, str] = {
    "typescript": "typescript",
    "ts":         "typescript",
    "tsx":        "typescript",
    "python":     "python",
    "py":         "python",
    "rust":       "rust",
    "rs":         "rust",
    "scala":      "scala3",
    "scala3":     "scala3",
    "lean":       "lean",
    "lean4":      "lean",
    "haskell":    "haskell",
    "hs":         "haskell",
    "ocaml":      "ocaml",
    "ml":         "ocaml",
    "java":       "java",
    "agda":       "agda",
    "tlaplus":    "tlaplus",
}

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


def load_knowledge_files(skill_dir: Path, only: list[str] | None) -> list[Path]:
    """Return sorted knowledge files, optionally filtered by ID list."""
    catalog = skill_dir / "catalog"
    search_dir = catalog if catalog.is_dir() else skill_dir
    files = sorted(
        f for f in search_dir.glob("*.md")
        if not f.name.startswith("00-")
    )
    if only:
        ids = {i.upper() for i in only}
        files = [f for f in files if knowledge_id(f).upper() in ids]
    return files

# ── opencode invocation ────────────────────────────────────────────────────────

def run_opencode(prompt: str) -> int:
    return subprocess.run(["opencode", "run", prompt]).returncode

# ── Git helpers ────────────────────────────────────────────────────────────────

def _git(*args: str, cwd: str | None = None) -> str:
    r = subprocess.run(["git", *args], capture_output=True, text=True, cwd=cwd or str(Path.cwd()))
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{r.stderr.strip()}")
    return r.stdout.strip()


def _in_git_repo() -> bool:
    try:
        _git("rev-parse", "--git-dir")
        return True
    except RuntimeError:
        return False


def _check_clean_tree(source: Path) -> None:
    """Exit if the target repository has uncommitted changes."""
    try:
        git_root = _git("rev-parse", "--show-toplevel", cwd=str(source.parent))
    except RuntimeError:
        return  # not in a git repo — skip check
    dirty = _git("status", "--porcelain", cwd=git_root)
    if dirty:
        err(f"Repository has uncommitted changes: {git_root}")
        err("Commit or stash them before running vibe-tdd with --commit.")
        sys.exit(1)


def _git_commit(source: Path, snippet_label: str, kids: str) -> None:
    """Stage the source file and commit if there are staged changes."""
    try:
        git_root = _git("rev-parse", "--show-toplevel", cwd=str(source.parent))
        try:
            rel = str(source.relative_to(git_root))
        except ValueError:
            warn(f"    {source} is not under git root {git_root} — skipping commit")
            return
        _git("add", rel, cwd=git_root)
    except RuntimeError:
        return

    # git diff --cached --exit-code: exits 0 when nothing staged, 1 when changes exist
    try:
        _git("diff", "--cached", "--exit-code", cwd=git_root)
        return  # nothing staged
    except RuntimeError:
        pass  # staged changes present → proceed

    msg = f"vibe-tdd({kids}): improve {snippet_label}"
    try:
        _git("commit", "-m", msg, cwd=git_root)
        info(f"    committed: {msg}")
    except RuntimeError as e:
        warn(f"    git commit failed: {e}")

# ── Markdown parsing ───────────────────────────────────────────────────────────

FENCE_RE = re.compile(
    r'(?P<fence>`{3,}|~{3,})(?P<lang>[a-zA-Z0-9_+\-]*)[ \t]*\n(?P<code>.*?)(?P=fence)',
    re.DOTALL,
)
HEADING_RE = re.compile(r'^#{1,6}[ \t]+(?P<title>.+)$', re.MULTILINE)
MAX_SECTION_CHARS = 3000


@dataclass
class Snippet:
    skill: str                    # resolved skill name (e.g. "typescript")
    fence_lang: str               # original fence tag (e.g. "ts")
    original_code: str            # code at parse time — never modified
    code: str                     # current code — updated after each improvement
    raw_start: int                # char offset of opening fence in file at parse time
    raw_end: int                  # char offset just after closing fence at parse time
    section: str                  # surrounding section text (read-only context)
    section_heading: str          # nearest heading title, used in commit messages
    improvements: list[tuple[str, str]] = field(default_factory=list)  # [(kid, explanation)]


def _find_section(content: str, fence_start: int) -> tuple[str, str]:
    """Return (section_text, heading_title) for the section containing fence_start."""
    section_start = 0
    heading_title = ""
    for m in HEADING_RE.finditer(content):
        if m.start() < fence_start:
            section_start = m.start()
            heading_title = m.group("title").strip()
        else:
            break

    section_end = len(content)
    for m in HEADING_RE.finditer(content, fence_start + 1):
        section_end = m.start()
        break

    section = content[section_start:section_end].strip()
    if len(section) > MAX_SECTION_CHARS:
        section = section[:MAX_SECTION_CHARS] + "\n… [truncated]"
    return section, heading_title


def parse_snippets(
    content: str,
    skills_root: Path,
    allowed_skills: list[str] | None,
) -> list[Snippet]:
    snippets = []
    for m in FENCE_RE.finditer(content):
        fence_lang = m.group("lang").strip()
        if not fence_lang:
            continue
        skill = FENCE_TO_SKILL.get(fence_lang.lower())
        if skill is None:
            continue
        if allowed_skills and skill not in allowed_skills:
            continue
        if not (skills_root / skill).is_dir():
            continue
        section, heading = _find_section(content, m.start())
        code = m.group("code")
        snippets.append(Snippet(
            skill=skill,
            fence_lang=fence_lang,
            original_code=code,
            code=code,
            raw_start=m.start(),
            raw_end=m.end(),
            section=section,
            section_heading=heading,
        ))
    return snippets

# ── Diff helper ────────────────────────────────────────────────────────────────

def _unified_diff(original: str, current: str, label: str = "snippet") -> str:
    """Return a unified diff string, or empty string if there are no changes."""
    a = original.splitlines(keepends=True)
    b = current.splitlines(keepends=True)
    lines = list(difflib.unified_diff(a, b, fromfile=f"original {label}", tofile=f"current {label}"))
    return "".join(lines)

# ── Prompt building ────────────────────────────────────────────────────────────

def build_prompt(kfile: Path, snippet: Snippet, tmp_json: Path) -> str:
    kid    = knowledge_id(kfile)
    ktitle = knowledge_title(kfile)

    prior_section = ""
    if snippet.code != snippet.original_code:
        diff = _unified_diff(snippet.original_code, snippet.code)
        if diff:
            prior_section = f"""--- CHANGES ALREADY APPLIED TO THIS SNIPPET (by earlier techniques in this run) ---
{diff}
--- END PRIOR CHANGES ---

These changes are settled decisions. Build on them — do not revert or contradict them.

"""

    return f"""You are reviewing a code snippet from a Technical Design Document.
Check whether the knowledge document below applies to the snippet. If it does, suggest an improved version.

Write your result to @{tmp_json} as a single JSON object:
  If the knowledge applies and an improvement is possible:
    {{ "improved": true, "explanation": "<1–2 sentences>", "code": "<improved code>" }}
  Otherwise:
    {{ "improved": false }}

Rules:
1. Only rewrite the code — do NOT modify the surrounding prose.
2. Do NOT include opening or closing fence markers (```) in "code".
3. Keep the original intent and logic intact; apply only what the knowledge prescribes.
4. "explanation" must be concise: state what was applied and why it helps.
5. If the snippet is pseudocode, prose-like, or clearly illustrative, respond {{ "improved": false }}.
6. Write exactly one JSON object to @{tmp_json}. No markdown wrapping.

{prior_section}--- KNOWLEDGE: {kid} · {ktitle} ---
{kfile.read_text(encoding="utf-8")}
--- END KNOWLEDGE ---

--- DOCUMENT SECTION (read-only context) ---
{snippet.section}
--- END SECTION ---

--- CURRENT SNIPPET ({snippet.fence_lang}) ---
{snippet.code}
--- END SNIPPET ---

Write the JSON object to @{tmp_json} now."""

# ── Write-back ─────────────────────────────────────────────────────────────────

def _format_replacement(snippet: Snippet) -> str:
    """Callout with explanation + improved code block, replacing the original fence."""
    kids         = ", ".join(kid for kid, _ in snippet.improvements)
    explanations = " ".join(f"({kid}) {exp}" for kid, exp in snippet.improvements)
    callout      = f"> [!TIP]\n> **vibe-tdd** ({kids}): {explanations}"
    code_block   = f"```{snippet.fence_lang}\n{snippet.code.rstrip()}\n```"
    return f"{callout}\n\n{code_block}"


def write_snippet_back(content: str, snippet: Snippet) -> str:
    """Replace one snippet's fence block in content using its original offsets."""
    replacement = _format_replacement(snippet)
    return content[:snippet.raw_start] + replacement + content[snippet.raw_end:]


def build_summary(snippets: list[Snippet], source_file: Path) -> str:
    """Standalone suggestion report for --output mode."""
    lines: list[str] = [f"# vibe-tdd Suggestions: `{source_file.name}`\n"]
    changed = [s for s in snippets if s.improvements]

    if not changed:
        lines.append("No improvements suggested.")
        return "\n".join(lines)

    lines.append(f"{len(changed)} of {len(snippets)} snippet(s) have suggestions.\n")
    lines.append("> These are suggestions only. The source file has not been modified.\n")

    for i, snippet in enumerate(changed, 1):
        kids    = ", ".join(kid for kid, _ in snippet.improvements)
        heading = f" — _{snippet.section_heading}_" if snippet.section_heading else ""
        lines.append(f"## Snippet {i} — `{snippet.fence_lang}` ({kids}){heading}\n")

        for kid, explanation in snippet.improvements:
            lines.append(f"- **{kid}**: {explanation}")
        lines.append("")

        lines.append("**Original:**")
        lines.append(f"```{snippet.fence_lang}")
        lines.append(snippet.original_code.rstrip())
        lines.append("```\n")

        lines.append("**Suggested:**")
        lines.append(f"```{snippet.fence_lang}")
        lines.append(snippet.code.rstrip())
        lines.append("```\n")

    return "\n".join(lines)

# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="vibe-tdd.py",
        description="AI-driven TDD snippet improvement using vibe-types skill knowledge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python vibe-tdd.py --file design.md
  python vibe-tdd.py --file design.md --skill typescript
  python vibe-tdd.py --file design.md --skill typescript,python --only T01,T13
  python vibe-tdd.py --file design.md --commit
  python vibe-tdd.py --file design.md --output suggestions.md
  python vibe-tdd.py --file design.md --dry-run
""",
    )
    p.add_argument("--file",      metavar="PATH",  required=True,
                   help="Markdown TDD file to process")
    p.add_argument("--skill",     metavar="LANGS",
                   help="Comma-separated skill names (default: all available, e.g. typescript,python)")
    p.add_argument("--skill-dir", metavar="PATH",
                   help="Path to a single custom skill directory (overrides --skill)")
    p.add_argument("--only",      metavar="IDs",
                   help="Comma-separated knowledge IDs to apply (e.g. T01,T13)")
    p.add_argument("--commit",    action="store_true",
                   help="Create a git commit after each improved snippet (in-place mode only)")
    p.add_argument("--output",    metavar="FILE",
                   help="Write a standalone suggestion report to FILE instead of modifying the TDD")
    p.add_argument("--dry-run",   action="store_true",
                   help="Print the processing plan without calling opencode")
    return p.parse_args()

# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()

    source = Path(args.file).resolve()
    if not source.is_file():
        err(f"File not found: {source}")
        sys.exit(1)

    if args.commit and args.output:
        err("--commit and --output are mutually exclusive.")
        sys.exit(1)

    if args.commit and not _in_git_repo():
        err("--commit requires a git repository.")
        sys.exit(1)

    if args.commit:
        _check_clean_tree(source)

    content = source.read_text(encoding="utf-8")

    # ── Resolve skill directories ──────────────────────────────────────────────
    skills_root = SCRIPT_DIR / "plugin" / "skills"

    if args.skill_dir:
        skill_dir_path = Path(args.skill_dir).resolve()
        skill_dirs: dict[str, Path] = {skill_dir_path.name: skill_dir_path}
    elif args.skill:
        requested = [s.strip() for s in args.skill.split(",") if s.strip()]
        skill_dirs = {}
        for name in requested:
            d = skills_root / name
            if d.is_dir():
                skill_dirs[name] = d
            else:
                warn(f"Skill not found: {name}")
        if not skill_dirs:
            available = " ".join(sorted(d.name for d in skills_root.iterdir() if d.is_dir()))
            err(f"No valid skills. Available: {available}")
            sys.exit(1)
    else:
        skill_dirs = {d.name: d for d in skills_root.iterdir() if d.is_dir()}

    allowed_skills = list(skill_dirs.keys())
    only_ids = [i.strip().upper() for i in args.only.split(",")] if args.only else None

    # ── Parse snippets ─────────────────────────────────────────────────────────
    snippets = parse_snippets(content, skills_root, allowed_skills)
    if not snippets:
        log("No processable code snippets found (fences must have a language tag).")
        sys.exit(0)

    # Process last-to-first so original offsets stay valid during in-place writes
    snippets_ordered = sorted(snippets, key=lambda s: s.raw_start, reverse=True)

    log(f"Found {len(snippets)} snippet(s) in {source.name}")

    # ── Load knowledge files per skill ─────────────────────────────────────────
    kfiles_by_skill: dict[str, list[Path]] = {}
    for skill, skill_dir in skill_dirs.items():
        kfiles = load_knowledge_files(skill_dir, only_ids)
        if kfiles:
            kfiles_by_skill[skill] = kfiles

    total_pairs = sum(len(kfiles_by_skill.get(s.skill, [])) for s in snippets)
    for skill, kfiles in sorted(kfiles_by_skill.items()):
        info(f"  {skill}: {len(kfiles)} knowledge file(s)")
    info(f"  Total (knowledge × snippet) pairs: {total_pairs}")
    if args.commit:
        info("  git commits enabled")
    if args.output:
        info(f"  output mode: suggestions → {args.output}")

    if args.dry_run:
        log("Dry run — no opencode calls made")
        for i, snippet in enumerate(snippets, 1):
            kfiles = kfiles_by_skill.get(snippet.skill, [])
            kids   = ", ".join(knowledge_id(k) for k in kfiles)
            heading = f" [{snippet.section_heading}]" if snippet.section_heading else ""
            info(f"  Snippet {i} ({snippet.fence_lang}){heading}: {len(kfiles)} file(s) [{kids}]")
        sys.exit(0)

    # ── Process (knowledge × snippet) pairs ───────────────────────────────────
    stat_oc_failures  = 0
    stat_improvements = 0
    stat_snippets_improved = 0
    stat_committed    = 0

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        for i, snippet in enumerate(snippets_ordered, 1):
            kfiles = kfiles_by_skill.get(snippet.skill, [])
            if not kfiles:
                continue

            # Use document-order index for display
            doc_idx = snippets.index(snippet) + 1
            heading = f" [{snippet.section_heading}]" if snippet.section_heading else ""
            log(f"Snippet {doc_idx}/{len(snippets)} ({snippet.fence_lang}){heading}")

            for kfile in kfiles:
                kid    = knowledge_id(kfile)
                ktitle = knowledge_title(kfile)
                info(f"  {kid} · {ktitle}")

                tmp_json = tmp_path / f"s{doc_idx}-{kid}.json"
                tmp_json.write_text('{"improved": false}', encoding="utf-8")

                oc_exit = run_opencode(build_prompt(kfile, snippet, tmp_json))

                if oc_exit != 0:
                    warn(f"    opencode failed (exit {oc_exit})")
                    stat_oc_failures += 1
                    continue

                try:
                    result = json.loads(tmp_json.read_text(encoding="utf-8"))
                    if not isinstance(result, dict):
                        raise ValueError("expected a JSON object")
                except Exception as e:
                    warn(f"    bad JSON from opencode: {e}")
                    stat_oc_failures += 1
                    continue

                if result.get("improved"):
                    new_code    = str(result.get("code",        "")).strip()
                    explanation = str(result.get("explanation", "")).strip()
                    if new_code and explanation:
                        snippet.code = new_code
                        snippet.improvements.append((kid, explanation))
                        stat_improvements += 1
                        info(f"    ✓ improved")

            # ── Write back this snippet immediately (in-place mode) ────────────
            if snippet.improvements and not args.output:
                content = write_snippet_back(content, snippet)
                source.write_text(content, encoding="utf-8")
                stat_snippets_improved += 1
                info(f"  → written back to {source.name}")

                if args.commit:
                    kids  = ", ".join(kid for kid, _ in snippet.improvements)
                    label = f"{snippet.fence_lang} snippet"
                    if snippet.section_heading:
                        label += f' in "{snippet.section_heading}"'
                    _git_commit(source, label, kids)
                    stat_committed += 1

    # ── Summary mode: write report, do not touch source ───────────────────────
    if args.output:
        # snippets list retains document order; compute improved count from it
        stat_snippets_improved = sum(1 for s in snippets if s.improvements)
        summary = build_summary(snippets, source)
        Path(args.output).write_text(summary, encoding="utf-8")
        log(f"Suggestions written to: {args.output}")

    if not stat_snippets_improved and not args.output:
        log("No improvements found.")

    # ── Stats ──────────────────────────────────────────────────────────────────
    print()
    print(f"  {'Snippets processed:':<32} {len(snippets)}")
    print(f"  {'Snippets improved:':<32} {stat_snippets_improved}")
    print(f"  {'Individual improvements:':<32} {stat_improvements}")
    print(f"  {'opencode failures:':<32} {stat_oc_failures}")
    if args.commit:
        print(f"  {'Commits created:':<32} {stat_committed}")
    print()


if __name__ == "__main__":
    main()
