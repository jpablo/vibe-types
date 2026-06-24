# Layer 2 — Behavioral uplift (Rust)

Asks the question the other layers can't: **once the skill is loaded, does it
make Claude's code more type-safe than a no-skill baseline?** The reward is the
**compiler as oracle** — deterministic, and impossible to talk into a wrong
answer, which is exactly what an LLM judge can't promise.

## How a task is scored (the compiler-oracle)

Each task fixes a small **public API** (type/function names + signatures) but
leaves the *representation* to the model. We then compile the model's solution
against fixed probes (reusing the rust-project type-checker from
`verify-markdown-snippets`):

- **positive probes** — legitimate use that MUST compile. A solution that fails
  these is broken, not safe.
- **negative / adversarial probes** — illegal use that MUST FAIL to compile *if
  the invariant is encoded in the types*. The fraction correctly rejected is the
  **invariant-enforcement rate** — the headline metric.

Each probe compiles as `mod sol { <solution> } use sol::*; fn main() { <probe> }`,
so module privacy applies and the probe only sees the public API. `score.py`
runs this; `score.py <task> --validate` checks a task's reference good/bad
solutions discriminate (enforcement(good) > enforcement(bad)) — a no-model-spend
sanity check that the probes actually measure something. Both seed tasks
discriminate 1.00 vs 0.00.

## Two design rules (learned the hard way)

1. **Invariants must live on the public surface**, or probes become
   solution-dependent. Type confusion (newtypes), typestate transitions, and
   totality (does the return type force handling the empty case?) are
   probe-able with solution-agnostic names. "Illegal states unrepresentable"
   (enum vs wide-struct) is *internal* once fields are private — externally
   indistinguishable — so it's a poor L2 probe.
2. **Prompts must be NEUTRAL** — state the domain, never the type-level
   solution. A prescriptive prompt ("make `build()` before `url()` a compile
   error") is aced by baseline Opus and measures nothing; the prompt did the
   skill's job. State only "url is required, method is optional" and let the
   probe detect whether the skill disposed Claude toward typestate.

## The eval (with-skill vs baseline)

`run_behavioral.py` runs each task through `claude -p` twice: **with** the Rust
skill injected (`.claude/skills/`, installed plugin isolated out) and told to
apply it, and **without** any skill (baseline). Each rollout writes
`solution.rs`; we score it and report the invariant-enforcement **delta**. This
isolates *content* effect — L1 already measures whether the skill triggers, so
here we force it in and ask whether its guidance changes the code.

```bash
python3 evals/behavioral/score.py tasks/rust/typestate-builder.json --validate   # no spend
make eval-behavioral RUNS=3                       # with/without rollouts (your configured model)
make eval-behavioral TASK=typestate-builder RUNS=1
```

## Backends: Claude agent vs vLLM / any OpenAI-compatible model

L2 is backend-pluggable, so you can measure (and later optimize) skills for **any
model**, including smaller ones served by vLLM:

- **`claude` (default)** — `claude -p` agent. The skill is injected as real files
  under `.claude/skills/`, so the agent reads `SKILL.md` and navigates the
  catalog/usecases on demand (full progressive disclosure).
- **`openai`** — one chat completion against any OpenAI-compatible endpoint (vLLM,
  OpenAI, etc.) via LiteLLM. There's no agentic skill-loading, so the WITH
  condition **inlines the `SKILL.md` body** into the system prompt — the
  closest faithful equivalent (the model can't open the catalog files).

```bash
# vLLM (OpenAI-compatible server):
make eval-behavioral BACKEND=openai MODEL=openai/Qwen2.5-Coder-7B-Instruct \
     API_BASE=http://your-vllm-host:8000/v1 RUNS=3
# (vLLM ignores the key; set VT_API_KEY if your gateway needs one.)

# A hosted OpenAI model (api-base defaults to OpenAI; key from .env / $OPENAI_API_KEY):
make eval-behavioral BACKEND=openai MODEL=gpt-4o-mini RUNS=3
```

Set the model with `MODEL=`/`$VT_MODEL`, the endpoint with `API_BASE=`/`$VT_API_BASE`,
and the key with `$VT_API_KEY` (or `$OPENAI_API_KEY`). **L1 triggering is
Claude-only** — autonomous skill-loading is a Claude Code mechanism a raw chat
model has no equivalent for; only L2 is backend-pluggable.

## Honest caveat

Opus 4.8 is a strong baseline — on simple tasks it often writes the type-safe
version unprompted (e.g. it returned `Option` for `safe_div` even under a
prescriptive prompt). So uplift is task-dependent and may be subtle; the value
of these skills is likely consistency and reach on harder/less-obvious problems,
not a dramatic delta on toy tasks. The harness measures whatever the truth is.

Smaller models flip this. gpt-4o-mini (openai backend) wrote a runtime-checked
builder both with and without the skill — 0% → 0% on typestate — so the reward
is **not saturated** for weaker models. That's exactly where optimizing the
skill *body* has a gradient to climb, which is the motivation for running this
against vLLM-served models.

## Where this is going

This is the reward GEPA optimizes next: the same `evaluate → (score, ASI)` shape
as L1, but the ASI is the compiler errors from the adversarial probes + a diff
vs. the reference — a far richer gradient than triggering. GEPA's built-in
`gskill` harness (install skill → run `claude -p task` → check a correctness
harness) is the structural reference; we swap its correctness check for this
compiler-oracle. The candidate to optimize is the skill *body* (tenets, the
relevant `usecases/` / `catalog/` entries), not just the description.

## Layout

```
behavioral/
├── score.py            # compiler-oracle scorer (+ --validate self-test)
├── run_behavioral.py   # with-skill vs baseline rollouts
└── tasks/rust/
    ├── <task>.json     # prompt (neutral) + positive/negative probes + reference pointers
    └── fixtures/       # reference good/bad solutions (docs + scorer self-test)
```
