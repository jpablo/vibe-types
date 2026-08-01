# TypeScript catalog review

Review of all 35 entries in `plugin/skills/typescript/catalog/`. Every finding below was
reproduced against `tsc` 5.7.2 with the project's exact flags
(`--strict --exactOptionalPropertyTypes --noUncheckedIndexedAccess --target es2022 --lib es2022`)
unless marked as a cross-language/library claim.

## Scope note

All snippets in the catalog **compile** — `make verify-typescript MATCH=1` is green across every
file. The harness also machine-checks `// error: <msg>` comments on live code and `@ts-expect-error`
directives, so those claims are already verified. What it cannot check, and what this review
targets, is **prose claims and ❌/✅ narrative comments**: statements about what the compiler does
that no snippet actually exercises.

The recurring defect is a ✅ example that does not demonstrate its own claim.

---

## Status: all findings below have been fixed

Every defect in this document has been corrected and verified. The corrections landed in nine
commits (`cbab040`/`53bb6fe` for T31/T32, then seven on `docs/catalog-correctness-fixes`):

| Commit | Scope |
|---|---|
| `1732fcb` | Exhaustiveness examples that enforced nothing — T14, T36, T52, T57, T59, T63 |
| `8f84b8b` | Inverted type-system rules — T02, T05, T08, T21, T62 |
| `0cdf1c9` | False encapsulation guarantees, broken examples — T03, T22, T26, T45, T47, T49 |
| `4636bdb` | never / self-type / conditional types — T33, T34, T41 |
| `81e5166` | Inference, discriminants, `satisfies` — T01, T04, T07 |
| `a443441` | Null-safety codes, recursion limits, async iteration — T13, T61, T63, T64 |
| `b9be3a4` | Effect tracking, library drift, metaprogramming — T06, T12, T17, T18, T54 |

Replacement claims were verified too, not just the corrections — the rewritten `CamelToSnake`
really does produce `"create_user_request"`, the repaired `withRetry` infers a concrete signature
instead of `any`, and the new exhaustiveness examples were each confirmed to fail when a case is
removed. Where a fix could be made self-checking it was: several now rest on `@ts-expect-error`,
which the harness fails if the error ever stops occurring, so those cannot silently rot again.

Section numbering was also repaired in the 9 files with duplicate or non-monotonic headings (T01,
T06, T07, T18, T21, T34, T45, T52, T61), with `Source Anchors` in T34/T52 unnumbered to match the
catalog convention.

**Correction to an earlier draft of this document:** it reported that T18 renders
`[Symbol.toPrimitive](hint: …)` as a broken markdown link. That was a false positive — the text sits
inside a fenced code block, where it renders correctly. The link scanner did not skip fenced
blocks. No change was needed and none was made.

Still open, cosmetic only: T05 and T54 have no section numbers at all, and
T02/T04/T08/T12/T13/T14 are partly numbered — the catalog has no single convention.

## Earlier pass (T31, T32)

- **T32-immutability-markers** — `Object.freeze` inference, `let x = "hello" as const`, a §12 ✅
  exhaustiveness example that produced no error, the inverted "readonly on primitives is redundant"
  antipattern, the `@final` analogy, and a missing gotcha on structural assignability.
- **T31-record-types** — same incorrect `Object.freeze` claim (gotcha 9).

---

## T01 — Algebraic Data Types

1. **L75 — discriminant claim too narrow.** "The discriminant field must be a literal type (string
   or number literal)". Boolean literals, enum members, and `null`/`undefined` all work. The file
   contradicts itself: Example B (L179) uses `ok: true`/`ok: false`, and L213 says "any
   literal-typed field". → "must be a unit type (string, number, boolean, enum member, `null`, `undefined`)".
2. **L453 — fabricated error text.** Quotes a hybrid `Type '...' is not assignable to parameter of
   type 'never'`. tsc emits *Argument* of type … is not assignable to *parameter* (TS2345) for
   `assertNever(s)`, or *Type* … not assignable to *type* (TS2322) for `const _: never = s`. L170 of
   the same file quotes it correctly.
3. **L473 — quoted widening error does not match.** For the file's own `PaymentStatus`, tsc reports a
   missing-property elaboration naming the `"failed"` constituent; it never mentions `"pending"`.
4. **L487 — excess-property error names the alias.** With a union target tsc names the matched
   *constituent* (`'{ kind: "pending"; amount: number; }'`), not `PaymentStatus`.

## T02 — Union & Intersection

1. **L3 — wrong version.** Intersection types shipped in **TS 1.6**, not 2.1 (2.1 = `keyof`, mapped
   types, object rest/spread).
2. **L77 — gotcha 5 is backwards.** Claims calling `((x: string) => void) & ((x: number) => void)`
   "requires satisfying both overloads simultaneously". An overloaded type requires satisfying
   *exactly one*; `f("s")` and `f(1)` both compile.
3. **L80 — gotcha 8 is false.** "Unions are not inferred from if/ternary branches — TypeScript widens
   to the common supertype". TS *does* infer unions: `const t = cond ? "a" : 1` → `"a" | 1`;
   if/else returns → `"a" | 1`; `[1,"a"]` → `(string | number)[]`. The real gotcha is literal
   widening in `let`/mutable positions.
4. **L254 — ✅ is a no-op.** The ❌ `type C = A | B` already has one shared `kind` discriminant, and
   TypeScript flattens nested unions, so ❌ and ✅ are the *identical type*. Verified by mutual-extends
   identity check. Make the ❌ actually lack a shared discriminant.
5. **L284 — recommended fix contains a dead variant.** `{type:"loading"; data: never}` is
   uninhabited — no value can be supplied for `data`. Drop the field.
6. **L303 — "uninhabited" is wrong.** `Array<string> & Array<number>` is inhabited by `[]` (verified).
   Element type collapses to `never`, making it useless — but it is not empty.

## T03 — Branded & Opaque Types

1. **L119 (§7) and §13 Antipattern 1 — the central encapsulation claim is false.** "Cannot write
   `"usr_42" as UserId` — `__userIdBrand` is not exported", and the antipattern blames *exporting the
   symbol* for enabling forgery. Verified: `as UserId` needs only the exported **type**. Forgery
   compiles identically whether or not the symbol is exported. The genuine benefit of `unique symbol`
   is avoiding accidental structural collisions between independently-declared brands.
2. **§13 Antipattern 3 — unreachable code.** `loadUser`'s ✅ `return { id: makeUserId(data.id) }`
   sits after the ❌ `return`, so it can never run. Split into two snippets. Also `JSON.parse` returns
   `any`, so `makeUserId(data.id)` swallows it silently.
3. §11 typo: `Farenheit` → `Fahrenheit` (twice).

## T04 — Generics & Bounds

1. **L151 — `empty()` does not error.** Doc: "`const xs = empty(); // error: cannot infer T`".
   Unresolved type parameters fall back to `unknown`, so it compiles as `unknown[]` — silently
   useless rather than rejected.
2. **L221 — two errors in one gotcha.** (a) An unconstrained type variable with no evidence resolves
   to `unknown`, never `any` — the file's own L427 asserts this. (b) TS7006 is about *unannotated
   parameters*, unrelated to type variables.
3. **L167-168 — inferred types are wrong.** With constraint `number | string` (primitive), literals
   are not widened: `pickLarger(1, 2)` infers `T = 1 | 2`, not `number`.
4. **L73 — gotcha 1 false at type level.** Template literal types apply directly to `T extends string`
   and preserve the literal; no conditional type needed. Only *value-level* operations are limited.
5. **L76 — `keyof any` is `string | number | symbol` under every strictness setting.** "in non-strict
   mode" is wrong (the flag that changed this, `--keyofStringsOnly`, is deprecated).
6. **L93 — C# analogy backwards.** C# generics *are* reified (`typeof(T)`, `new T()`); C# is the
   standard counterexample to erasure. And `T.class` is what Java *cannot* do. Compare to Java only.

## T05 — Type Classes

1. **L372 (gotcha 8), L90, L145 — "abstract classes are checked nominally" is false.** Verified: an
   object literal with all members is assignable to an `abstract class` type with no inheritance.
   The doc's own literal fails only because it omits `perimeter`/`describe`. Nominality requires a
   `private`/`protected` member; `abstract` only blocks instantiation.
2. **L329 — mechanism does not exist.** "TypeScript resolves method collisions via the `implements`
   declaration order and `as` casts". `implements` order has zero effect (byte-identical
   diagnostics when swapped) and `as` cannot re-dispatch. Contradicts L340/L359 of the same file.
3. **L664 — antipattern 5's fix is a no-op.** `interface Node { children: Node[] }` → `type Node =
   { children: Node[] }` produces a mutually assignable identical type and "breaks" no cycle.
   Self-referential interfaces are the normal way to type recursive data.

## T06 — Derivation

1. **L53 — "caught … statically if you pass a literal" is false.** `parseUser(raw: unknown)` never
   statically checks a literal argument; only the runtime `ZodError` fires.
2. **L492 — cause is backwards.** `Type 'string' is not assignable to type 'never'` occurs when a
   variant is **missing**, not when "all branches are exhausted" (exhausted → residual *is* `never` → compiles).
3. **L484 — quoted error wrong.** Actual is TS2741 (single line, "… but required in type 'Customer'"),
   or TS2345 in argument position.
4. **L496 — fabricated error.** tsc never says a `Partial<T>` property "does not exist"; the real
   error is TS2322 about `undefined`. (The prose explanation is correct; only the heading is invented.)
5. **L88 — `z.array(z.infer<T>)` is not valid TypeScript.** `z.infer` is type-only and cannot appear
   in a value position.
6. **L135 / L408 — outdated for the pinned zod 4.4.3.** Recursive schemas are fully inferable via the
   getter form; no separate annotation needed. Scope the `z.lazy()` caveat to zod 3.
7. **L278-288 — the ❌ demonstrates the fix.** `const FLAGS = { enabled: true } as const` does not
   widen and is not mutable. Make the ❌ half a plain object literal.

## T08 — Variance & Subtyping

1. **L23 — the core contravariance rule is stated backwards.** Doc: "`--strictFunctionTypes` ensures
   `(animal: Animal) => void` is **not** assignable to `(dog: Dog) => void`". Verified: that
   assignment **succeeds**; the rejected direction is `(dog: Dog) => void` → `(animal: Animal) => void`.
   L39, L101, L161 of the same file state it correctly.
2. **L20, L22, L45 — `out T` in a method parameter is silently accepted** (methods are bivariant), so
   the `// error` on L45 is wrong; only function-*property* syntax triggers TS2636. And `in out` is
   never verified to "genuinely appear in both positions". Contradicts the file's own L306/L321.
3. **L91 — gotcha 3 backwards on both halves.** Markers *do* change assignability (they override
   inferred variance) and are *not* reliably checked against usage. The file's own `@ts-expect-error`
   at L346 depends on markers changing assignability.
4. **L194 — the quoted diagnostic does not exist.** No "`out` modifier cannot appear on a mutable
   property" in TS 5.7 (0 matches in typescript.js); the real one is TS2636. The shown code produces
   no error at all because `set` is method syntax.
5. **L441-446 and L398-404 — both ❌ halves are not invariant.** TypeScript infers variance for
   unannotated parameters, so an output-only `Reader<T>` is already covariant and assigns directly;
   the "wrapper required" premise is false. Rewrite around a genuinely invariant container.
6. **L274 — `Map.Immutable<T>` does not exist**, and `Record<string, T>` is mutable. Use
   `Readonly<Record<string, T>>` / `ReadonlyMap<K, V>`.

## T07 — Structural Typing

1. **§13 (excess-property antipattern) — the ✅ does not demonstrate its claim.** `data satisfies
   User` on a **variable** performs no excess-property check. The snippet errors only because `age`
   is required and missing — actual text `TS1360 … Property 'age' is missing`, not the quoted
   "'aeg' does not exist". With `age?: number` the typo passes silently. The quoted TS2353 message
   appears only for the fresh-literal form `const data = { … } satisfies User`.
2. **§14 "Nominal Typing with `class`" is mischaracterised.** TS classes are structural. The ❌
   `area(new Square(10))` fails on a genuine shape mismatch (`size` vs `width`/`height`), not
   because classes are "rigid nominals".
3. **§12.2 Money example mislabeled** — `currency: "KGS"` is a missing literal union, not a
   structural-typing problem.
4. **§14 "Manual Type Predicate Boilerplate"** — advice is backwards (named predicates are idiomatic
   and reusable), and the ✅ silently changes behaviour by passing a *new* object `{ id: data.id }`.
5. CHECKED-OK: the `number & { readonly brand: unique symbol }` fix really does separate the types —
   each inline `unique symbol` is distinct.

## T12 — Effect Tracking

1. **L7 and L11 — the headline claim is false.** "the compiler enforces that callers `await` or chain
   the result". Discarding a `Promise`/`IO`/`Either` is not an error; only *assigning* to the
   unwrapped type is. The file's own gotchas 1 and 6 state the truth. Call-site enforcement needs
   `@typescript-eslint/no-floating-promises`.
2. **L189 — `Result<T, never>` does not collapse.** The error branch survives (`{ok:false; error:never}`
   is not reduced), so narrowing is still mandatory before reading `.value`.
3. **L195 — "no way to express sync-or-async without overloading"** — `T | Promise<T>` does exactly
   that and `await` accepts it.
4. **L209 — quoted error wrong.** That case emits TS2741 ("Property 'name' is missing"), not the
   quoted TS2322 wording, which only appears for primitive targets.
5. **L340 / L325 — fp-ts parameter order reversed.** `TaskEither<E, A>` is error-first; the ✅ comment
   says `TaskEither<User, Error>`, a genuinely different type. The ❌ label names a non-existent type.
6. **L380 — identity assertion.** `user as User` where `user: User` cannot fail; and a single-step
   `as` from `Either` to `User` *is* rejected (TS2352), so "assertions bypass the type system
   entirely" is wrong here. Use `as unknown as User`.

## T13 — Null Safety

1. **L204 / heading L196 — wrong error code and title.** Simple identifiers emit **TS18048**
   `'host' is possibly 'undefined'`, not TS2532; and "Cannot find name" (TS2304) never occurs here.
2. **L180-184 — code/cause mismatch.** For the stated cause (property access on a named value) TS 4.0+
   emits TS18047/TS18048; TS2531/TS2532 fire only for non-reference receivers (`f().b`, `arr[0].length`).
3. **L31 / L7 — `x?: T` is not `T | undefined` under this project's flags.** With
   `exactOptionalPropertyTypes` (which the harness enables, and the file's own gotcha 10 describes)
   the two are not mutually assignable (TS2375).

## T14 — Type Narrowing

1. **L308, L318, L376, L526 — the exhaustiveness pattern provides zero exhaustiveness.**
   `default: throw new Error(\`Unreachable: ${s as never}\`)` **never** errors, however many cases are
   missing — `never` is assignable to anything, so the assertion is always permitted. Replace with a
   real `assertNever(x)` call or `const _: never = x`.
2. **L490-506 — fabricated ❌/✅ pair.** TypeScript narrows `typeof x == "string"` identically to
   `===`. The ❌ has exactly the same type behaviour as the ✅.
3. **L471 — the ✅ is statically *worse* than the ❌.** `JSON.parse` returns `any`; the guards narrow
   nothing, so `raw.anyTypoAtAll` also compiles. Annotate `const raw: unknown = JSON.parse(json)`.
4. **L272 — wrong cause for TS7027.** "Unreachable code detected" is syntactic (code after
   `return`/`throw`, or after a `never`-returning call); branches emptied by narrowing never produce it.
5. **L437 — comment inverted.** `return "name" in a` for `a is Cat` *always* narrows at call sites —
   that is the bug (a `Dog` is unsoundly narrowed to `Cat`), not "never narrows".

## T17 — Macros & Metaprogramming

1. **L20 — no distribution occurs.** `string | number extends unknown ? T[] : never` yields
   `(string | number)[]`, not `string[] | number[]` — the checked type is a written-out union, not a
   naked parameter. Contradicts the file's own L209.
2. **L383 — the implementation is broken.** `CamelToSnake<"CreateUserRequest">` actually produces
   `"C_raeU_srR_eust"` (consumes two chars per step, never lowercases).
3. **L463 — invented error code.** `_INST_0444` does not exist; the real diagnostic is TS2589.
4. **L529-543 — neither "fix" changes anything.** All three variants produce `"item/a" | "item/b"`;
   `T & {}` still distributes and `[T] extends [unknown]` is always true. Also the ❌ contains no
   conditional type — it is template-literal distribution, which cannot be opted out of.
5. **L215 — `T` *is* naked.** Nakedness is a property of the conditional's checked type, not of the
   argument; distribution simply doesn't happen because the argument is a tuple, not a union.
6. **L307 — `?` is not `| undefined`.** Under `exactOptionalPropertyTypes`, `Patch<T>` fields may be
   omitted but explicitly passing `undefined` is rejected. The file's own L322-328 shows `name?: string`.

## T18 — Conversions & Coercions

1. **L381 — the ✅ demonstrates the opposite of its headline.** Under `satisfies { apiUrl: string;
   timeout: number }` the literals **are** widened and the properties are **not** readonly; actual
   type is `{ apiUrl: string; timeout: number }` and `config.timeout = 9` compiles. Either fix the
   comment or add `as const` before `satisfies` (as L141 correctly does).
2. **L132 — the comparison does not show what it claims.** `Number(id) === 9007199254740993` is
   **true**: the literal itself rounds to …992. Use `id === BigInt(Number(id))`.
3. **L229/L243 — wrong mechanism.** The class defines `[Symbol.toPrimitive]`, which takes precedence
   over `valueOf` throughout ToPrimitive. `valueOf()` is never called for `temp + 32`. Result (132)
   is right, explanation is not.
4. **L92 — gotcha 5 wrong.** Arrow functions *can* declare `asserts` return types. The real
   restriction is TS2775 at the *call site*: the called name needs an explicit type annotation.

## T21 — Encapsulation

1. **L92 — gotcha 4 backwards.** `#private` is **also** nominal — verified, `#x` in class A and `#x`
   in class B are different members and assignment is rejected both ways, exactly like `private`.
   (Related, L83: "`private` is checked structurally" is the wrong word — it is checked by
   declaration origin.)
2. **L85 — "truly unpierceable without the module's cooperation" is false.** A `#private` field blocks
   plain assignment (TS2741), but a single `as` from a consumer module forges the type with no error.
   Same defect class as T03.
3. **L245 — `Map<readonly K, V>` is not valid TypeScript** (TS1354). Intended: `ReadonlyMap<K, V>`.
4. **L192-193 — barrel example does not compile.** `export type { Circle }` plus `export { Circle }`
   from the same module is a duplicate identifier (TS2300). In a `typescript ignore` block, so the
   harness skips it.
5. **L94 — gotcha 6 describes a mechanism that does not exist.** Import + redeclare is TS2440, and
   `extends` creates a new interface. Cross-module addition requires explicit module augmentation.
6. **L289-297 — label does not match code.** The ✅ "module-level hiding" uses `constructor(private …)`,
   the very thing the ❌ is criticised for; the only real change shown is constructor injection.

## T22 — Callable Typing

1. **L448-469 — ❌ and ✅ are behaviorally identical.** The implementation signature is never visible
   to callers (the file's own gotcha 1 says so), so `...args: any[]` shadows nothing. Both versions
   produce the same errors at the same call sites. Replace with a rest *overload signature* declared
   before narrower ones, which genuinely does capture calls first.
2. **L86 — gotcha 6 backwards.** Resolution is first-match-wins, so a *later* rest overload can never
   shadow an earlier specific one. "earlier" → "later".
3. **L292 — keyword-argument claim is meaningless.** TS/JS has no keyword arguments; and parameter
   names in function types are cosmetic (ignored for assignability), so they encode nothing.
4. **L274 — wrong error in the heading.** The snippet emits TS2355 ("must return a value"), not the
   titled TS2322 `Type 'void' is not assignable to type 'string'`, and the type in play is `number`.
5. **L212-213 — flagship example throws at runtime.** `Object.assign(fn, { name })` always throws
   (`name` is non-writable), so neither `console.log` is reached. Use `Object.defineProperty` or a
   different property name.

## T23 — Type Aliases

1. **L154 and L324 — `type Bad = Bad[]` compiles.** Verified: array element position is one of the
   deferred positions TS 3.7 legalized; only `type Direct = Direct` triggers TS2456. Contradicts the
   file's own gotcha 2, and §9's "fix" solves a non-problem.
2. **L331-333 — "reorder the declarations" is not a fix for anything.** Type declarations are
   order-independent; forward references never produce TS2304. TS2304 means the name does not exist.
3. **L235 / L348 — alias-vs-interface error-message asymmetry does not exist.** The printer uses the
   alias symbol when present; alias and interface names print identically. The real phenomenon is
   that *anonymous* and structurally-computed types print expanded.
4. **L202-217 — misattributed fix.** Interfaces are fully generic and fully recursive; the ❌ is just
   a non-generic declaration. Replace with a case aliases genuinely win, e.g. a recursive *union*
   (`type Json = … | Json[] | { [k: string]: Json }`), which cannot be an interface.

## T26 — Refinement Types

1. **L289 — "guarantee consumers cannot construct invalid state" is false** (T03 bug class). Verified
   two-file probe: consumer imports only the type, forges with `as`, tsc exits 0. Contradicts the
   file's own L273-276.
2. **L235 — "All schema libraries produce branded types on `.parse()`" is false.** Branding is opt-in
   (`.brand<"Name">()`, `t.brand`); `z.string().parse(x)` returns plain `string`.
3. **L88 — gotcha 4 backwards.** tsc uses the *alias* name at top level; the brand intersection
   appears only in the nested elaboration.
4. **L242-244, L251-253, L258-263, L142 — quoted error blocks do not match actual output** (top-level
   names `Email`; union normalizes to `Error | Port` with a third elaboration line; source type is
   `$brand<…>`).
5. **L55 — zod version drift.** Under the pinned zod 4.4.3 the inferred type is `string & $brand<"Email">`,
   not the zod-3 `{ [BRAND]: "Email" }`.

## T27 — Erased / Phantom Types

1. **L9 — "or as empty interfaces" is wrong.** Empty interfaces are structurally identical, so every
   tag unifies and the phantom distinction vanishes (verified: `needsFeet(m)` compiles). Tags need a
   `unique symbol`, a string literal, or a distinguishing brand member.
2. **L106 — gotcha 4 false on both halves.** `readonly [__unit]: Unit` is already a covariant
   position, so `Quantity<Unit>` *is* covariant with no changes.
3. **L96 — table row wrong.** A parameter appearing nowhere is *bivariant*, not invariant — all
   instantiations are interchangeable.
4. **L107 — gotcha 5 wrong.** `--strict` produces no unused-type-parameter diagnostic; TS6133 needs
   `noUnusedLocals`/`noUnusedParameters`, which `strict` does not imply.
5. **L241-258 — ❌ does not show invariance and ✅ is a no-op.** Distinct literal tags are rejected
   under covariance too; adding `extends string` changes variance not at all.
6. **L358 — comment claims code compiles when it does not.** Excess-property checking rejects it
   (TS2353).

## T33 — Self Type

1. **L102 (gotcha 4) and L286-297 — TypeScript does not check `this is T` predicates.** The doc says
   `this is string` in a class method is "always an error". Verified: `isString(): this is string`
   compiles clean. TS2677 only fires for *parameter* predicates (`x is T`). This is an unsound spot
   worth documenting as such, not a rejected one.
2. **L286 and L102 — error text reversed.** tsc says "must be assignable **to** its parameter's type",
   not "assignable from".
3. **L269 — `InstanceType<typeof this>` silently loses the polymorphism** the section teaches:
   `typeof this` in a static body resolves to the *declaring* class, so `Derived.create()` returns
   `Base`. Only the `this: T` generic form works.
4. **L99 (gotcha 1) — not "different semantics", a hard error.** `this` as a static return type is
   TS2526. The gotcha's own opening clause contradicts its tail.
5. **L103 (gotcha 5) — assignment does not widen `this`.** `const fn = b.setFlag; fn("x").extended()`
   compiles; the loss comes solely from an explicit base-typed annotation. §13 states this correctly.
6. **L491-499 — ❌ and ✅ have identical signatures**, so the ✅ does not fix the stated "too narrow"
   defect; the real difference is `constructor.name` vs `instanceof` at runtime.

## T34 — never / Bottom Type

1. **L317-323 and L375-380 — the "GOOD" exhaustiveness examples are not exhaustiveness checks.**
   The parameter is a *single object type with a union-typed property* (`{ type: "a" | "b" }`), not a
   discriminated union, so no narrowing occurs and `assertNever` errors **unconditionally — even when
   every case is handled** (verified). §11's real-union version works correctly.
2. **L221-223 — the section heading is an error tsc never emits.** `never[]` **is** assignable to
   `string[]` (gotcha 3 at L84 says so); the real error goes the other direction, and the example
   actually produces a `push` argument error.
3. **L87 (gotcha 6) — unconditional `throw` is necessary but not sufficient.** `never` is inferred
   only for function *expressions* and arrows; function declarations and methods infer `void`.
4. **L232 — `reveal_type` is mypy/Python**, not TypeScript. Retitle to "on hover / in an inferred type".
5. **L206 — quoted type wrong**: tsc reports the literal `'"pending"'`, not `'string'`.

## T36 — Trait Objects

1. **L338 — ✅ "compiler enforces handling both" enforces nothing.** `handle` has an inferred `void`
   return and no `never` guard, so deleting a case compiles clean. The file's own §3 (L81) does it
   correctly with `const _: never = notification`.
2. **L111 / L118 — "abstract classes cannot be used with plain objects" is false.** Abstract instance
   types are structural; a plain object literal and an unrelated non-extending class are both
   assignable. Only `new Exporter()` is blocked.
3. **L322 — "interfaces cannot type member methods against `this`" is false**, and contradicted by
   L96 of the same file, which offers `compare(other: this): number` as an interface example.
4. **L321 / L100 — the performance claim is backwards for TypeScript.** Generics are fully erased —
   no monomorphization, no static dispatch. Example C's two halves emit byte-identical JS.
5. **L9 — Rust analogy wrong.** Rust trait conformance is nominal and explicit (`impl Trait for Type`);
   Go's implicit interfaces are the right analogue for structural conformance.
6. **L197 — arithmetic wrong**: the total is `60.27`, not `56.27`.

## T41 — Match / Conditional Types

1. **L122 — wrong result.** `LeafElem<string[][]>` is `string`, not `string[]` — the recursion bottoms
   out rather than short-circuiting.
2. **L251-252 — the comment says the opposite of what happens.** `len` is a type parameter, not a
   value, and the type works exactly as written (`Result<unknown, 0>` is `"empty"`).
3. **L66 — heading contradicts the code.** There is no tuple wrapping, and the type is distributive
   *by design* — distribution is what produces the intersection.
4. **L94 — literal form is `X`, not `never`.** `never extends string ? X : Y` written literally is
   `X`; the `never` result requires an alias (`D<never>`).
5. **L96 / L111 — depth figure only covers non-tail recursion.** Tail-position recursive conditionals
   run to **1000** iterations (verified: `Count<999>` compiles, `Count<1001>` → TS2589).
6. **L7 — two releases conflated.** Recursive conditional types = 4.1; tail-recursion elimination = 4.5.
7. **L195-196 — homomorphic mapped type preserves `?`.** Result is `{ host: "required"; port?: …;
   debug?: … }`. Add `-?` if a fully-required record is intended.
8. **L419-428 — the "Better" replacement is strictly worse.** It keeps every property required and
   merely widens with `undefined`; the intersection form makes non-`K` properties genuinely omittable.

## T45 — ParamSpec & Variadic

1. **L362-379 — the `Concatenate` analog provides zero type safety.** `F` appears only inside
   `Parameters<F>`/`ReturnType<F>` (non-inference positions), so it falls back to its constraint and
   the wrapper becomes `(...args: any[]) => any`. `wrapped("totally", "wrong", 1, 2, 3)` produces no
   error. Fix: `<A extends unknown[], R>(fn: (retryCount: number, ...args: A) => R): (...args: A) => R`.
2. **L322 — gotcha 1 false on every count.** `[...A, ...B]` is valid as a type literal, three spreads
   work, and `[...infer A, ...infer B]` works. The real restriction (TS1265) is one *unbounded* rest.
   The file's own L33 uses `[...A, ...B]` as an annotation.
3. **L487 — wrong depth.** 12 elements resolves fine; the naive `Reverse` first fails between 45 and 50.
4. **L464/L471 — wrong inferred type.** It infers `(string | number)[]`, not `string[]` or
   `string[] | number[]`.
5. **L476 — `readonly` is stripped.** Because `T extends unknown[]` is mutable, `as const` input
   yields the mutable `["hello", 42]`.
6. **L429 — heading names an error tsc never emits here** (actual: TS2574 "A rest element type must
   be an array type").

## T47 — Gradual Typing

1. **L91 — gotcha 1 does not demonstrate contagion.** `(anyValue as string[]).map(x => …)` gives `x`
   type `string`. Use `anyValue.map(x => …)` for a real example.
2. **L97 — `object` rejects arbitrary property access** (TS2339), and `noUncheckedIndexedAccess` is
   unrelated. The file's own L101 comment contradicts the prose.
3. **L48, L104 — stale error text.** tsc emits `TS18046: 'x' is of type 'unknown'`; "Object is of
   type 'unknown'" is pre-4.4 wording.
4. **L274 — wrong code.** Property access on `unknown` is TS18046, not TS2339; duplicates the correct
   section at L262.
5. **L439-441 — the "GOOD" pattern is itself a compile error.** A double cast through `any` does not
   error, so `@ts-expect-error` above it is TS2578 (unused directive). It only passes the harness
   because the block omits the declaration.
6. **L514-522 — ❌/✅ pair does not show what it claims.** A `(value: any): value is string` predicate
   narrows an `any` exactly as well as the `unknown` version; the ❌ "proves nothing" only because it
   calls the guard as a bare statement instead of in a conditional.

## T49 — Associated Types

1. **L156 — not a silent `never`.** Passing a non-constructor to `InstanceType<C>` is a hard
   constraint error (TS2344) and the fallback type is `any`. The real bound is
   `abstract new (...args: any) => any`.
2. **L452-453 — the "Good" version does not type-check.** Calling `fn` through the type parameter
   yields `unknown`, not assignable to the deferred `ReturnType<F>`. The error is masked from the
   harness because the same fence's "Bad" half carries a `// Error:` comment, marking the whole
   snippet expect-error. Use `<R>(fn: () => R): R`.
3. **L317 — misattributed error.** `class MultiCache<T> implements Cache<T>` is legal and normal; the
   suppressed error is TS2355 for the empty body, nothing to do with `T`.
4. **L134 — Rust analogy wrong.** Rust also allows implementing a generic trait with different type
   arguments; coherence forbids only *overlapping* impls. The real contrast is Rust **associated
   types** (one impl per type) vs generic trait parameters.

## T52 — Literal Types

1. **L316 — ✅ "Compiler shows all missing sites" shows nothing** (the T32 bug class). `handle`
   returns void with no `assertNever`, so adding `"CANCEL"` produces zero diagnostics.
2. **L228 — comment teaches the opposite of the widening rule.** Without `as const`, `typeof OPS` is
   `{ add: string; sub: string }`, so `Operation` is `string`, never `"add" | "sub"` — which is what
   the block's own ❌ heading says.
3. **L91 — `satisfies` preserves literals only conditionally.** With `type Config = { mode: string }`
   the literal widens exactly as with an annotation; preservation requires a literal-union target.
4. **L359 — numeric enums do round-trip.** `g(Status.Pending)`, `g(s)` and `f(0)` all compile; only
   an out-of-range literal is rejected. Use a string enum, or state the real numeric-enum problem.
5. **L265-267 — the ✅ produces no pairs.** `E` is unused, so `CRUD<E>` is not a template literal type
   and `UserActions` contains no `"User"`.
6. **L114 — `Literal['w']` is Python typing syntax**; tsc emits TS2769 "No overload matches this call".

## T54 — Functor / Applicative / Monad

1. **L119, L124, L294 — "you cannot write a single `map` generic over any functor" is false**, and is
   the whole point of fp-ts's defunctionalisation (`URIS` + `Kind<F, A>` + a `Functor1<F>` dictionary).
   Verified: one `genericMap` works for both `Option` and `Array`. The real limits are no *implicit*
   resolution (you pass the dictionary by hand), `F` must be a registered URI, and arity needs
   separate `Kind`/`Kind2` families.
2. **L292-321 — Example B does not demonstrate its own claim.** `parseAndHalve` is monomorphic in
   `Option`; it is ordinary dependency injection, not "generic over a monad".
3. **L116, L323, L140 — Effect's type parameters are in the wrong order.** effect@3.21.4 declares
   `Effect<out A, out E = never, out R = never>` — success first, requirements last.
4. **L27 — `chain` does not union the error types.** fp-ts `chain` is invariant in `E`; the widening
   variant is `chainW`.
5. **L126, L128 — the accumulation advice does not accumulate.** `E.bind` is defined via `chain` and
   short-circuits, and `sequenceS(E.Applicative)` short-circuits too. Accumulation requires
   `E.getApplicativeValidation(S)` (as the file's own Example A correctly uses). Also `fp-ts/These` is
   the analogue of cats' `Ior`, not `Validated`.
6. **L15, L323 — Effect does not use URI-based encoding**; it uses `TypeLambda` HKTs. And collapsing
   everything into one concrete type is the opposite of HKT abstraction; `Option.flatMap` /
   `Either.flatMap` still exist as separate exports.
7. **L197-201 — the "equivalent desugaring" does not type-check.** `TaskEither<E, A>` is a *thunk*
   (`() => Promise<Either<E, A>>`); `.then` does not exist on it.
8. **L116 — `Task<A>` is not thenable**; `await t` yields the function. You must call it (`await t()`).
9. **L3 — `Array.prototype.flatMap` is ES2019**, not ES5/ES6.

## T57 — Typestate

1. **L242 — the "When to Use" showcase enforces nothing** (verified myself). `class Query<State>`
   never references `State`, so `Query<NoTable>` and `Query<HasTable>` are structurally identical and
   `select(Query.begin(), ["id","name"])` — the exact thing the comment calls "a type error" —
   compiles with exit 0. Add `declare private readonly _state: State`.
2. **L115 / L320-323 — the prescribed fix is ineffective.** Unique brands are *not* sufficient: an
   unused type parameter is ignored in structural comparison, so `Db<Closed>` and `Db<Open>` stay
   mutually assignable even with distinct brands. The decisive rule is that the generic must
   *reference* its parameter in a member position — and the ✅ block leaves `class Db<S> { }` untouched.
3. **L116 / L304-307 — the "always rebind" remedy does not work.** `let conn = conn.connect()` is a
   self-referential declaration (TS7022/TS2448), and `let conn = Db.open(); conn = conn.connect();`
   fails once `S` is load-bearing, because `conn` is inferred at the initial state. Recommend
   shadowing in a narrower scope or a single fluent chain.
4. **L270-290 — Antipattern A's ❌ compiles for the wrong reason.** `Conn<S>` never uses `S` and puts
   `query` on every state, so it does not model typestate at all.
5. **L122 — gotcha 8 names the wrong error** for the file's primary technique: `this:`-gated methods
   give TS2684 (`this` context), not TS2339 ("property does not exist"), which comes from the
   per-state-type variant.

## T59 — Existential Types

1. **L185, L210, L216 — the central encapsulation claims do not hold.** "callers cannot store it" /
   "cannot escape the callback" / "never appears in the outer type". `Result` is a free type
   parameter chosen by the caller, so the callback can return the concrete `QueryResult<…>` *and*
   `query` itself — both escape with full types, and `query` stays callable after the transaction
   "closes" (verified). Constrain `Result` if escape must actually be prevented.
2. **L330 — ✅ "Compiler error if we miss a case" produces no diagnostic.** `useShape` has an inferred
   return type, so a missing case silently widens it to `number | undefined`; `--strict` does not
   include `noImplicitReturns`. Annotate the return type or add a `never` arm.
3. **L107 — gotcha 6 describes emission TypeScript does not do.** Types are erased; union-typed and
   interface-typed dispatch emit byte-identical JS. There is no "inline code per variant".
4. **L108 — gotcha 7 wrong on both halves.** `satisfies` never widens (that is its purpose) and the
   full literal type is kept in *all* contexts, not "some". The snippet also does not compile —
   excess-property checking rejects `secret` on a fresh literal.
5. **L181 — Lean analogy backwards.** `Sigma`/`Σ` is a strong pair whose witness is projectable via
   `.fst`; the construct that hides the witness is `Exists` (`∃`) in `Prop`.

## T61 — Recursive Types

1. **L7 and L74 — the "~100 levels" figure is wrong in both directions, and names the wrong error.**
   Non-tail-recursive conditional types (the category this file teaches) fail well under 50; tail-
   recursive ones reach ~1000 (TS 4.5 tail-recursion elimination). Deeply nested *values* fail
   structural comparison with **TS2321 "Excessive stack depth comparing types"**, not TS2589.
2. **L76 — gotcha 3 false.** Type declarations are hoisted; mutually recursive aliases work in any
   order and need no interface workaround. The file's own Example C contradicts it (`Stmt` at L188
   references `Expr`, declared at L194).
3. **L81 — gotcha 8 lists the canonical *accepted* form as rejected.** `type T = { v: T }` is exactly
   what TS 3.7 enabled and compiles fine; only bare `type T = T` is TS2456. The next sentence of the
   same gotcha contradicts it.

## T62 — Mapped Types

1. **L312-319 — the ✗/✓ pair is backwards** and contradicts L123 of the same file. `{ [K in keyof T]:
   T[K] }` **is** homomorphic and preserves both `readonly` and `?`. The "✓" version does not
   *preserve* modifiers — it unconditionally *adds* `readonly`, and looks equivalent only because the
   source was already readonly.
2. **L205 — duplicate remapped keys union, they do not "last wins".** `{ [K in keyof T as "x"]: T[K] }`
   over `{a:string;b:number;c:boolean}` gives `{x: string | number | boolean}`. No information lost.
3. **L209 — `T[K]` is an indexed access, not a naked parameter, so the conditional never
   distributes**; the `[T[K]] extends [V]` remedy is a no-op. The real surprise is the opposite: a
   union-valued property fails `T[K] extends V` and is silently *dropped*.
4. **L208 — arrays are handled correctly** by a homomorphic `DeepReadonly` (`string[]` →
   `readonly string[]`). The suggested guard is backwards — it leaves arrays mutable. Only
   `Function`/`Date`/`RegExp` and other method-bearing built-ins break, as the file's own §9 shows.

## T63 — Template Literal Types

1. **L393 — ✅ "TypeScript enforces exhaustiveness" enforces nothing** (the T32 bug class). Inferred
   return type, no `never` guard, two of four cases omitted → exit 0. Annotate the return type.
2. **L93 — `string` does not pass through unchanged.** `Uppercase<string>` is a deferred intrinsic and
   a strict subtype: assignable *to* `string`, but `string` is not assignable to it.
3. **L327 — wrong resulting type.** `Transform<string>` is `Uppercase<string>`, not `string`. (The
   "no transform" point is right.)
4. **L193 — quoted diagnostic does not exist.** tsc says "**Expression** produces a union type that is
   too complex to represent" (TS2590).

## T64 — Async Iteration

1. **L7 and L67 — `for await...of` accepts sync iterables.** It awaits each yielded value; this is
   legal at every strictness level and under `--downlevelIteration`. Verified across three configs.
   (The `lib` gotcha in row 1 *is* correct — `--lib es2017` gives TS2583.)
2. **L68 — rejection behaviour is wrong.** A rejection inside an async generator surfaces at the
   consumer's `for await` and is catchable there; it is not an unhandled rejection and the generator
   does not silently exit. Verified in node with an `unhandledRejection` listener that never fired.
3. **L250, L254 — `await`-recursion does not grow the stack.** Each `await` unwinds the synchronous
   frame; a 200,000-deep traversal completes without overflow. What grows is the pending-promise
   chain (heap). Reframe as "no backpressure, O(depth) pending promises".
