#!/usr/bin/env python3
"""Layer-2 scorer — the compiler-as-oracle reward for a Rust solution.

A task fixes a public API (names + signatures) but leaves the *representation*
to the model. We score a candidate solution by compiling it against the task's
probes (reusing the rust-project type-checker from verify-markdown-snippets):

  * positive probes — legitimate use that MUST compile (the design supports real
    work); a solution that fails these is broken, not safe.
  * negative/adversarial probes — illegal use that MUST FAIL to compile if the
    invariant is encoded in the types. The fraction correctly rejected is the
    **invariant-enforcement rate** — the headline L2 metric, and the part the
    compiler judges deterministically (it can't be talked into a wrong answer).

Each probe is compiled as `mod sol { <solution> } use sol::*; fn main() { <probe> }`
so module privacy applies (encapsulation probes work) and the probe only sees
the public API. Only hard type/borrow errors count — noise lints are silenced.

Usage:
    python3 score.py tasks/rust/typestate-builder.json --solution sol.rs
    python3 score.py tasks/rust/typestate-builder.json --validate   # check the
        reference good/bad solutions: enforcement(good) must exceed enforcement(bad)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "plugin" / "skills" / "verify-markdown-snippets" / "scripts"))
import verify_rust  # noqa: E402  — reuse the rust-project type-checker


def unwrap_module(src: str) -> str:
    """If the whole solution is wrapped in a single outer `mod NAME { ... }`,
    return its inner body. Models sometimes wrap everything in a named module,
    which would hide the public API behind `sol::NAME::*` and break the probes."""
    s = src.strip()
    m = re.match(r"^(?:\s|//[^\n]*\n|/\*.*?\*/)*(?:pub\s+)?mod\s+\w+\s*\{", s, re.S)
    if not m:
        return src
    open_idx = s.index("{", m.end() - 1)
    depth = 0
    for i in range(open_idx, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return s[open_idx + 1:i] if s[i + 1:].strip() == "" else src
    return src


def compile_unit(solution: str, probe: str) -> tuple[bool, list]:
    """Compile `solution` (as a module) + `probe` (in main). True iff no errors."""
    solution = unwrap_module(solution)
    src = f"#![allow(unused)]\nmod sol {{\n{solution}\n}}\nuse sol::*;\nfn main() {{\n{probe}\n}}\n"
    rustc = verify_rust.verify(src).get("rustc", {})
    errors = rustc.get("errors") or []
    return (bool(rustc.get("ok")) and not errors), errors


def score_solution(task: dict, solution: str) -> dict:
    impl_compiles, impl_errs = compile_unit(solution, "")
    probes = []
    for p in task["probes"]:
        compiled, errs = compile_unit(solution, p["code"])
        correct = compiled if p["kind"] == "pos" else (not compiled)
        probes.append({"name": p["name"], "kind": p["kind"], "invariant": p.get("invariant", ""),
                       "compiled": compiled, "correct": correct})
    pos = [r for r in probes if r["kind"] == "pos"]
    neg = [r for r in probes if r["kind"] == "neg"]
    pos_rate = sum(r["correct"] for r in pos) / len(pos) if pos else None
    neg_rate = sum(r["correct"] for r in neg) / len(neg) if neg else None
    # A solution only "counts" as safe if it compiles and supports legitimate use.
    usable = impl_compiles and (pos_rate == 1.0 if pos else impl_compiles)
    return {
        "impl_compiles": impl_compiles,
        "usable": usable,
        "positive_pass_rate": pos_rate,
        "invariant_enforcement": neg_rate,   # headline metric
        "score": (neg_rate if (usable and neg_rate is not None) else 0.0),
        "probes": probes,
        "impl_errors": [] if impl_compiles else [e.get("message", str(e)) for e in impl_errs][:3],
    }


def load_task(path: Path) -> dict:
    task = json.loads(path.read_text())
    task["_dir"] = path.parent
    return task


def read_ref(task: dict, key: str) -> str | None:
    ref = task.get("reference", {}).get(key)
    if not ref:
        return None
    return (task["_dir"] / ref).read_text()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("task", help="path to a task JSON")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--solution", help="path to a Rust solution file to score")
    g.add_argument("--validate", action="store_true",
                   help="score the task's reference good/bad solutions and check the gap")
    args = ap.parse_args()

    task = load_task(Path(args.task))

    if args.solution:
        res = score_solution(task, Path(args.solution).read_text())
        print(json.dumps(res, indent=2))
        return 0

    # --validate: the reward must rank good above bad, else the task/probes are weak.
    good = read_ref(task, "good")
    bad = read_ref(task, "bad")
    if good is None or bad is None:
        print(f"task {task['id']}: missing reference good/bad", file=sys.stderr)
        return 2
    gr = score_solution(task, good)
    br = score_solution(task, bad)
    print(f"task: {task['id']}  ({task.get('tenet','')})")
    for label, r in (("GOOD", gr), ("BAD", br)):
        print(f"  {label}: impl_compiles={r['impl_compiles']} pos_pass={r['positive_pass_rate']} "
              f"invariant_enforcement={r['invariant_enforcement']} -> score={r['score']:.2f}")
        for p in r["probes"]:
            mark = "ok " if p["correct"] else "XX "
            print(f"      {mark}{p['kind']:3} {p['name']:28} compiled={p['compiled']} ({p['invariant']})")
    ok = (gr["usable"] and gr["score"] > br["score"])
    print(f"  => discriminates: {'YES' if ok else 'NO'} "
          f"(good {gr['score']:.2f} vs bad {br['score']:.2f})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
