# Language Context Strategy: Skills vs MCP vs Plugins

## Objective

Bring language-specific guidance into agent context reliably, with low token
cost and minimal manual effort.

## Recommendation

Use a hybrid model, with **skills as the default layer**:

1. Skills for language-specific workflows, heuristics, and coding conventions.
2. MCP servers for large or dynamic context (internal APIs, schemas, changing docs).
3. Plugins/tools for execution and integration (build/test/deploy), not primary knowledge storage.

## Why This Split Works

### Skills (primary)

- Best for stable, reusable language guidance.
- Lightweight and local.
- Easy to structure with progressive disclosure:
  - `SKILL.md` for compact workflow rules.
  - `references/` for deeper material loaded only when needed.
  - `scripts/` for deterministic repeated operations.

### MCP servers (secondary)

- Best when context is too large or changes often.
- Keeps core prompt lean by fetching only relevant slices on demand.
- Useful for cross-repo/internal data that should not be duplicated into skills.

### Plugins/tools (tertiary)

- Best for actions, not memory:
  - run tests
  - call CI/CD
  - interact with external systems
- Keep language decision logic in skills, not scattered in plugins.

## Practical Architecture

1. Create one skill per language:
   - `lang-rust`, `lang-scala3`, `lang-typescript`, `lang-python`, etc.
2. Keep each `SKILL.md` short:
   - decision rules
   - anti-patterns
   - when to consult references
3. Store detailed content in `references/`:
   - edge cases
   - framework-specific notes
   - longer examples
4. Add scripts in `scripts/` for repetitive checks or transformations.
5. Use project-level trigger instructions (`AGENTS.md`/equivalent) to auto-apply the language skill.
6. Add MCP only where docs/data are too large or frequently updated.

## Decision Rules

- If guidance is stable and procedural: use a skill.
- If data is large and changing: use MCP.
- If the need is to execute side effects: use a plugin/tool.
- If unsure: start with a skill, then add MCP for specific high-churn domains.

## Rollout Plan

1. Start with 2-3 high-use languages and ship focused skills.
2. Add project-level trigger rules so skills load automatically by repo language.
3. Track misses (cases where the assistant failed to apply known guidance).
4. Refine skill descriptions and references based on misses.
5. Introduce MCP selectively for large/changing sources.

