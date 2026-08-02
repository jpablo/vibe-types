# Lean 4 catalog review

Review of all 48 entries in `plugin/skills/lean/catalog/` plus `00-overview.md`. Every finding was
reproduced against the pinned **Lean 4 v4.31.0, core only** (`projects/lean-project/lakefile.toml`
declares no dependencies) via `lake env lean`, unless marked as a cross-language or
documentation-reference claim.

**~180 verified defects across all 49 entries. No file came back clean** — the first of the three
catalogs reviewed where that is true (Scala had 5 clean files).

## Method

Same as `typescript-catalog-review.md` and `scala-catalog-review.md`: mechanical passes, then one
agent per group of ~4 files, each compiling a minimal probe before reporting. The most consequential
or surprising claims were then re-verified by hand.

Unlike the Scala pass, `lake env lean` genuinely inherits the pinned toolchain, so agent probes were
a true match to the harness — no repeat of the hand-typed-flags gap documented in the Scala review.

### The harness blind spot

`verify_lean.py` computes `ok = returncode == 0 and not errors`. **Warnings do not fail a snippet,
and `sorry` is a warning.** Verified:

```
theorem fake : 1 = 2 := by sorry
-- warning: declaration uses `sorry`     (exit 0 — harness passes)
#print axioms fake  -- 'fake' depends on axioms: [sorryAx]
#print axioms real  -- 'real' does not depend on any axioms
```

So an admitted proof passes green. This is the Lean analogue of TypeScript's vacuous ✅, and
`#print axioms` is the tool that exposes it.

**This hypothesis was largely falsified up front**, which is worth recording: a fence-aware scan
found all 10 `sorry` occurrences are prose *about* the concept, none load-bearing; `native_decide`
appears only in prose; and the five `partial def`s are legitimate `IO` loops in the two files whose
topic is termination. The blind spot is real; the corpus does not exploit it.

---

## The two systematic patterns

These are the substantive result of the review — they are facts about how the corpus was written,
not about either language.

### Pattern 1 — "claimed ambiguity error, actual silent selection" (7 sites, 2 languages)

| File | Claim | Reality (verified) |
|---|---|---|
| **Scala T25** | given imports conflict → ambiguity error | silently picks last import (`"M2"`) |
| **Lean T05** | overlapping instances → "ambiguous, possible interpretations" | silently picks last declared (`"B"`) |
| **Lean T18** | multiple `Coe` instances → ambiguity reported | silently picks last declared |
| **Lean T19** | conflicting scoped instances → ambiguity errors | silently picks later namespace (`"@42"`) |
| **Lean T25** | "ambiguous instances cause compile errors" | `#synth` returns `instB`, no diagnostic |
| **Lean T37** | "must find exactly one best instance" | first success in search order wins, silently |
| **Lean T49** | conflicting `outParam` outputs → ambiguity | silently commits, `rc=0` |

Every one of these promises the compiler **rejects** the conflict. Every one of these languages
**silently chooses**. Neither Lean's `SynthInstance.lean` nor Scala 3 has the diagnostic being
quoted — the Lean string `ambiguous, possible interpretations` comes from identifier/notation
overloading, not instance search.

The consequence is worse than a wrong message. For T25 and T37 it means **importing a library can
silently flip which instance a user gets** — exactly the hazard Rust's coherence rules exist to
prevent — while the documentation tells the reader they are protected. T37 contradicts itself: its
line 73 Rust comparison correctly says Lean "has no orphan rules", directly against its own
lines 20/25.

### Pattern 2 — kernel vs elaborator reducibility (5 Lean files)

**T16 L59, T21 L13/L14/L132, T23 L9-L11, T39 L30, T40 L62** all attribute `@[reducible]` /
`@[irreducible]` to *the kernel*. The kernel ignores them entirely and delta-reduces any `def`;
they are elaborator/`whnf` transparency settings. Only `opaque` is a genuine kernel barrier.

```
@[irreducible] def n5 : Nat := 5
theorem k2 : n5 = 5 := by with_unfolding_all rfl   -- accepted
#print axioms k2   -- does not depend on any axioms   ← the kernel unfolded it
opaque o5 : Nat := 5
theorem k3 : o5 = 5 := by with_unfolding_all rfl   -- error: rfl failed
```

**T53's build failure is this same confusion surfacing as an actual break** (below), and the
related fact — that instance search runs at *reducible* transparency, so a plain `def` alias blocks
instance synthesis exactly as hard as `@[irreducible]` — is missing from T23 and is the single most
useful gotcha the catalog omits.

---

## Structural passes

- **Section numbering: clean** across all 48 entries.
- **Links: clean**, 0 real breaks (fence-aware scanner).
- **Snippets: 68 files checked, 2 failures.**

### The 2 compile failures

Both are `expected_fail_mismatched` — the same defect class as Scala's T12/T33 and TypeScript's
T47: a snippet registered as expect-error that *does* fail, but for the wrong reason.

**T03-newtypes-opaque L40** fails with `Unknown identifier 'speed'`. The fence is registered
expect-error because of a `-- error: expected Meters, got anonymous constructor` comment at L34 —
which is itself **fabricated**: `#eval speed ⟨100.0⟩ ⟨10.0⟩` evaluates to `10.000000`, since
anonymous-constructor notation elaborates against the expected type. The doc teaches readers to
avoid the correct idiom, and that bogus claim is what breaks the build. One fix resolves both.

**T53-path-dependent-types L104** fails with `failed to synthesize OfNat age.ValType 30` and
`ToString age.ValType`. Root cause: `age`/`email` are plain `def`s, and instance synthesis runs at
`reducible` transparency, so it cannot unfold `age.ValType` to `Nat`. Changing them to `abbrev`
makes the whole example compile. Snippet 1 passes because there the numeral elaborates at `Nat`
and is only *unified* with the projection, at default transparency.

---

## Highest-severity findings beyond the patterns

**Claims that something fails when it succeeds** — the characteristic Lean defect, and the opposite
polarity from TypeScript's:

- **T09 L103**: `h : n = m` used where `n = m + 0` is expected is presented as an error "because
  they are only propositionally equal". They are *definitionally* equal (`Nat.add` recurses on its
  second argument) and it compiles. The file's own L19 says so correctly.
- **T15 L85 and T22 L91** (same fabricated narrative, two files): `safeGet #[10,20,30] ⟨1, by omega⟩`
  is shown working and `⟨5, by omega⟩` failing. `omega` fails on **both** — it treats
  `#[10,20,30].size` as an opaque atom — and the quoted error ("omega fails to prove 5 < 3") is
  invented. `by decide` is what works.
- **T40 L60**: "no type-level `if`" — `ite` is `Sort`-polymorphic, so type-level `if` works.
- **T52 L53**: "`Fin 100` does not coerce to `Nat`" — it does, implicitly. The gotcha is reversed.
- **T21 L66**: "`opaque` blocks `#eval`" with a fabricated message `cannot evaluate, 'x' is opaque`
  (zero hits in the toolchain source). `opaque` values evaluate fine.
- **T31 L44**: `opaque structure` — a parse error; the feature does not exist.
- **T39 L27**: "`@[simp]` must be an equality or iff" — any proposition can be tagged (normalized
  to `p = True`).

**Load-bearing claims that are simply wrong:**

- **T40 L13**: "Lean's universes are **cumulative**" — Lean 4 is *not* cumulative (Coq is). This is
  the file's central justification.
- **T61 L9**: "Lean's **kernel** includes a termination checker" — termination is enforced by the
  *elaborator*; the kernel only accepts recursor applications, which is why `partial` bypasses it
  entirely as an `opaque` constant.
- **T51 L114**: "`partial` is an *axiom* … similar to `sorry`" — `partial def` adds **no axiom**;
  it requires `Nonempty`/`Inhabited` evidence for the return type, the opposite of "without
  constructive evidence". (I passed this claim to the agent in my own briefing; it falsified it.)
- **T31 L19**: "the compiler generates child→parent coercions automatically" — it generates only
  the `toParent` projection, and the file's own Example B has to register `Coe` by hand.
- **T39 L65**: `set_option` scoping stated backwards — bare `set_option` persists to end of scope;
  `... in` is the one-command form.
- **T20 L7**: "neither `=` nor `==` is available for free" — `=` is universal for every type.
- **T22 L62**: "no mechanism to constrain callable things" — `CoeFun` does exactly that, and is the
  missing centerpiece of a file titled *callable typing*.
- **T05 L137**: `DecidableEq` is not a class and has no `decEq` field — it is a reducible
  abbreviation for a Pi type of `Decidable` instances.

**Mathlib-boundary confusion runs in *both* directions** — more interesting than the one-way drift
predicted:

- **T16 L49, T30 L56/L124**: `norm_num` presented as available; it is Mathlib-only. So is `ring`,
  `linarith`; `aesop` is the separate Aesop package.
- **T58 L17**: `Fact` cited as core with an `Init.Prelude` anchor; it is Mathlib.
- **T53 L51**: `Type*` is Mathlib syntax; it does not parse in core.
- **T55 L7**: `WriterT` listed as core; it **does not exist** in Lean 4 core.
- **T54 L9**: `LawfulFunctor`/`LawfulMonad` attributed to Mathlib; they are in **core**
  (`Init.Control.Lawful`) — the doc *under*-credits core.

**Fabricated compiler messages** (a smaller share than Scala's, but present): `universe level
mismatch` (T35), `macro expansion produced ill-formed term` (T17), `maximum coercion depth reached`
(T18), `maximum class-instance resolution depth reached` (T05/T37 — Lean 3 phrasing), `'partial'
definition uses 'sorry'-like axiom` (T51), `cannot evaluate, 'x' is opaque` (T21). All verified
absent from the 4.31.0 source.

**Both overviews are stale in the same way.** Lean's `00-overview` describes a 16-document catalog
numbered `01`–`16`; 48 exist, numbered T01–T61 sparsely, and 32 are missing from the inventory —
including every file reviewed by the agent that found it. It also mandates sections 8 and 9 that
only those same 16 files have, and tells proof-background readers to "start with section 9", which
two thirds of the catalog lacks. (The Scala overview had the identical defect with different
numbers — see `scala-catalog-review.md`.)

---

## What I got wrong

Recorded because the priors I hand the agents shape what they look for:

- **The `sorry` hypothesis.** I predicted the harness's warning blind spot would be exploited by
  hollow proofs. Scanned first: it is not. All `sorry` uses are prose.
- **`partial def` as a `sorry`-like axiom.** I passed T51's claim into the agent brief as
  established. It is false — `partial` adds no axiom. The agent checked rather than accepting it.
- **Mathlib drift direction.** I briefed agents to hunt Mathlib-only claims presented as core. That
  found real defects, but the reverse error (core presented as Mathlib) also occurs and I did not
  ask for it; T54 was caught anyway.

This is now the third review in which agent pushback corrected my briefing, which I regard as the
main safeguard in this method: had the agents simply executed the briefs, several of my errors
would have been written into the docs as fixes.

---

## Cross-catalog comparison

Three catalogs, three distinct dominant failure modes:

| Catalog | Dominant defect | Snippet failures | Clean files |
|---|---|---|---|
| **TypeScript** | the vacuous ✅ — enforcement claimed, never performed | 0 | 0 |
| **Scala 3** | fabricated compiler output — invented codes and messages | 2 | 5 |
| **Lean 4** | claims that something *fails* when it succeeds | 2 | 0 |

Lean inverts TypeScript's polarity: where TypeScript over-claimed what the checker catches, Lean
over-claims what it rejects. Both directions mislead, but differently — a TypeScript reader thinks
they are protected when they are not; a Lean reader avoids correct idioms they were told would fail
(T03's anonymous constructors being the clearest case).

What is shared across all three is **Pattern 1**: whenever a language resolves an ambiguity
silently, the documentation claims it errors. That held in Scala and in five separate Lean files.
