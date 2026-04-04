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

## Coming from JavaScript

JavaScript's `null` and `undefined` cause the majority of runtime errors (`Cannot read properties of null`). TypeScript's `--strictNullChecks` is the single most impactful flag for moving those crashes to compile time. Optional chaining (`?.`) and nullish coalescing (`??`) were added to JavaScript itself (ES2020) largely to address the same problem at the language level.

## 6. Use-Case Cross-References

- [-> UC-16](../usecases/UC16-nullability.md) Explicit nullable types and compile-time-forced null handling
- [-> UC-01](../usecases/UC01-invalid-states.md) Prevent invalid absent-value states by making nullability explicit in the type
- [-> UC-08](../usecases/UC08-error-handling.md) `T | null` as a lightweight error-effect type for operations that may produce no result
