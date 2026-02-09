# Further Reading

Curated links to official documentation, specifications, talks, and libraries.

---

## Official Documentation

- [Scala 3 Reference](https://docs.scala-lang.org/scala3/reference/) — The authoritative language reference.
- [Scala 3 Book](https://docs.scala-lang.org/scala3/book/introduction.html) — Introductory guide to Scala 3 features.
- [Scala 3 Migration Guide](https://docs.scala-lang.org/scala3/guides/migration/compatibility-intro.html) — Migrating from Scala 2 to Scala 3.
- [Scala 3 Language Specification](https://scala-lang.org/files/archive/spec/3.x/) — Formal language spec.
- [TASTy Format](https://docs.scala-lang.org/scala3/guides/tasty-overview.html) — Typed Abstract Syntax Trees.

## SIPs (Scala Improvement Proposals)

Key SIPs behind the features in this guide:

| SIP | Feature | Status |
|-----|---------|--------|
| [SIP-23](https://docs.scala-lang.org/sips/literal-types.html) | Literal-based singleton types | Implemented |
| [SIP-33](https://docs.scala-lang.org/sips/match-types.html) | Match types | Implemented |
| [SIP-44](https://docs.scala-lang.org/sips/fewer-braces.html) | Fewer braces | Implemented |
| [SIP-47](https://docs.scala-lang.org/sips/clause-interleaving.html) | Clause interleaving | Implemented |
| [SIP-54](https://docs.scala-lang.org/sips/multi-source-extension-overloads.html) | Multi-source extensions | Implemented |
| [SIP-56](https://docs.scala-lang.org/sips/named-tuples.html) | Named tuples | Implemented |
| [SIP-57](https://docs.scala-lang.org/sips/replace-nonsensical-unchecked.html) | Replace unchecked | Implemented |
| [SIP-58](https://docs.scala-lang.org/sips/into-type.html) | `into` type | Preview |

## Talks & Presentations

- **Martin Odersky — "Simplicitly: Foundations and Applications of Implicit Function Types"** — The theoretical underpinning of context functions.
- **Martin Odersky — "A Tour of Scala 3"** (ScalaDays 2019) — Overview of Scala 3's design goals.
- **Martin Odersky — "Safe Programming with Effects"** — Introduction to capture checking.
- **Guillaume Martres — "Match Types in Scala 3"** — Deep dive into match types implementation.
- **Nicolas Stucki — "Metaprogramming in Scala 3"** — Quotes, splices, and inline.
- **Jamie Thompson — "Type Class Derivation in Scala 3"** — Practical derivation patterns.

## Key Papers

- **Odersky et al. — "The Essence of Dependent Object Types" (DOT)** — Theoretical foundation for Scala 3's type system.
- **Amin, Grütter, Odersky, Rompf, Stucki — "The Essence of Scala"** — Formal model of Scala's core.
- **Boruch-Gruszecki et al. — "Tracking Captured Variables in Types"** — Capture checking foundations.
- **Blanvillain, Brachthäuser, Odersky et al. — "Type-Level Programming in Scala 3"** — Match types and inline.

## Libraries Demonstrating Advanced Type Features

| Library | Key Features Used |
|---------|-------------------|
| [Kittens](https://github.com/typelevel/kittens) | Type class derivation [-> catalog/08] |
| [Circe](https://github.com/circe/circe) | ADTs, derivation, opaque types [-> catalog/11] [-> catalog/08] [-> catalog/12] |
| [Iron](https://github.com/Iltotore/iron) | Inline validation, opaque types, compiletime ops [-> catalog/17] [-> catalog/12] |
| [Ox](https://github.com/softwaremill/ox) | Context functions, structured concurrency [-> catalog/06] |
| [Tapir](https://github.com/softwaremill/tapir) | Match types, type lambdas, derivation [-> catalog/03] [-> catalog/02] |
| [Shapeless 3](https://github.com/typelevel/shapeless-3) | Mirror, type class derivation, HKTs [-> catalog/08] [-> catalog/02] |
| [Ducktape](https://github.com/arainko/ducktape) | Macros, Mirror, inline [-> catalog/18] [-> catalog/08] [-> catalog/17] |
| [Scala CLI](https://scala-cli.virtuslab.org/) | Inline directives, compile-time configuration |
| [ZIO](https://github.com/zio/zio) | Intersection types for environment, union for errors [-> catalog/01] |
| [Cats Effect](https://github.com/typelevel/cats-effect) | Type class hierarchy, context functions [-> catalog/05] [-> catalog/06] |

## Community Resources

- [Scala 3 Gitter / Discord](https://discord.gg/scala) — Community discussion.
- [Contributors Forum](https://contributors.scala-lang.org/) — Language design discussions.
- [Scala Center](https://scala.epfl.ch/) — Educational initiatives.
- [Scala Exercises](https://www.scala-exercises.org/) — Interactive learning.
