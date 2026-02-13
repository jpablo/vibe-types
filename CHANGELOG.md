# Changelog

All notable changes to this guide are documented here.

Format: each entry records the date, the Scala version (if applicable), and what changed.

---

## 2026-02-13 — Multi-language restructure

- Renamed project from `scala3-type-guide` to `vibe-types`
- Moved Scala 3 content into `scala3/` subdirectory (`catalog/`, `usecases/`)
- Created `scala3/README.md` as the Scala 3 landing page
- Rewrote root `README.md` as a multi-language hub
- Added placeholder directories for TypeScript, Rust, Python, Haskell, and Lean
- Fixed internal links after directory restructure

---

## 2026-02-08 — Initial release

- Created complete guide with 44 documents
- Feature Catalog: 23 documents covering all Scala 3 type system features
- Use-Case Index: 15 documents mapping constraints to features
- Appendix: glossary (40+ terms), feature matrix (23×15), further reading
- Added Scala version annotations to all catalog documents

### Version coverage

Features documented as of this release:

| Scala Version | Features |
|---------------|----------|
| 3.0 | Union/intersection types, type lambdas, match types, dependent/polymorphic function types, givens/using, context functions/bounds, extension methods, type class derivation, multiversal equality, conversions, enums/ADTs/GADTs, opaque types, open/export/transparent, matchable/TypeTest, structural/refined types, kind polymorphism, inline/compiletime, macros, explicit nulls (experimental), erased definitions (experimental) |
| 3.2 | Capture checking (experimental) |
| 3.4 | `open` class warning becomes default |
| 3.5 | Given disambiguation rule 9 (most-general preference) |
| 3.6 | New given syntax (`[T] => ...`), named context bounds (`as`), aggregate bounds (`{Ord, Show}`), context bounds on type members and polymorphic functions, deferred givens |
| 3.7 | Named tuples |
| 3.8 | `into` type (preview) |

### Experimental / research features

- Explicit nulls — experimental since 3.0
- Erased definitions — experimental since 3.0
- Capture checking — experimental research project since 3.2
- Named type arguments — experimental since 3.0
- Modularity (`tracked`, applied constructor types) — experimental
