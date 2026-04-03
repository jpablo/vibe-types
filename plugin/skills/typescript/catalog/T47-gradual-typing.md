# Gradual Typing & `any`

> **Since:** TypeScript 1.0; `unknown` since TypeScript 3.0; `--strict` since TypeScript 2.3

> **Status:** Requires `--strict` (or individual flags) to maximize enforcement

## 1. What It Is

TypeScript is a **gradually typed** language: every JavaScript value is valid TypeScript, and the type system can be engaged at whatever granularity you choose. At one extreme, `any` turns off all type checking for a value — it is assignable to every type and every type is assignable to it, making it a hole in the type system. At the other extreme, `--strict` enables a bundle of flags (`--strictNullChecks`, `--strictFunctionTypes`, `--strictBindCallApply`, `--strictPropertyInitialization`, `--noImplicitAny`, `--noImplicitThis`, `--useUnknownInCatchVariables`) that make the type system as sound as TypeScript's design allows. The `unknown` type (TypeScript 3.0) is the type-safe counterpart to `any`: it accepts all values on input but requires narrowing before any operation. The `@ts-ignore` directive suppresses the next line's errors; `@ts-expect-error` suppresses and also errors if the line is *not* an error (useful for tests). Individual files can opt out with `// @ts-nocheck`.

## 2. What Constraint It Lets You Express

**`unknown` forces you to prove the shape of a value before using it; `any` disables all proofs; `--strict` makes unannotated code default to the safest interpretation rather than silently guessing.**

- A function accepting `unknown` cannot call methods on it without a type guard — the compiler rejects `value.trim()` until `typeof value === "string"` is confirmed.
- `--noImplicitAny` turns every implicit `any` (unannotated parameter, unresolvable inference) into a compile error, forcing explicit annotations at the boundary.
- `--strictNullChecks` makes `null` and `undefined` non-assignable to non-nullable types, catching the billion-dollar mistake.
- Per-file `@ts-ignore` / `@ts-expect-error` allow surgical suppressions without disabling the whole project.

## 3. Minimal Snippet

```typescript
// --- any: no checks at all ---
let danger: any = fetchSomething();
danger.foo.bar.baz(); // OK at compile time — may explode at runtime

// --- unknown: must narrow before use ---
let safe: unknown = fetchSomething();
// safe.trim(); // error — Object is of type 'unknown'

if (typeof safe === "string") {
  safe.trim(); // OK — narrowed to string
}

// --- strictNullChecks: null is not assignable to string ---
// (requires --strictNullChecks or --strict)
function greet(name: string): string {
  return `Hello, ${name.toUpperCase()}`; // OK — name cannot be null
}
// greet(null); // error — Argument of type 'null' is not assignable to parameter of type 'string'

// --- noImplicitAny: unannotated parameters must be explicit ---
// (requires --noImplicitAny or --strict)
// function process(x) { return x; } // error — x has implicit 'any' type
function process(x: unknown): unknown { return x; } // OK — explicit

// --- @ts-expect-error: document a known type violation ---
// @ts-expect-error: legacy API returns untyped object
const raw = legacyApi() as { id: number };

// --- unknown in catch (TypeScript 4.0 useUnknownInCatchVariables, default in --strict) ---
try {
  JSON.parse("{bad json}");
} catch (e) {
  // e is unknown — must narrow before use
  const message = e instanceof Error ? e.message : String(e); // OK
}
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Null Safety** [-> T13](T13-null-safety.md) | `--strictNullChecks` is the primary null-safety mechanism; it is part of `--strict` and makes `null`/`undefined` distinct types rather than assignable to everything. |
| **Type Narrowing** [-> T14](T14-type-narrowing.md) | `unknown` is only useful when paired with narrowing; `typeof`, `instanceof`, and custom type guards are the tools that unlock `unknown` values for actual use. |
| **Conversions & Coercions** [-> T18](T18-conversions-coercions.md) | `as any` followed by `as TargetType` (the double-cast "escape hatch") is the standard way to force a type cast that the compiler would otherwise reject; this erases all safety. |

## 5. Gotchas and Limitations

1. **`any` is contagious** — a single `any` value in a computation poisons its result; `(anyValue as string[]).map(x => x.toUpperCase())` type-checks but `x` is still `any` inside the callback if inference is imprecise.
2. **`unknown` from JSON.parse** — `JSON.parse` returns `any`, not `unknown`; in a strict codebase, immediately cast to `unknown` and narrow with a validator library (Zod, io-ts) before use.
3. **`--strict` is not retroactively safe** — enabling `--strict` on an existing codebase often reveals hundreds of errors; incremental adoption using `// @ts-ignore` or per-directory `tsconfig.json` with `"strict": true` is the common migration path.
4. **`@ts-ignore` vs `@ts-expect-error`** — prefer `@ts-expect-error`; it fails if the suppression is no longer necessary (e.g., after a dependency upgrade fixes the type), preventing stale suppressions from silently hiding real errors.
5. **Type inference fills gaps silently** — TypeScript infers `any` for some unresolvable positions without an error unless `--noImplicitAny` is on; turning on `--strict` after the fact can surface many of these.
6. **`unknown[]` for rest parameters** — variadic rest parameters typed as `...args: any[]` accept anything; typing them as `...args: unknown[]` is stricter but requires callers to narrow before use, which may be impractical for generic adapters.

## 6. Use-Case Cross-References

- [-> UC-04](../usecases/UC04-generic-constraints.md) Use bounds instead of `any` to write generic code that is still type-safe
- [-> UC-16](../usecases/UC16-nullability.md) Enforce non-nullability at the type level via `--strictNullChecks`
