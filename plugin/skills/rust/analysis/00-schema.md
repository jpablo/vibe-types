# Rust Analysis Schema

## Goal

Normalize findings from Rust sources into a single format so we can generate:

1. `rust/catalog/*` feature docs.
2. `rust/usecases/*` constraint docs.
3. Cross-references between both sides.

## Source Snapshots

- `rust-by-example`: `/Users/jpablo/GitHub/rust-by-example` @ `5383db524711` (2026-02-16)
- `book`: `/Users/jpablo/GitHub/book` @ `05d114287b7d` (2026-02-03)
- `rust`: `/Users/jpablo/GitHub/rust` @ `59fd4ef94daa` (2026-02-20)

## Record Schema

Each extracted finding should use this shape:

```md
- feature: <short canonical name>
  constraint: <what the compiler enforces>
  source_path: <repo-relative path>
  example_pointer: <section heading or nearby file path>
  confidence: high|medium|low
  notes: <gotcha, scope, or caveat>
```

## Confidence Rules

- `high`: supported by at least one canonical source (`rust` repo docs) and one teaching source (`book` or `rust-by-example`).
- `medium`: supported by one strong source, but not cross-confirmed yet.
- `low`: inferred from secondary material or blocked by missing source data.

## Extraction Rules

- Prefer compile-time constraints over runtime behavior.
- Keep snippets minimal and tied to one enforced property.
- Track unstable/nightly status explicitly when present.
- Prefer stable, cross-source wording when names differ.

## Output Files

- `rust/analysis/10-rbe-findings.md`
- `rust/analysis/11-book-findings.md`
- `rust/analysis/12-rustcore-findings.md`
- `rust/analysis/20-merged-map.md`
- `rust/analysis/30-crossref-plan.md`
- `rust/analysis/40-readiness-report.md`
