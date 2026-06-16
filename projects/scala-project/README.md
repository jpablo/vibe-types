# scala-project — reference environment

Reference sbt build for strongly typed functional Scala 3, with two jobs:

1. **Reference** — the compiler settings, library baseline, and formatting
   config here are the recommended starting point for new projects. Copy
   `build.sbt` and adjust.
2. **Snippet verification** — the `verify-markdown-snippets` skill compiles
   every ` ```scala ` fence in the repo's docs against this project's pinned
   Scala version and dependencies, so documentation code is guaranteed to
   compile.

## Toolchain

| Component | Version | Where pinned |
|-----------|---------|--------------|
| Scala | 3.8.4 | `build.sbt` (`scala3Version`) |
| sbt | 1.12.11 | `project/build.properties` |
| scalafmt | 3.11.1 | `.scalafmt.conf` |

The snippet verifier (`verify_scala.py`) parses the Scala version and
`libraryDependencies` out of `build.sbt`, so this file is the single source of
truth — bump versions here and both sbt and the verifier follow.

## Compiler settings — rationale

Enabled by default:

- `-deprecation`, `-feature`, `-unchecked` — surface everything the compiler
  knows is questionable.
- `-Wsafe-init` — rejects reading fields before they are initialized; closes a
  classic soundness hole in object construction.
- `-Wvalue-discard`, `-Wnonunit-statement` — a discarded non-Unit value is
  almost always a forgotten effect (an un-run `IO`, an ignored `Either`).
  These two flags make "I computed it and dropped it on the floor" a warning.
- `-Wunused:all` — unused imports/locals/privates/params rot fast; keep them out.
- `-new-syntax` — one syntax (significant indentation, `if x then y`), not two.
- `-Werror` — in-tree code must be warning-free. Documentation snippets are
  verified with a relaxed subset (see below) so docs can show unused names etc.

Commented out, recommended once the team opts in:

- `-source:future` — adopt next-version semantics early.
- `-language:strictEquality` — `==` requires `CanEqual` evidence; prevents
  comparing unrelated types (catalog: `T20-equality-safety`).
- `-Yexplicit-nulls` — Java interop results become `T | Null` and the null
  branch must be handled (catalog: `T13-null-safety`).

## How snippet verification uses this project

`verify_scala.py` writes each snippet to `snippet_tmp/_snippet_<id>.scala` and
compiles it with `scala-cli` using:

- the Scala version and dependencies from `build.sbt`, and
- a relaxed flag set: the correctness flags above, minus `-Werror`,
  `-Wunused:all`, and `-new-syntax` (docs legitimately show unused names and
  both syntaxes), plus `-experimental` so catalog entries demonstrating
  experimental features (capture checking, safer exceptions) compile on a
  stable release.

`snippet_tmp/`, `reports/`, and `.scala-build/` are throwaway artifacts and
gitignored.

## Manual usage

```bash
cd projects/scala-project
sbt compile   # verify the reference build itself
sbt test      # run any munit suites under src/test/scala
```
