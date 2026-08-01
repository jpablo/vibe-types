# Scala 3 catalog review

Review of all 47 entries in `plugin/skills/scala3/catalog/` plus `00-overview.md`. Every finding was
reproduced against **Scala 3.8.4** via `scala-cli compile --server=false`, with the pinned library
set (cats-core 2.13.0, cats-effect 3.7.0, zio 2.1.26, iron 3.3.1), unless marked as a
cross-language or documentation-reference claim.

**~140 verified defects across 42 of 47 entries.** Five files came back clean: **T07, T13, T17,
T40, T42**.

## Method

Same approach as `typescript-catalog-review.md`: mechanical passes first, then one agent per group
of ~3 files, each compiling a minimal repro before reporting anything. 13 of the most consequential
or surprising claims were then independently re-verified by hand; all 13 held.

A note on the compiler-flag context, which drives a whole class of findings.
`projects/scala-project/build.sbt` has `-source:future`, `-language:strictEquality` and
`-Yexplicit-nulls` **commented out**, and `verify_scala.py` compiles snippets without `-Werror` or
`-Wunused:all`. So under the settings these docs are actually validated with, a non-exhaustive
`match` *warns* rather than errors. Several entries claim otherwise.

## What this review found that the TypeScript one did not

The two catalogs fail differently, and the difference suggests different provenance.

TypeScript's dominant defect was the **vacuous ✅** — an example claiming enforcement the compiler
never performs. Scala's is **fabricated compiler output**: invented error codes, swapped codes, and
message text that does not exist. Roughly a third of the findings below are of that shape. The
worst case is T37, which quotes a multi-line implicit-search transcript from a flag Scala 3 does
not have.

That pattern reads as entries written against Scala 2 habits or against the upstream reference
rather than a live 3.8.4 compiler. Two findings make the provenance concrete: **T41's** stale
variance sentence is copied verbatim from the official Scala reference page, which the compiler
contradicts; and **T44's** given-priority version number matches the scala-lang docs and not the
compiler.

### Cross-file defects (shared provenance)

The same wrong claim appears in more than one entry, which is worth fixing as a set:

| Claim | Files | Reality |
|---|---|---|
| `=:=`/`<:<` witnesses are heap-allocated per call | T57 L55, T58 L41 | One cached singleton for *all* `=:=` **and** `<:<` in the program. Verified: `summon[Int =:= Int] eq summon[String =:= String] eq summon[Int <:< Any]` is `true`. Both files build optimization advice on a cost that does not exist. |
| "Named import beats wildcard given import" | T25 L61, T37 L66 | Scala 3 dropped that Scala-2 rule. The two are ambiguous; priority is nesting depth, then specificity. |
| `opaque type X = Y derives CanEqual` | T03 L58, T20 L48 | Illegal — `derives` is only valid on class/trait/object/enum. Must hand-write the given in the companion. |
| `T#A` requires a *concrete class* prefix | T44 L59, T49 L62 | The restriction is on abstract-**type** prefixes. Traits and abstract classes are legal — and T49's own example uses `trait Container`. |
| `given [T: Ord & Show]` as a context bound | T02 L59, T05 L54 | Kind error. Use `[T: {Ord, Show}]` (3.6+) or `[T: Ord : Show]`. |

---

## Snippet compilation: 2 files fail

`make verify-scala MATCH=1` → **69 files checked, 2 with failures.** (The TypeScript catalog was
fully green.)

Both are the same defect: a snippet registered as expect-error that *does* fail, but on
`Not found:` for undefined names rather than the error being taught — while the actual lesson sits
in a **commented-out** line and is never compiled.

- **T12-effect-tracking L15** — fails on `Not found: type FileOutputStream` (missing
  `import java.io.FileOutputStream`). The capture-checking escape it teaches is commented out.
- **T33-self-type L31** — fails on `Not found: type UserService` / `HasLogger`, which are declared
  in an earlier fence; each fence compiles standalone. The illegal-inheritance claim is on a
  commented-out class.

This is the same masking as TypeScript's T47, where an `@ts-expect-error` was absorbing an
undefined-name error: the snippet reads as a demonstration but proves nothing.

---

## Highest-severity findings

**T25 promises a safety property that does not hold.** L107/L13: "the compiler rejects the program
with an ambiguity error rather than silently choosing one." For the *anonymous* given style this
file uses throughout, both givens synthesize the name `given_Show_Int`, so the later import
silently shadows the earlier. Verified: prints `M2`, no diagnostic. Naming the givens restores the
E172 ambiguity. Also, the scenario as written is impossible — third parties cannot place
`given Ordering[Int]` in a companion object, and companion givens are never *imported*.

**T37 quotes compiler output that does not exist.** L76 and Example A L112-117 claim `-explain`
prints a given-search trace ("Found given Codec[String] in JsonCodecs (via import) … Selected: …").
Verified: `-explain` emits *nothing* on a successful search and adds nothing to a failed one, and
`-Xlog-implicits` / `-Xprint-implicits` / `-Vimplicits` / `-Ydebug-implicits` are all rejected
(`bad option ... was ignored`). Scala 3.8.4 has no implicit-search-trace flag at all.

**T57's headline recipe does not compile.** L9/L44/L55 tell you to combine `erased` with `=:=` to
strip phantom evidence. The synthesized witness `=:=.refl[A]` is a method application and fails
`erased`'s purity check with `[E217] implicit argument to an erased parameter fails to be a pure
expression`. A working version needs a hand-rolled evidence trait with a non-parameterized
`erased given` bound to a pure path.

**T33 gets self-type checking backwards.** L117/L11: "checked late… the error appears only when you
try to `new` it." Verified: `[E058]` fires at an `abstract class AbsRepo extends Repo33` definition
with nothing instantiated. The check runs at every inheriting definition, class or trait, abstract
or not. The same file contains a **fabricated error block** (L147-159) asserting
`new HasAuth with HasLogger {}` fails to conform to `HasLogger` — impossible, since
`HasAuth & HasLogger` is by definition a subtype.

**T14 inverts why `ClassTag` is unsound.** L81 says such tests "emit `unchecked` warnings". They
emit nothing — `viaClassTag[List[String]](List(1,2,3))` silently returns `Some(List(1, 2, 3))`.
The silence *is* the unsoundness. A reader told to watch for a warning concludes their code is fine.

**T08 gets opaque-type variance backwards.** L95/L107 claim variance is checked against the
declared bounds, not the underlying type, and that "phantom variance" over an invariant carrier is
legal. Verified: `opaque type IArr[+T] = Array[T]` does not compile
("covariant type parameter T occurs in invariant position"). The stdlib works only because it is
`Array[? <: T]` — the wildcard is what legalises it. Explicit bounds do not relax the check.

**T61 claims recursive opaque aliases are allowed.** L45. Verified: `[E140] Cyclic Error`.
Transparent aliases can recurse; opaque ones cannot.

**T56 claims a guarantee the compiler does not make.** L15: "the compiler rejects any direct use of
concrete effects." `F[_]: Monad` constrains only the *return* type; a polymorphic method can call
`IO.println(...).unsafeRunSync()` in its body and compile clean. Tagless final is a discipline, not
a checked boundary.

**Exhaustivity claimed as an error, actually a warning** — the predicted Scala analogue of the
TypeScript exhaustiveness bug: **T61** L105/L15/L17/L44 and **T02** L38 both assert the compiler
makes incomplete handling a compile error. It is `[E029]`, a warning, under the flags these docs
are validated with.

---

## Inverted advice

Two entries invert the same way their TypeScript counterparts did — considering only one axis and
missing the typing consequence:

- **T32 L53** "`final` on `val` is sometimes redundant… in a `final class`, all members are
  effectively final." Backwards: `final val x = 42` *without a type ascription* infers the literal
  singleton `(42 : Int)`, where a plain `val` gives `Int`. That is the constant-folding marker and
  it is unaffected by the enclosing class being final. (The TypeScript entry made the analogous
  error about `readonly` on primitives.)
- **T22 L102** "eta-expansion requires an expected type to disambiguate… fails if `show` is
  overloaded." Backwards, and self-contradictory: an expected type is exactly what *resolves* the
  overload. Verified: `val f: Int => String = Show.show` compiles.

## Claims contradicted by their own file

- **T31 L83** "named tuples do not have `Mirror` instances" — they do, with field-name labels.
- **T32 L94** a `class SuperAdmin extends Permission` example labelled a compile error, sitting in
  the same file as the sealed trait, where extension is legal; contradicts its own gotcha 6.
- **T23 L147/150** an error block annotated "the alias is expanded in the error" — the compiler
  prints `Required: Handler`, i.e. the opposite, and it is the sole example backing gotcha 5.
- **T54 L121** "any cats `Monad` works transparently" — contradicts its own gotcha 2 (abstract
  `F[_]: Monad` needs the syntax imports).
- **T37 L57** search-order list places top-level package givens last; they are lexical scope and
  win outright, contradicting its own gotcha 2.
- **T49 L62** the `T#A` claim, contradicted by the `trait Container` two sections above it.
- **T53 L194** "cannot write a dependent lambda directly" — contradicts its own L166.
- **T43 L20** the snippet keeps `import scala.language.implicitConversions`, making its own
  "no language import needed" point unprovable.

## Library and version drift

- **T26** iron: `.refine` is the *unsafe throwing* variant and is deprecated (→ `refineUnsafe`);
  `refineEither`/`refineOption` are the safe ones. No `StrictlyPositive` in 3.3.1 — `Positive` is
  already strict. Predicate names listed (`MatchesRegex`, `NonEmpty`) are refined's, not iron's.
  refined's literal auto-refinement is **Scala 2 only** — refined_3 0.11.3 ships no `autoRefineV`,
  so `val x: PosInt = 42` does not compile. And on Scala 3 refined's `Refined[T,P]` is *also* an
  opaque type, so the "zero overhead" contrast holds only against refined-on-Scala-2.
- **T54** no `IO.parMapN` (it is tuple syntax, and needs `Parallel`, not `Applicative`); "Future is
  not a lawful Monad" is overstated (cats ships `Monad[Future]`; the real issue is referential
  transparency); the accumulation example has only *one* invalid input.
- **T55** `Ask` is cats-mtl, not cats-core; `*` kind-projector syntax needs the plugin (native is
  `[A] =>> …`). Its transformer parameter orders and the stack-ordering gotcha were all verified
  **correct** — the strongest content in the review.
- **T57 L59** `scala-newtype` is Scala-2-only (macro-paradise) and is about newtypes, not builders.
- **T58 L41** `@specialized` is a no-op in Scala 3 (specialization was dropped), and `erasedValue`
  cannot supply evidence.
- **T12 L59** "always use the latest nightly" is stale — capture checking, `saferExceptions`,
  `erasedDefinitions` and `modularity` all compile on stable 3.8.4 with no flags.
- **T44/T25** the given-priority re-prioritisation lands in **3.7**, not 3.5/3.6;
  `-source:3.5-migration` is silent.
- **T52 L3** Scala 2.13 shipped literal types **by default** (SIP-23); `-Yliteral-types` is not a
  valid 2.13 option.
- **T34 L3** `-Yexplicit-nulls` is not "stabilized in 3.3" — still an experimental `-Y` flag, as
  the file's own source anchor (`/reference/experimental/`) shows.
- **T43** modularity does not need `-source:future` (the language import alone gates it, as its own
  snippet proves); `into` is `opaque type into[+T] >: T = T` — the covariance is missing.
- **T39 L49/L72** `-language:experimental` is not a valid option; the real opt-ins are
  `@experimental`, a package-level `scala.language.experimental.*` import, or `-experimental`.

## Wrong or invented compiler diagnostics

Beyond T37's fabricated transcript: **T08** L123/L146 label variance errors `[E093] Variance Error`
— variance errors carry **no** error ID (bare `-- Error:`), and E093 is `ExtendFinalClass`;
L139 invents a trailing "Note: Cat <: Animal, but class MutRef is invariant". **T04** L97/L106 has
two codes effectively swapped (E008 vs E057) and the wrong trigger. **T23** L131/134 says E046 +
"Recursion limit exceeded"; it is E140 + "illegal cyclic type reference". **T33** L132-140 says
E157; it is E058, and names the parent's self type alone. **T34** L139 says E172; it is E007, and
L104-112/L128-133 quote `Required: Int` where the compiler prints the structural
`Required: ?{ + : ? }`. **T22** L151 invents "not a single abstract method type"; L158 says E081
where it is E086. **T31** L132 invents "may not extend another case class"; the real text is
"case-to-case inheritance is prohibited". **T52** L110 invents "Cannot reduce constValue[Int]"
(real: E182). **T15** L138-139/L144 invent two diagnostics. **T26** and **T06** quote several
blocks that do not match actual output.

## Cross-language analogy errors

- **T35 L62** Lean universe claims are off by one: `Prop = Sort 0` is a definitional *equality*,
  but `Prop : Type 0`. And `AnyKind` abstracts over **kinds** (arity), not universe levels — Scala
  has no universe levels, so the analogy is a category error.
- **T37 L7** Rust/Haskell resolve against a *global, coherent* instance set; scope- and
  import-sensitivity is precisely how Scala differs, not how it is similar.
- **T36 L9** Rust trait conformance is nominal and explicit (`impl Trait for Type`); Go's implicit
  interfaces are the right analogue for structural conformance.
- **T59 L60** Haskell's `ExistentialQuantification` has no explicit pack form either — introduction
  is data-constructor application. `pack`/`unpack` belongs to System F; ML uses opaque ascription.
- **T49 L9/L64** Rust's associated-type *defaults* are unstable (feature-gated), and the real
  contrast is arity of determination: Rust's associated type is unique per implementing type;
  Scala's is per instance/path.
- **T36 L55** presents constructor parameters as what distinguishes abstract classes from traits —
  Scala 3 traits take them too (only a *directly*-extending class may pass them).

## Structural passes

- **Section numbering: clean** across all 47 entries — no duplicates, no out-of-order sections.
  (The TypeScript catalog had 9 broken files.)
- **Links: clean** — 0 real breaks.
- **00-overview** has two documentation errors of its own: L29 says the catalog is "numbered
  `01`–`23`" with `[-> catalog/nn]` cross-references — it is `T01`–`T61`, 47 sparse entries, with
  `[-> catalog/Tnn]`; a reader would conclude T24+ do not exist. L16 says Minimal snippets contain
  "no imports", contradicted by 16 of the 47 files.

### A caveat on my own link scanner

The first link pass reported **120 broken links**. All were false positives: Scala generics inside
code fences (`def map[B](f: A => B)`) parse as markdown `[text](target)`. The scanner is now fence-
and inline-code-aware, and the zero above is from the fixed version. The same bug produced the one
retracted finding in the TypeScript review (T18's `[Symbol.toPrimitive](hint: …)`).

## Hypotheses I gave the agents that turned out wrong

Worth recording, since these priors shaped the search:

- **T20 (equality safety)** — I predicted its strict-equality claims would silently depend on
  `-language:strictEquality`. The agent tested the premise and falsified it: `derives CanEqual`
  makes cross-type comparison an error with *no* flag, exactly as documented. (It found three other
  real defects there instead.)
- **T13 (null safety)** — I flagged it as high-risk for unqualified `-Yexplicit-nulls` claims. It
  came back clean: the prose is consistently flag-qualified and the snippet carries its own
  `//> using option "-Yexplicit-nulls"`, which the harness honours.

## Where Scala is genuinely better than its TypeScript counterpart

**T57 typestate.** The TypeScript entry of the same name had a flagship example that enforced
nothing — its phantom state parameter was never referenced, so both states were the same type.
Scala's equivalent examples were each verified to reject the illegal transition, including a
union-of-evidence trick that works because given search decomposes union types. Scala's nominal
generics do the work TypeScript's structural ones could not, so the same technique is sound in one
language and vacuous in the other. T57's defects are all in its *prose* about `erased` and runtime
cost, not in its type-level machinery.
