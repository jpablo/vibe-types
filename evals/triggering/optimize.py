#!/usr/bin/env python3
"""Optimize a vibe-types skill *description* with the real GEPA library.

This is a thin adapter, not a reimplementation: GEPA's `optimize_anything` does
the reflection, mutation, Pareto search, and held-out selection. We only supply
the one project-specific piece GEPA requires — an `evaluator` that scores a
candidate description by actually running `claude -p` triggering (candidate +
isolate mode, via run_triggering.py) and returns a score plus textual side
information (ASI) for GEPA to reflect on.

Modes (per the "optimize anything" blog): we use generalization mode —
`dataset` = train queries, `valset` = held-out queries — so GEPA selects the
description that generalizes, not one overfit to the training phrasings.

Reflection LM: GEPA proposes rewrites with an OpenAI model via LiteLLM, which
reads OPENAI_API_KEY. Put the key in `evals/triggering/.env` (gitignored) as
    OPENAI_API_KEY=sk-...
or export it in your shell. The *task* side (running candidates) stays on your
authenticated `claude -p`, so only reflection needs the OpenAI key.

Run (gepa is pulled ephemerally by uv):
    uv run --no-project --with gepa python evals/triggering/optimize.py --skill typescript
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import run_triggering as T  # noqa: E402

EXEMPLAR_SKILL = "scala3"   # 100% baseline recall — the wording GEPA should emulate
TRAIN_FRAC = 0.6


def load_env(paths: list[Path]) -> None:
    """Minimal .env loader: KEY=VALUE lines, without overriding real env vars."""
    for p in paths:
        if not p.exists():
            continue
        for line in p.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def build_split(skill, queries):
    """skill positives (recall) + `none` near-misses (precision), 60/40 per class."""
    pos = [q for q in queries if q["expected"] == skill]
    neg = [q for q in queries if q["expected"] == T.NONE]
    train, held = [], []
    for group in (pos, neg):
        group = sorted(group, key=lambda q: q["id"])
        cut = max(1, round(len(group) * TRAIN_FRAC))
        train += group[:cut]
        held += group[cut:]
    return train, held


def eval_one(descs, query, runs, model, timeout):
    """Install the 5-skill candidate menu in a temp dir, fire `query` `runs`
    times in isolate mode, return (modal_fired, distribution)."""
    wd = Path(tempfile.mkdtemp(prefix="vt-opt-"))
    try:
        name_to_skill = T.install_menu(wd, descs)
        fired = [T.detect_fired(query, name_to_skill, wd, timeout, model, isolate=True)
                 for _ in range(runs)]
    finally:
        shutil.rmtree(wd, ignore_errors=True)
    tally = Counter(fired)
    return tally.most_common(1)[0][0], dict(tally)


def make_evaluator(skill, base_descs, runs, model, timeout):
    """Return GEPA's evaluator: score one (candidate, query) and emit ASI.

    candidate is {skill: description}; merged over the fixed base for the menu.
    Score: skill query -> 1 if it fires `skill`; non-skill query -> 1 if `skill`
    stays out (recall + precision for the skill being optimized).
    """
    def evaluate(candidate, example=None):
        desc = candidate[skill] if isinstance(candidate, dict) else candidate
        descs = {**base_descs, skill: desc}
        fired, dist = eval_one(descs, example["query"], runs, model, timeout)
        if example["expected"] == skill:
            score = 1.0 if fired == skill else 0.0
            verdict = "correct (triggered)" if score else f"MISS — should trigger {skill}, fired '{fired}'"
        else:
            score = 1.0 if fired != skill else 0.0
            verdict = "correct (stayed out)" if score else f"FALSE FIRE — {skill} triggered on a query it should ignore"
        return score, {"query": example["query"], "expected": example["expected"],
                       "fired": fired, "verdict": verdict, "runs": dist}
    return evaluate


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skill", required=True, choices=T.DEFAULT_SKILLS)
    ap.add_argument("--queries", default=str(Path(__file__).parent / "queries.json"))
    ap.add_argument("--reflection-model", default="openai/gpt-5",
                    help="OpenAI model for GEPA reflection (LiteLLM id). Set to one your key can access.")
    ap.add_argument("--model", default="claude-opus-4-8", help="task model for `claude -p` triggering")
    ap.add_argument("--runs", type=int, default=1, help="trigger runs per query per evaluation")
    ap.add_argument("--max-metric-calls", type=int, default=60, help="GEPA evaluation budget")
    ap.add_argument("--max-workers", type=int, default=4, help="GEPA parallel evaluations")
    ap.add_argument("--timeout", type=int, default=90)
    ap.add_argument("--out", default=str(Path(__file__).parent / "reports"))
    args = ap.parse_args()

    load_env([Path(__file__).parent / ".env", T.REPO_ROOT / ".env"])

    try:
        import gepa.optimize_anything as oa
    except ModuleNotFoundError:
        print("gepa not importable — run via:  uv run --no-project --with gepa python "
              "evals/triggering/optimize.py ...", file=sys.stderr)
        return 2
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set. Put it in evals/triggering/.env (OPENAI_API_KEY=sk-...) "
              "or export it; GEPA's reflection LM needs it.", file=sys.stderr)
        return 2

    skill = args.skill
    queries = json.loads(Path(args.queries).read_text())["queries"]
    base = T.discover_descriptions(T.DEFAULT_SKILLS, {})
    train, held = build_split(skill, queries)
    seed = {skill: base[skill]}

    objective = (f"Improve the `description` of the vibe-types:{skill} skill so Claude loads it for "
                 f"{skill} type-system / compile-time-safety tasks (recall) but stays out of unrelated "
                 f"work (precision). A higher score means more queries are routed correctly.")
    background = (
        "Skill triggering depends ONLY on the skill's name + description; Claude consults a skill "
        "merely from that text, and only for tasks it can't trivially handle itself. A strong "
        "description concretely names the relevant tasks, error messages, tool names and phrasings a "
        "user would actually type, without vague terms that grab unrelated work. Keep it concise "
        f"(2-4 sentences), keep the opening '{skill} ... techniques — ...' shape and a pushy "
        f"'Use this skill whenever ...' clause. A sibling description that triggers reliably, for "
        f"style: {base[EXEMPLAR_SKILL]}")

    evaluator = make_evaluator(skill, base, args.runs, args.model, args.timeout)
    config = oa.GEPAConfig(
        engine=oa.EngineConfig(max_metric_calls=args.max_metric_calls, parallel=True,
                               max_workers=args.max_workers, display_progress_bar=True),
        reflection=oa.ReflectionConfig(reflection_lm=oa.make_litellm_lm(args.reflection_model),
                                       reflection_minibatch_size=3),
    )

    print(f"[gepa optimize_anything] skill={skill} train={len(train)} held={len(held)} "
          f"budget={args.max_metric_calls} reflect={args.reflection_model}", file=sys.stderr)
    result = oa.optimize_anything(seed_candidate=seed, evaluator=evaluator,
                                  dataset=train, valset=held,
                                  objective=objective, background=background, config=config)

    best = getattr(result, "best_candidate", None)
    best_desc = (best.get(skill) if isinstance(best, dict) else best) or base[skill]
    val_raw = getattr(result, "val_aggregate_subscores", None)
    if isinstance(val_raw, (list, tuple)) and val_raw and all(isinstance(x, (int, float)) for x in val_raw):
        val_score = sum(val_raw) / len(val_raw)
    else:
        val_score = val_raw

    ts = time.strftime("%Y-%m-%d_%H%M%S")
    out_dir = Path(args.out) / f"gepa-{skill}-{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "result.json").write_text(json.dumps(
        {"skill": skill, "reflection_model": args.reflection_model, "val_score": val_score,
         "seed_desc": base[skill], "best_desc": best_desc,
         "train_ids": [q["id"] for q in train], "held_ids": [q["id"] for q in held]},
        indent=2, default=str))

    changed = best_desc.strip() != base[skill].strip()
    md = [f"# GEPA description optimization — {skill} — {ts}", "",
          f"- reflection LM: `{args.reflection_model}` · task model: `{args.model}` · "
          f"budget: {args.max_metric_calls} metric calls · runs/query: {args.runs}",
          f"- train: {', '.join(q['id'] for q in train)}",
          f"- held-out: {', '.join(q['id'] for q in held)}",
          f"- GEPA held-out score: {val_score}", "",
          "## Seed description", f"> {base[skill]}", "",
          f"## Best description {'(changed — verify before adopting)' if changed else '(unchanged — GEPA kept the seed)'}",
          f"> {best_desc}", "",
          "Verify before adopting (clean, runs=3):",
          f"  echo '{{\"{skill}\": \"<best>\"}}' > /tmp/cand.json && \\",
          f"  python3 evals/triggering/run_triggering.py --mode candidate --isolate "
          f"--only {skill},none --runs-per-query 3 --descriptions /tmp/cand.json"]
    md = "\n".join(md)
    (out_dir / "report.md").write_text(md)
    print(md)
    print(f"\n[written] {out_dir}/report.md", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
