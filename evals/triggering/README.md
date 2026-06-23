# Layer 1 — Triggering eval

Measures whether the **right language skill fires** for a realistic user query,
with all five `vibe-types` language skills competing in the same menu. This is
the cheapest, fastest layer of the eval suite (see [`../README.md`](../README.md)
for the three-layer plan and how this feeds GEPA optimization).

A skill is useless if it never loads. Triggering is decided entirely by the
`name` + `description` in a skill's frontmatter — the rest of the skill is only
read *after* it fires. So this layer scores descriptions, and it is the surface
the optimizer rewrites first.

## What it measures

Every query is labelled with the language skill that *should* fire, or `none`
for a near-miss that should fire nothing. Because all five skills compete at
once, the result is a **confusion matrix** over
`{rust, python, scala3, lean, typescript, none}`:

- **Overall accuracy** — fired skill == expected, across all queries.
- **Cross-language confusion** — a language query fires the *wrong* language
  (e.g. a Scala query firing `rust`). The diagonal is good; off-diagonal between
  two languages is the interesting failure.
- **Under-trigger rate** — a language query fires *nothing* (the model just
  answered). This is real and common; see "Caveats".
- **Over-trigger rate** — a `none` near-miss fires a skill it shouldn't.
- **Per-skill precision / recall / F1.**

Each query runs `--runs-per-query` times (triggering is stochastic); the modal
outcome is the verdict and the per-run spread is recorded in `report.json`.

## Running it

From the repo root:

```bash
# Quick smoke (a few queries, 1 run) — sanity check the pipeline:
python3 evals/triggering/run_triggering.py --only rust,none --limit 4 --runs-per-query 1 --verbose

# Full baseline sweep of the installed skills (52 queries x 3 runs):
make eval-triggering
# or directly, pinning the model to the one you actually run:
python3 evals/triggering/run_triggering.py --runs-per-query 3 --model claude-opus-4-8 --verbose
```

Outputs land in `evals/triggering/reports/<timestamp>/` as `report.md`
(human-readable: headline metrics, confusion matrix, failure list) and
`report.json` (machine-readable, including per-run distributions).

### Useful flags

| flag | purpose |
|---|---|
| `--mode installed` | (default) test the **real** installed `vibe-types:<lang>` skills |
| `--mode candidate` | inject temp skills carrying candidate descriptions (optimizer) |
| `--descriptions f.json` | `{skill: "candidate description"}` to score in candidate mode |
| `--model <id>` | model for `claude -p`; use the one you actually run for fidelity |
| `--runs-per-query N` | runs per query (default 3) — higher N, tighter trigger-rate |
| `--only rust,none` | restrict to certain expected labels |
| `--limit N` | cap query count (smoke tests) |
| `--workers N` | parallel `claude -p` processes (default 8) |

## How it works

`run_triggering.py` shells out to `claude -p <query> --output-format stream-json`
and watches the event stream. The first `Skill`/`Read` tool-use whose input
names a tracked skill is the one that "fired"; we read that *intent* from the
streamed `tool_use` block (which appears before the tool executes) and kill the
process, so no real work runs. This generalises skill-creator's single-skill
trigger eval to N competing skills.

Several non-obvious facts were established empirically while building this (worth
knowing before you change the harness):

- **Inject skills, not commands.** A slash-*command* placed in `.claude/commands/`
  is not auto-invoked by the model; a real skill under `.claude/skills/` is. So
  candidate descriptions are injected as skills.
- **Auth is bound to the default `~/.claude` config.** A fresh `CLAUDE_CONFIG_DIR`
  fails with "Not logged in" (the login token isn't portable), so the harness
  runs under the default config. Consequence: the live menu also contains the
  user's *other* global skills, and in `candidate` mode the **real** vibe-types
  plugin shares the menu with the injected candidates. For a fully clean
  candidate run, temporarily disable the installed `vibe-types` plugin.
- **Parse partial messages carefully.** With `--include-partial-messages`,
  `assistant` events stream incrementally (a text-only partial usually arrives
  first). Concluding "none" from a partial assistant event aborts before the
  skill fires — the detector only treats `result`/`message_stop` as terminal.
- Set `VT_DEBUG_RAW=<dir>` to dump each run's raw stream for debugging.

## The query set (`queries.json`)

```json
{
  "skills": ["rust", "python", "scala3", "lean", "typescript"],
  "queries": [
    {"id": "rs-01", "expected": "rust", "query": "..."},
    {"id": "neg-01", "expected": "none", "note": "why it's a near-miss", "query": "..."}
  ]
}
```

`expected` ∈ the five skills ∪ `none`. Good queries are concrete and realistic
(file paths, casual phrasing, occasional typos) and lean on *implicit* language
signals (`cannot borrow`, `mypy`, `given`, `lake build`, `tsc`) rather than
naming the language. The `none` near-misses are the valuable negatives — they
share vocabulary with type-safety work but need something else (CI, profiling, a
mechanical rename, SQL). Every language positive doubles as a negative for the
other four, so cross-language confusion needs no separate entries.

## Optimizing a description with GEPA (`optimize.py`)

`optimize.py` drives the **real `gepa` library** (`optimize_anything`) — it does
the reflection, mutation, Pareto search, and held-out selection. We supply only
the one project-specific piece GEPA requires: an `evaluator` that scores a
candidate description by running `claude -p` triggering in `candidate + isolate`
mode and returns `(score, side_info)` (the ASI GEPA reflects on). `dataset` =
train queries, `valset` = held-out queries, so GEPA selects wording that
*generalizes*. (GEPA's built-in `gskill` harness evaluates skills on *task
correctness*, not triggering, so there's nothing to reuse for L1 — but it's the
reference to build on for the Layer-2 behavioral eval.)

**API key — where to put it.** GEPA proposes rewrites with an OpenAI model via
LiteLLM, which reads `OPENAI_API_KEY`. Create `evals/triggering/.env`
(gitignored; `optimize.py` auto-loads it):

```
OPENAI_API_KEY=sk-...
```

Only *reflection* uses OpenAI; the task side (running candidates) stays on your
authenticated `claude -p`.

**Run** (gepa + litellm are pulled ephemerally by uv):

```bash
make optimize SKILL=typescript            # or: BUDGET=80 to widen the search
# equivalently:
uv run --no-project --with gepa --with litellm \
  python evals/triggering/optimize.py --skill typescript \
  --reflection-model openai/gpt-5 --max-metric-calls 60
```

Set `--reflection-model` to a model your key can access. The report shows the
seed vs. best description, GEPA's held-out score, and a `--descriptions` command
to re-verify the winner at `runs=3` before you paste it into `SKILL.md`.

## Caveats

- **Under-triggering is real.** The model only consults a skill for tasks it
  can't trivially handle; clear-but-simple queries may fire nothing even with a
  perfect description. Mitigate with substantive queries and multiple runs;
  interpret rates, not single shots.
- **Other global skills compete.** Under the default config the live menu
  includes all your installed skills, so a query can fire a *non*-vibe skill
  (counted as `none` here). That's realistic, but means a low score can reflect
  competition rather than a bad description.
- **Cost.** Triggering queries are detected early and killed (fast). `none` /
  under-triggering queries run a full turn before we can be sure nothing fired,
  so they dominate runtime and token cost. A full 52×3 sweep is ~150 short
  `claude -p` calls.
