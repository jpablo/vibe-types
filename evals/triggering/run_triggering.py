#!/usr/bin/env python3
"""Layer-1 triggering eval for the vibe-types language skills.

Measures *cross-skill* triggering: with all five language-skill descriptions
present at once, does the right one fire for a given query — and does nothing
fire for queries that only *look* type-related?

Two modes (auth is bound to the default ~/.claude config, so we run there):
  * installed (default): detect the *real* `vibe-types:<lang>` skills from the
    live plugin — measures the descriptions users actually have installed.
  * candidate: inject five temp skills (carrying candidate descriptions) into a
    scratch `.claude/skills/` and detect those instead — used by the optimizer
    to score a proposed description. (The installed plugin still shares the
    menu; disable it for a fully clean candidate run — see README.)

Detection (generalises skill-creator's single-skill trigger eval to N skills):
  For each query, run `claude -p <query> --output-format stream-json` and watch
  the stream. The first `Skill`/`Read` tool-use whose input names one of the
  tracked skills is the one that "fired"; if the turn opens with another tool
  (or no tool at all), nothing fired -> "none". We read the *intent* from the
  tool_use block, which streams before the tool executes, so no work runs.
  Each query runs `--runs-per-query` times (triggering is stochastic); the
  modal outcome is the verdict and the per-run spread is reported.

Scoring is a confusion matrix over {rust, python, scala3, lean, typescript,
none}. The diagonal is correct. Off-diagonal between two languages is
cross-language confusion; an expected-"none" query that fires anything is an
over-trigger.

Outputs `report.json` (machine) and `report.md` (human) in --out.

This script is stdlib-only and self-contained — it does not import from the
installed skill-creator plugin, so the eval suite stays vendored in-repo.
"""

from __future__ import annotations

import argparse
import json
import os
import select
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import uuid
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SKILLS = ["rust", "python", "scala3", "lean", "typescript"]
NONE = "none"
CMD_PREFIX = "vt-trig"  # filesystem-safe injected-skill name prefix

# Disable the installed vibe-types plugin for the run so only injected
# candidates compete (no installed "twin" stealing triggers). Surgical: keeps
# auth and every other global skill as realistic competition. The plugin id is
# from ~/.claude/settings.json `enabledPlugins`; change here if yours differs.
ISOLATE_PLUGIN_ID = "vibe-types@vibe-types-marketplace"
ISOLATE_SETTINGS = json.dumps({"enabledPlugins": {ISOLATE_PLUGIN_ID: False}})


# --------------------------------------------------------------------------- #
# Skill discovery
# --------------------------------------------------------------------------- #
def parse_skill_description(skill_md: Path) -> str:
    """Return the `description:` value from a SKILL.md frontmatter block.

    Handles both a single-line scalar and YAML block scalars (>, |, >-, |-).
    """
    lines = skill_md.read_text().split("\n")
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{skill_md}: missing opening frontmatter '---'")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise ValueError(f"{skill_md}: missing closing frontmatter '---'")

    fm = lines[1:end]
    i = 0
    while i < len(fm):
        line = fm[i]
        if line.startswith("description:"):
            value = line[len("description:"):].strip()
            if value in (">", "|", ">-", "|-"):
                cont = []
                i += 1
                while i < len(fm) and (fm[i].startswith("  ") or fm[i].startswith("\t")):
                    cont.append(fm[i].strip())
                    i += 1
                return " ".join(cont)
            return value.strip('"').strip("'")
        i += 1
    raise ValueError(f"{skill_md}: no description field")


def discover_descriptions(skills: list[str], overrides: dict[str, str]) -> dict[str, str]:
    """Map each skill -> description, letting `overrides` replace any of them.

    Overrides exist so the optimization loop (GEPA / run_loop) can test a
    *candidate* description without touching the installed skill.
    """
    out: dict[str, str] = {}
    for skill in skills:
        if skill in overrides:
            out[skill] = overrides[skill]
            continue
        skill_md = REPO_ROOT / "plugin" / "skills" / skill / "SKILL.md"
        if not skill_md.exists():
            raise FileNotFoundError(f"no SKILL.md for skill '{skill}' at {skill_md}")
        out[skill] = parse_skill_description(skill_md)
    return out


# --------------------------------------------------------------------------- #
# Menu installation (isolated temp cwd)
# --------------------------------------------------------------------------- #
def install_menu(workdir: Path, descriptions: dict[str, str]) -> dict[str, str]:
    """Install each candidate as a real skill under `workdir/.claude/skills/`.

    `claude -p` discovers project-level skills here and invokes the relevant one
    via the `Skill` tool — which is what we detect. The injected name embeds a
    per-run batch id so it can't collide with anything else in the menu.

    Returns a map of injected skill-name -> language skill, for attribution.
    """
    skills_dir = workdir / ".claude" / "skills"
    batch = uuid.uuid4().hex[:8]
    name_to_skill: dict[str, str] = {}
    for skill, desc in descriptions.items():
        clean = f"{CMD_PREFIX}-{skill}-{batch}"
        sk = skills_dir / clean
        sk.mkdir(parents=True, exist_ok=True)
        indented = "\n  ".join(desc.split("\n"))
        (sk / "SKILL.md").write_text(
            f"---\nname: {clean}\ndescription: |\n  {indented}\n---\n\n"
            f"# {skill}\n\nGuidance for {skill} type-safety tasks.\n"
        )
        name_to_skill[clean] = skill
    return name_to_skill


# --------------------------------------------------------------------------- #
# Single-query trigger detection
# --------------------------------------------------------------------------- #
def detect_fired(
    query: str,
    patterns: dict[str, str],
    workdir: Path,
    timeout: int,
    model: str | None,
    isolate: bool = False,
) -> str:
    """Run one `claude -p` and return which skill fired, or NONE.

    `patterns` maps a substring (e.g. "vibe-types:rust" or an injected skill
    name) to the language it attributes to. The first such substring to appear
    in a Skill/Read tool input wins. Faithful to skill-creator's stream parsing,
    generalised to N skills: we read the model's *intent* from the tool_use
    block (which streams before the tool executes), so no real work runs.
    """
    cmd = [
        "claude", "-p", query,
        "--output-format", "stream-json",
        "--verbose",
        "--include-partial-messages",
    ]
    if model:
        cmd += ["--model", model]
    if isolate:
        cmd += ["--settings", ISOLATE_SETTINGS]

    # Run under the default (authenticated) config. Strip CLAUDECODE so claude
    # -p can nest inside an interactive Claude Code session.
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    proc = subprocess.Popen(
        cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, cwd=str(workdir), env=env,
    )

    _dbg = os.environ.get("VT_DEBUG_RAW")
    _dbgf = open(Path(_dbg) / f"raw-{proc.pid}.jsonl", "w") if _dbg else None

    def match(blob: str) -> str | None:
        for pat, skill in patterns.items():
            if pat in blob:
                return skill
        return None

    start = time.time()
    buffer = ""
    pending = False          # inside a Skill/Read tool_use block
    acc = ""                 # accumulated tool input json
    try:
        while time.time() - start < timeout:
            if proc.poll() is not None:
                rest = proc.stdout.read()
                if rest:
                    dec = rest.decode("utf-8", errors="replace")
                    buffer += dec
                    if _dbgf:
                        _dbgf.write(dec)
                # fall through to drain remaining lines below
            else:
                ready, _, _ = select.select([proc.stdout], [], [], 1.0)
                if not ready:
                    continue
                chunk = os.read(proc.stdout.fileno(), 8192)
                if not chunk:
                    if proc.poll() is not None:
                        pass
                    else:
                        continue
                dec = chunk.decode("utf-8", errors="replace")
                buffer += dec
                if _dbgf:
                    _dbgf.write(dec)

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                etype = event.get("type")
                if etype == "stream_event":
                    se = event.get("event", {})
                    st = se.get("type", "")
                    if st == "content_block_start":
                        cb = se.get("content_block", {})
                        if cb.get("type") == "tool_use":
                            if cb.get("name", "") in ("Skill", "Read"):
                                pending, acc = True, ""
                                hit = match(json.dumps(cb.get("input", {})))
                                if hit:
                                    return hit
                            else:
                                return NONE  # turn opened with an unrelated tool
                    elif st == "content_block_delta" and pending:
                        delta = se.get("delta", {})
                        if delta.get("type") == "input_json_delta":
                            acc += delta.get("partial_json", "")
                            hit = match(acc)
                            if hit:
                                return hit
                    elif st in ("content_block_stop", "message_stop"):
                        if pending:
                            return match(acc) or NONE
                        if st == "message_stop":
                            return NONE
                elif etype == "assistant":
                    # Under --include-partial-messages these arrive incrementally
                    # (often a text-only partial first). Only act on a Skill/Read
                    # match; never conclude "none" here — that is what the
                    # terminal `result`/`message_stop` events are for.
                    for item in event.get("message", {}).get("content", []):
                        if item.get("type") == "tool_use" and item.get("name", "") in ("Skill", "Read"):
                            hit = match(json.dumps(item.get("input", {})))
                            if hit:
                                return hit
                elif etype == "result":
                    return NONE

            if proc.poll() is not None and "\n" not in buffer:
                break
        return NONE
    finally:
        if _dbgf:
            _dbgf.close()
        if proc.poll() is None:
            proc.kill()
            proc.wait()


# --------------------------------------------------------------------------- #
# Eval driver
# --------------------------------------------------------------------------- #
def run_eval(
    queries: list[dict],
    skills: list[str],
    mode: str,
    descriptions: dict[str, str],
    runs_per_query: int,
    workers: int,
    timeout: int,
    model: str | None,
    verbose: bool,
    isolate: bool = False,
) -> list[dict]:
    """Run every (query, run) and return per-query records with modal verdict."""
    workdir = Path(tempfile.mkdtemp(prefix="vt-trig-work-"))
    try:
        if mode == "candidate":
            patterns = install_menu(workdir, descriptions)        # injected name -> lang
        else:  # "installed": detect the real plugin skills in the live menu
            patterns = {f"vibe-types:{s}": s for s in skills}

        jobs = [(q, r) for q in queries for r in range(runs_per_query)]
        outcomes: dict[str, list[str]] = {q["id"]: [] for q in queries}

        def task(q: dict) -> tuple[str, str]:
            return q["id"], detect_fired(q["query"], patterns, workdir, timeout, model, isolate)

        done = 0
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(task, q): (q, r) for q, r in jobs}
            for fut in as_completed(futs):
                q, _ = futs[fut]
                try:
                    qid, fired = fut.result()
                except Exception as e:  # noqa: BLE001 — a crashed run counts as "none"
                    print(f"warn: query {q['id']} run failed: {e}", file=sys.stderr)
                    qid, fired = q["id"], NONE
                outcomes[qid].append(fired)
                done += 1
                if verbose:
                    print(f"  [{done}/{len(jobs)}] {qid} -> {fired}", file=sys.stderr)

        by_id = {q["id"]: q for q in queries}
        records = []
        for qid, fired_list in outcomes.items():
            q = by_id[qid]
            tally = Counter(fired_list)
            modal = tally.most_common(1)[0][0]
            records.append({
                "id": qid,
                "query": q["query"],
                "expected": q["expected"],
                "note": q.get("note", ""),
                "fired": modal,
                "correct": modal == q["expected"],
                "runs": len(fired_list),
                "distribution": dict(tally),
            })
        return records
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #
def score(records: list[dict], skills: list[str]) -> dict:
    labels = skills + [NONE]
    matrix = {exp: {fired: 0 for fired in labels} for exp in labels}
    for r in records:
        matrix[r["expected"]][r["fired"]] += 1

    per_skill = {}
    for s in skills:
        tp = matrix[s][s]
        fn = sum(matrix[s][f] for f in labels if f != s)         # expected s, fired other
        fp = sum(matrix[e][s] for e in labels if e != s)         # expected other, fired s
        per_skill[s] = {
            "recall": tp / (tp + fn) if (tp + fn) else None,     # of true-s queries, fired s
            "precision": tp / (tp + fp) if (tp + fp) else None,  # of fired-s, were true s
            "support": tp + fn,
        }
        p, rc = per_skill[s]["precision"], per_skill[s]["recall"]
        per_skill[s]["f1"] = (2 * p * rc / (p + rc)) if (p and rc) else 0.0

    lang_records = [r for r in records if r["expected"] != NONE]
    none_records = [r for r in records if r["expected"] == NONE]
    cross = sum(1 for r in lang_records if r["fired"] != r["expected"] and r["fired"] != NONE)
    miss = sum(1 for r in lang_records if r["fired"] == NONE)
    over = sum(1 for r in none_records if r["fired"] != NONE)

    total = len(records)
    correct = sum(1 for r in records if r["correct"])
    return {
        "overall_accuracy": correct / total if total else None,
        "correct": correct,
        "total": total,
        "language_accuracy": (
            sum(1 for r in lang_records if r["correct"]) / len(lang_records)
            if lang_records else None
        ),
        "cross_language_confusion_rate": cross / len(lang_records) if lang_records else None,
        "under_trigger_rate": miss / len(lang_records) if lang_records else None,
        "over_trigger_rate": over / len(none_records) if none_records else None,
        "per_skill": per_skill,
        "confusion_matrix": matrix,
        "labels": labels,
    }


def render_markdown(meta: dict, scored: dict, records: list[dict]) -> str:
    labels = scored["labels"]
    L = [f"# Triggering eval — {meta['timestamp']}", ""]
    L.append(f"- mode: **{meta.get('mode', 'installed')}**  ·  model: `{meta['model']}`  ·  "
             f"runs/query: {meta['runs_per_query']}  ·  queries: {scored['total']}")
    L.append("")
    L.append("## Headline metrics")
    L.append("")
    def pct(x): return "—" if x is None else f"{x*100:.0f}%"
    L.append(f"- **Overall accuracy** (fired == expected): **{pct(scored['overall_accuracy'])}** ({scored['correct']}/{scored['total']})")
    L.append(f"- Language accuracy (right language wins): {pct(scored['language_accuracy'])}")
    L.append(f"- Cross-language confusion (wrong language fires): {pct(scored['cross_language_confusion_rate'])}")
    L.append(f"- Under-trigger (language query → nothing fires): {pct(scored['under_trigger_rate'])}")
    L.append(f"- Over-trigger (none-query → something fires): {pct(scored['over_trigger_rate'])}")
    L.append("")
    L.append("## Per-skill precision / recall / F1")
    L.append("")
    L.append("| skill | recall | precision | F1 | support |")
    L.append("|---|---|---|---|---|")
    for s, m in scored["per_skill"].items():
        L.append(f"| {s} | {pct(m['recall'])} | {pct(m['precision'])} | {m['f1']:.2f} | {m['support']} |")
    L.append("")
    L.append("## Confusion matrix (rows = expected, cols = fired)")
    L.append("")
    L.append("| expected ↓ / fired → | " + " | ".join(labels) + " |")
    L.append("|" + "---|" * (len(labels) + 1))
    for exp in labels:
        row = [f"**{exp}**"] + [str(scored["confusion_matrix"][exp][f]) for f in labels]
        L.append("| " + " | ".join(row) + " |")
    L.append("")
    L.append("## Failures (modal verdict ≠ expected)")
    L.append("")
    fails = [r for r in records if not r["correct"]]
    if not fails:
        L.append("None — every query produced its expected verdict. 🎉")
    for r in fails:
        L.append(f"- `{r['id']}` expected **{r['expected']}**, fired **{r['fired']}** "
                 f"`{r['distribution']}`{(' — ' + r['note']) if r['note'] else ''}")
        L.append(f"  > {r['query']}")
    L.append("")
    return "\n".join(L)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--queries", default=str(Path(__file__).parent / "queries.json"))
    ap.add_argument("--out", default=str(Path(__file__).parent / "reports"))
    ap.add_argument("--model", default=None, help="model for `claude -p` (default: your configured model)")
    ap.add_argument("--runs-per-query", type=int, default=3)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--timeout", type=int, default=60, help="seconds per query")
    ap.add_argument("--only", default=None, help="comma-separated expected labels to keep (e.g. rust,none)")
    ap.add_argument("--limit", type=int, default=None, help="cap number of queries (smoke test)")
    ap.add_argument("--mode", choices=["installed", "candidate"], default="installed",
                    help="installed: test the real plugin skills (default). "
                         "candidate: inject temp skills carrying candidate descriptions.")
    ap.add_argument("--isolate", action="store_true",
                    help="disable the installed vibe-types plugin (via --settings) so only "
                         "injected candidates compete — clean room for candidate mode")
    ap.add_argument("--descriptions", default=None,
                    help="JSON file mapping skill -> candidate description "
                         "(candidate mode; overrides the installed SKILL.md text)")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    spec = json.loads(Path(args.queries).read_text())
    skills = spec.get("skills", DEFAULT_SKILLS)
    queries = spec["queries"]
    if args.only:
        keep = set(args.only.split(","))
        queries = [q for q in queries if q["expected"] in keep]
    if args.limit:
        queries = queries[: args.limit]

    overrides = json.loads(Path(args.descriptions).read_text()) if args.descriptions else {}
    descriptions = discover_descriptions(skills, overrides)

    ts = time.strftime("%Y-%m-%d_%H%M%S")
    if args.verbose:
        print(f"[{args.mode}] {len(queries)} queries x {args.runs_per_query} runs "
              f"({args.model or 'default model'})...", file=sys.stderr)

    if args.isolate and args.mode == "installed":
        print("warning: --isolate disables the very plugin installed mode tests; "
              "use it with --mode candidate.", file=sys.stderr)
    records = run_eval(queries, skills, args.mode, descriptions, args.runs_per_query,
                       args.workers, args.timeout, args.model, args.verbose, args.isolate)
    scored = score(records, skills)
    meta = {"timestamp": ts, "mode": args.mode, "model": args.model or "default",
            "runs_per_query": args.runs_per_query, "skills": skills,
            "isolate": args.isolate, "overrides": sorted(overrides.keys())}

    out_dir = Path(args.out) / ts
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(json.dumps(
        {"meta": meta, "score": scored, "records": records}, indent=2))
    md = render_markdown(meta, scored, records)
    (out_dir / "report.md").write_text(md)

    print(md)
    print(f"\n[written] {out_dir}/report.json  and  report.md", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
