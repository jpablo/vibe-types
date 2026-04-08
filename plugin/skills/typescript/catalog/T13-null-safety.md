# Null Safety

> **Status:** Requires `--strictNullChecks` | **Since:** TypeScript 2.0

## 1. What It Is

Before TypeScript 2.0, `null` and `undefined` were subtypes of every type — assignable to `string`, `number`, or any other type without an error. With `--strictNullChecks` (included in `--strict`), `null` and `undefined` become their own distinct types, not assignable to anything else unless explicitly declared. Absent values must be spelled out in the type: `string | null`, `number | undefined`. **Optional properties** (`x?: T`) are shorthand for `T | undefined`. The **non-null assertion operator** `x!` tells the compiler "trust me, this is not null" — it opts out of safety for a single expression and provides no runtime check. **Optional chaining** `?.` propagates `undefined` without throwing when a chain encounters `null` or `undefined`. **Nullish coalescing** `??` provides a default value for `null` or `undefined` without treating other falsy values (`0`, `""`, `false`) as absent.

## 2. What Constraint It Lets You Express

**Reference types cannot hold `null` or `undefined` unless explicitly declared; the compiler forces handling of all absent-value cases before the value can be used as the non-nullable type.**

- A function typed `(name: string): void` rejects `null` and `undefined` arguments without a cast.
- The compiler tracks narrowing: after `if (x !== null)`, `x` is typed as the non-null type for the rest of the `if` block.
- Optional chaining and nullish coalescing compose to form a safe, terse idiom for deeply nested nullable access.

## 3. Minimal Snippet

```typescript
// Without --strictNullChecks: null is assignable to everything (unsafe)
// With --strictNullChecks: explicit nullable types required

function greet(name: string | null): string {
  // name.toUpperCase(); // error — 'name' is possibly null
  if (name !== null) {
    return `Hello, ${name.toUpperCase()}`; // OK — narrowed to string
  }
  return "Hello, stranger";
}

// Optional property: equivalent to { label?: string | undefined }
interface ButtonProps {
  label?: string;   // string | undefined
  disabled?: boolean;
}

function renderButton(props: ButtonProps): string {
  // props.label.length; // error — possibly undefined
  const text = props.label ?? "Click me"; // OK — nullish coalescing provides default
  return `<button>${text}</button>`;
}

// Optional chaining: propagates undefined instead of throwing
type Config = { db?: { host?: string } };
const config: Config = {};
const host = config.db?.host ?? "localhost"; // OK — string, never throws

// Non-null assertion: opts out of null checking (no runtime guarantee)
function processInput(input: string | null): number {
  return input!.length; // OK at compile time, throws at runtime if input is null
}

// Nullish coalescing vs logical OR
const value = 0;
const withOr  = value || 42; // 42 — treats 0 as falsy (often wrong)
const withNull = value ?? 42; // 0  — only replaces null/undefined
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Type Narrowing** [-> T14](T14-type-narrowing.md) | Null safety and narrowing are inseparable: `if (x !== null)`, truthiness checks, and optional chaining all narrow `T \| null` to `T` in the affirmative branch. |
| **Union Types** [-> T02](T02-union-intersection.md) | `T \| null` is a plain union; null safety is implemented entirely through union types — `null` and `undefined` are just additional union members under `--strictNullChecks`. |
| **Never / Bottom** [-> T34](T34-never-bottom.md) | After checking all cases (including null) in a discriminated union, the `never` type appears in the default branch as the exhaustiveness proof; null is treated as an additional variant. |
| **Discriminated Unions & ADTs** [-> T01](T01-algebraic-data-types.md) | ADT variants can include nullable fields; inside a narrowed variant, further null checks on fields complete the safety chain. |

## 5. Gotchas and Limitations

1. **`--strictNullChecks` is off by default** — projects not using `--strict` must opt in explicitly; mixing strict and non-strict code in a monorepo creates null-safety blind spots.
2. **`!` provides no runtime guarantee** — the non-null assertion operator suppresses the compile error but adds no runtime check; it should be used only when you can prove non-nullability through external invariants.
3. **`undefined` and `null` are distinct types** — `x: string | null` does not accept `undefined`, and `x?: string` (equivalent to `string | undefined`) does not accept `null`. Mixing them requires `string | null | undefined`.
4. **Optional chaining short-circuits the entire chain** — `a?.b?.c` evaluates to `undefined` if any step is `null` or `undefined`, not just the first; a `null` in the middle silently swallows all downstream access without error.
5. **`??` does not help with `false` or `0`** — only `null` and `undefined` trigger the right side; `false ?? "default"` remains `false`. For all falsy values, use `||`.
6. **Definite assignment assertion** — class properties can be marked with `!` (`name!: string`) to assert they will be assigned before use (e.g., in a framework lifecycle hook); this is safe only if the framework guarantees initialization.
7. **JSON.parse returns `any`** — deserialized values are untyped; null safety is not enforced across JSON boundaries without explicit validation and type assertion.
8. **Nested nullability: `(T | null) | null`** — a function that calls another function returning `T | null` and maps over it can produce a doubly-wrapped nullable. TypeScript flattens union members (`(T | null) | null` simplifies to `T | null`), so this is rarely a type-level problem — but it signals a design issue worth a dedicated wrapper type.
9. **`noUncheckedIndexedAccess` is not part of `--strict`** — enabling this flag adds `| undefined` to all array index and index-signature access (`arr[0]` becomes `T | undefined`), matching Rust's `Vec::get` semantics. It is opt-in and off by default even under `--strict`. Without it, `arr[0]` is typed `T` even when the array might be empty.
10. **`exactOptionalPropertyTypes` tightens optional properties** — by default, an optional property `x?: string` accepts `undefined` as an explicit value (`{ x: undefined }`). With `exactOptionalPropertyTypes`, setting a property to `undefined` explicitly is an error; only omitting the property is allowed. This flag is also not included in `--strict`.

## 6. Beginner Mental Model

Think of `string | null` as a **box labeled "string or empty"**. The type checker is a strict inspector who will not let you use the contents of the box as a string until you prove the box is not empty — by checking `if (value !== null)`, using `value ?? default`, or calling `value?.method`. If you write `string` (no `| null`), the box is always full; the compiler guarantees it.

Unlike JavaScript — where any variable can silently be `null` or `undefined` at runtime — `--strictNullChecks` makes absence **visible in the type**. Every callsite knows whether a value can be absent.

Coming from Rust: `string | null` ≈ `Option<String>`, with `!` playing the role of `unwrap()` (both compile without error and both panic/throw at runtime on absent values). Coming from Lean/Haskell: TypeScript lacks a `do`-notation monad, but optional chaining (`?.`) is a limited version of monadic `Option` sequencing — it short-circuits the chain on the first absent value.

## Example A — Chaining nullable lookups (combinator style)

TypeScript has no built-in `map`/`andThen` for `T | null`, but optional chaining composes the common case, and a small helper can fill the gap:

```typescript
type User = { id: number; name: string; teamId: number | null };
type Team = { id: number; lead: string };

const users = new Map<number, User>([
  [1, { id: 1, name: "Alice", teamId: 42 }],
  [2, { id: 2, name: "Bob",   teamId: null }],
]);
const teams = new Map<number, Team>([
  [42, { id: 42, lead: "Carol" }],
]);

// Optional chaining + nullish coalescing: safe deep access
function findTeamLead(userId: number): string | null {
  const user = users.get(userId) ?? null;     // Map.get returns T | undefined
  const teamId = user?.teamId ?? null;        // null if user absent or has no team
  const team = teamId !== null ? (teams.get(teamId) ?? null) : null;
  return team?.lead ?? null;
}

console.log(findTeamLead(1)); // "Carol"
console.log(findTeamLead(2)); // null (Bob has no team)
console.log(findTeamLead(9)); // null (no such user)
```

For repeated patterns, a small utility avoids repetition without a library:

```typescript
function mapNullable<T, U>(value: T | null, fn: (v: T) => U | null): U | null {
  return value === null ? null : fn(value);
}

function findTeamLeadV2(userId: number): string | null {
  const user   = users.get(userId) ?? null;
  const teamId = mapNullable(user, u => u.teamId);
  const team   = mapNullable(teamId, id => teams.get(id) ?? null);
  return mapNullable(team, t => t.lead);
}
```

This is the TypeScript analogue of Lean's `do`-notation or Rust's `and_then` chains on `Option<T>`.

## Example B — Discriminated union with null elimination

A richer alternative to `T | null` that makes the absent-value path carry information:

```typescript
type Found<T> = { found: true;  value: T };
type Missing  = { found: false; reason: string };
type Lookup<T> = Found<T> | Missing;

function lookupUser(id: number): Lookup<User> {
  const user = users.get(id);
  if (!user) return { found: false, reason: `no user with id ${id}` };
  return { found: true, value: user };
}

const result = lookupUser(1);
if (result.found) {
  console.log(result.value.name); // narrowed to Found<User>
} else {
  console.log(result.reason);     // narrowed to Missing
}
```

`T | null` is fine when absence needs no explanation. When it does, a discriminated union encodes both cases with full type safety — no `!`, no runtime surprises.

## Common Type-Checker Errors

### Object is possibly 'null' / 'undefined'

```
// TypeScript
error TS2531: Object is possibly 'null'.
error TS2532: Object is possibly 'undefined'.
```

**Cause:** You accessed a property or called a method on a value whose type includes `null` or `undefined`.
**Fix:** Narrow with `if (x !== null)`, use optional chaining `x?.method()`, or provide a default with `x ?? fallback`.

### Type 'null' is not assignable to type 'T'

```
error TS2322: Type 'null' is not assignable to type 'string'.
```

**Cause:** You assigned `null` (or `undefined`) to a variable or parameter whose type does not include it.
**Fix:** Either change the type to `string | null`, or ensure the value is never null at the assignment point.

### Cannot find name (after optional chain)

Optional chaining returns `T | undefined`, not `T`. Forgetting this causes downstream errors:

```typescript
const host = config.db?.host; // string | undefined
const upper = host.toUpperCase(); // error TS2532 — Object is possibly 'undefined'
const safe  = host?.toUpperCase() ?? "LOCALHOST"; // OK
```

### Property does not exist on type 'never'

```
error TS2339: Property 'x' does not exist on type 'never'.
```

**Cause:** The compiler narrowed a union down to `never` — all cases have been eliminated. This often means a null check contradicts a prior narrowing, or you guarded against the only non-null variant.

## Coming from JavaScript

JavaScript's `null` and `undefined` cause the majority of runtime errors (`Cannot read properties of null`). TypeScript's `--strictNullChecks` is the single most impactful flag for moving those crashes to compile time. Optional chaining (`?.`) and nullish coalescing (`??`) were added to JavaScript itself (ES2020) largely to address the same problem at the language level.

## 7. Use-Case Cross-References

- [-> UC-16](../usecases/UC16-nullability.md) Explicit nullable types and compile-time-forced null handling
- [-> UC-01](../usecases/UC01-invalid-states.md) Prevent invalid absent-value states by making nullability explicit in the type
- [-> UC-08](../usecases/UC08-error-handling.md) `T | null` as a lightweight error-effect type for operations that may produce no result

## Source Anchors

- [TypeScript 2.0 release notes — `--strictNullChecks`](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-2-0.html)
- [TypeScript Handbook — Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- [TypeScript Handbook — `strictNullChecks`](https://www.typescriptlang.org/tsconfig#strictNullChecks)
- [TypeScript Handbook — `noUncheckedIndexedAccess`](https://www.typescriptlang.org/tsconfig#noUncheckedIndexedAccess)
- [TypeScript Handbook — `exactOptionalPropertyTypes`](https://www.typescriptlang.org/tsconfig#exactOptionalPropertyTypes)
- [MDN — Optional chaining (`?.`)](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Optional_chaining)
- [MDN — Nullish coalescing (`??`)](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Nullish_coalescing)
