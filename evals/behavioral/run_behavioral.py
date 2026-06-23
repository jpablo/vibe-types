#!/usr/bin/env python3
"""Layer-2 behavioral eval — does the loaded skill make Claude's Rust more type-safe?

For each task we run `claude -p` twice: WITH the Rust skill injected (and the
installed plugin isolated out) and WITHOUT any skill (baseline). Each rollout
must write `solution.rs`; we score it with the compiler-oracle (score.py) and
report the **invariant-enforcement** delta (with-skill minus baseline) — the
fraction of adversarial probes the model's design makes the compiler reject.

This isolates *content* effect, not triggering: with-skill rollouts are told the
skill is available and to apply it (L1 already measures whether it triggers).

Run:
    python3 run_behavioral.py --runs 3 --model claude-opus-4-8 --verbose
    python3 run_behavioral.py --task typestate-builder --runs 1   # one task, smoke
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from statistics import mean, pstdev

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
import score as S  # noqa: E402

RUST_SKILL = REPO / "plugin" / "skills" / "rust"
TASKS_DIR = HERE / "tasks" / "rust"
# Disable the installed vibe-types plugin so the WITH condition uses only our
# injected copy and the WITHOUT condition has no vibe-types skill at all.
ISOLATE_SETTINGS = json.dumps({"enabledPlugins": {"vibe-types@vibe-types-marketplace": False}})

CAPTURE = ("\n\nWrite your final solution to a file named `solution.rs` in the current "
           "directory, containing only the Rust module body (no `fn main`, no tests, no prose).")
WITH_PREFIX = ("You have a Rust type-safety skill available in this project (under .claude/skills). "
               "Consult it and apply its guidance.\n\n")


def inject_skill(workdir: Path) -> None:
    dst = workdir / ".claude" / "skills" / "vibe-types-rust"
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copytree(RUST_SKILL, dst, dirs_exist_ok=True)


def extract_code(text: str) -> str | None:
    blocks = re.findall(r"```(?:rust|rs)?\s*\n(.*?)```", text or "", re.S)
    return blocks[-1] if blocks else None


def rollout(task: dict, with_skill: bool, model: str | None, timeout: int) -> str:
    """Run one claude -p and return the captured solution source ('' on failure)."""
    wd = Path(tempfile.mkdtemp(prefix="vt-l2-"))
    try:
        prompt = task["prompt"] + CAPTURE
        if with_skill:
            inject_skill(wd)
            prompt = WITH_PREFIX + prompt
        cmd = ["claude", "-p", prompt, "--dangerously-skip-permissions",
               "--settings", ISOLATE_SETTINGS]
        if model:
            cmd += ["--model", model]
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
        try:
            proc = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True,
                                  text=True, cwd=str(wd), env=env, timeout=timeout)
        except subprocess.TimeoutExpired:
            return ""
        sol = wd / "solution.rs"
        if sol.exists() and sol.read_text().strip():
            return sol.read_text()
        return extract_code(proc.stdout) or ""
    finally:
        shutil.rmtree(wd, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", default=None, help="only this task id (default: all in tasks/rust/)")
    ap.add_argument("--runs", type=int, default=3, help="rollouts per (task, condition)")
    ap.add_argument("--model", default="claude-opus-4-8")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=240, help="seconds per rollout")
    ap.add_argument("--out", default=str(HERE / "reports"))
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    task_files = sorted(TASKS_DIR.glob("*.json"))
    tasks = [S.load_task(f) for f in task_files]
    if args.task:
        tasks = [t for t in tasks if t["id"] == args.task]
    if not tasks:
        print("no matching tasks", file=sys.stderr)
        return 2

    # 1) Roll out in parallel (claude -p is the slow part).
    jobs = [(t, cond, r) for t in tasks for cond in (True, False) for r in range(args.runs)]
    solutions: dict[tuple, str] = {}
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(rollout, t, cond, args.model, args.timeout): (t["id"], cond, r)
                for (t, cond, r) in jobs}
        for fut in as_completed(futs):
            tid, cond, r = futs[fut]
            try:
                solutions[(tid, cond, r)] = fut.result()
            except Exception as e:  # noqa: BLE001
                print(f"warn: rollout {tid}/{cond}/{r} failed: {e}", file=sys.stderr)
                solutions[(tid, cond, r)] = ""
            done += 1
            if args.verbose:
                got = bool(solutions[(tid, cond, r)].strip())
                print(f"  [{done}/{len(jobs)}] {tid} {'with' if cond else 'base'} run{r}: "
                      f"{'captured' if got else 'NO SOLUTION'}", file=sys.stderr)

    # 2) Score sequentially (the rust type-checker serializes on the cargo lock anyway).
    by_task = {}
    for t in tasks:
        rec = {"with": [], "without": []}
        for cond, key in ((True, "with"), (False, "without")):
            for r in range(args.runs):
                sol = solutions.get((t["id"], cond, r), "")
                if not sol.strip():
                    rec[key].append({"usable": False, "invariant_enforcement": None, "score": 0.0, "captured": False})
                    continue
                sc = S.score_solution(t, sol)
                sc["captured"] = True
                rec[key].append(sc)
        by_task[t["id"]] = rec

    # 3) Aggregate + report.
    def agg(runs):
        enf = [x["invariant_enforcement"] for x in runs if x.get("usable") and x["invariant_enforcement"] is not None]
        return {
            "n": len(runs),
            "captured": sum(1 for x in runs if x.get("captured")),
            "usable": sum(1 for x in runs if x.get("usable")),
            "enforcement_mean": mean(enf) if enf else 0.0,
            "enforcement_stdev": pstdev(enf) if len(enf) > 1 else 0.0,
        }

    ts = time.strftime("%Y-%m-%d_%H%M%S")
    lines = [f"# Behavioral (L2) eval — Rust — {ts}",
             f"- model: `{args.model}` · runs/condition: {args.runs} · tasks: {len(tasks)}",
             "", "## Invariant-enforcement: with-skill vs baseline", "",
             "| task | baseline | with-skill | delta | usable (with/base) |",
             "|---|---|---|---|---|"]
    summary = {}
    for t in tasks:
        w = agg(by_task[t["id"]]["with"])
        b = agg(by_task[t["id"]]["without"])
        delta = w["enforcement_mean"] - b["enforcement_mean"]
        summary[t["id"]] = {"with": w, "without": b, "delta": delta}
        lines.append(f"| {t['id']} | {b['enforcement_mean']*100:.0f}% (±{b['enforcement_stdev']*100:.0f}) "
                     f"| {w['enforcement_mean']*100:.0f}% (±{w['enforcement_stdev']*100:.0f}) "
                     f"| **{delta*100:+.0f}pp** | {w['usable']}/{w['n']} · {b['usable']}/{b['n']} |")
    overall_w = mean([summary[t["id"]]["with"]["enforcement_mean"] for t in tasks])
    overall_b = mean([summary[t["id"]]["without"]["enforcement_mean"] for t in tasks])
    lines += ["", f"**Overall invariant-enforcement: baseline {overall_b*100:.0f}% → "
              f"with-skill {overall_w*100:.0f}% ({(overall_w-overall_b)*100:+.0f}pp)**", ""]

    out_dir = Path(args.out) / ts
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(json.dumps(
        {"meta": {"timestamp": ts, "model": args.model, "runs": args.runs},
         "summary": summary,
         "runs": {tid: {k: [{kk: vv for kk, vv in x.items() if kk != "solution"} for x in v]
                        for k, v in rec.items()} for tid, rec in by_task.items()}}, indent=2, default=str))
    md = "\n".join(lines)
    (out_dir / "report.md").write_text(md)
    print(md)
    print(f"\n[written] {out_dir}/report.md", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
