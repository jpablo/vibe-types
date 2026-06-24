# vibe-types eval suite

Measures — and optimizes — how effective the language skills actually are. The
key asset this project has that most skill evals lack: **the compiler is a
deterministic oracle for the exact thing the skills teach** ("encode the
invariant in types so bad states don't compile"). Wherever possible the reward
signal is anchored on that, not on an LLM judge.

"Effectiveness" is three distinct questions, each measured differently. Don't
conflate them.

| Layer | Question | How it's measured | Signal | Status |
|------|----------|-------------------|--------|--------|
| **L0 — content correctness** | Do the doc snippets compile / fail for the stated reason? | `verify-markdown-snippets` extracts each fenced block and runs the real compiler/checker | Deterministic | ✅ built (`make verify`, `make verify-<lang>`) |
| **L1 — triggering** | Does the *right* language skill load for a realistic query? | Run real `claude -p` with all five skills competing; score a cross-skill confusion matrix | LLM behavior | ✅ built — [`triggering/`](triggering/) |
| **L2 — behavioral uplift** | Once loaded, does the skill make Claude's code *more type-safe* than a no-skill baseline? | Per-task rollout scored by **compiler + adversarial probes** (invariant-enforcement rate) | Deterministic-anchored | ✅ built (Rust) — [`behavioral/`](behavioral/) |

**L0** is a precondition (a skill full of broken examples can't teach), not a
measure of behavioral effect. **L1** is the cheapest layer and the one a user
notices first — a skill that never loads is useless. **L2** is where the real
value is: it's the only layer that asks whether the guidance *changes the code*.

## L1 — triggering (built)

See [`triggering/README.md`](triggering/README.md). It runs each labelled query
through `claude -p` with all five descriptions in the menu, detects which skill
fires, and scores recall / precision / cross-language-confusion / over-trigger.
Baseline reading (`claude-opus-4-8`): descriptions are well-scoped (≈100%
precision, 0% over-trigger) and fail only by **under-triggering** — partly an
inherent ceiling, because the model self-answers tasks it finds easy. `make
eval-triggering`.

## Optimization — GEPA (real library)

[`triggering/optimize.py`](triggering/optimize.py) drives the real `gepa`
package (`optimize_anything`) to rewrite a skill's `description`. We supply only
the project-specific evaluator (score a candidate by running L1 triggering and
return `(score, side_info)` — the ASI GEPA reflects on); GEPA does the
reflection, mutation, Pareto search, and held-out selection. Reflection runs on
an OpenAI model via LiteLLM (`OPENAI_API_KEY` in `triggering/.env`); the task
side stays on `claude -p`. `make optimize SKILL=<lang>`.

The same evaluator shape is how GEPA will drive **L2** once it exists — there,
the score is the **invariant-enforcement rate**: ship each task with adversarial
mutations (snippets that try to construct an illegal state, skip a case, mutate
a frozen value); if the model encoded the invariant properly the compiler
*rejects* them, if it wrote loose types they compile. The mutation results +
compiler errors are the ASI. GEPA ships a built-in `gskill` harness that
evaluates Claude Code skills on **task correctness** (SWE-bench style) — not
triggering, so nothing to reuse for L1, but it's the reference to build L2 on
(swap their correctness check for the compiler-oracle).

## Choosing the model

Everything model-dependent is parameterized: pick the model per-run with
`MODEL=<id>`, or set it once for the shell with `VT_MODEL=<id>` (default: your
CLI-configured model). This is deliberate — triggering and uplift differ by
model, and you may want to optimize a *smaller* model, not just a frontier one.

```bash
VT_MODEL=claude-haiku-4-5 make eval-all            # L1 + L2 against one model
make eval-behavioral MODEL=claude-sonnet-4-6       # or per-target
make optimize SKILL=python MODEL=claude-haiku-4-5  # optimize a description FOR that model
make optimize-all MODEL=claude-haiku-4-5           # all five descriptions (expensive)
```

The model must be one `claude -p --model` accepts. Only L1/L2 use a model — the
L0 snippet checks (`make verify-*`) are compiler-driven and model-independent.
For optimization, `MODEL` is the model being optimized *for*; the reflection
proposer is separate (`REFLECT=` / `$VT_REFLECTION_MODEL`, default
`openai/gpt-5`) and can stay a strong model even while optimizing a small one.

## Layout

```
evals/
├── README.md         # this file — the three-layer plan
└── triggering/       # L1: cross-skill triggering eval + GEPA description optimizer
    ├── run_triggering.py   # the harness (installed / candidate modes, --isolate)
    ├── optimize.py         # GEPA optimize_anything driver
    ├── queries.json        # labelled query set
    ├── .env.example        # OPENAI_API_KEY for GEPA reflection
    └── README.md
```
