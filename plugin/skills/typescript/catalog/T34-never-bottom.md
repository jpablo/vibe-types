# Never & Bottom Type

> **Since:** TypeScript 2.0

## 1. What It Is

`never` is TypeScript's **bottom type**: it is a subtype of every type and is inhabited by no values. It arises naturally in several situations: a function that always throws or loops forever has return type `never`; a variable's type becomes `never` when control-flow analysis determines that no value can reach a particular point (the intersection of two incompatible types is `never`; narrowing a `string` with `=== 42` leaves `never`); the intersection of incompatible union arms is `never`. The most important deliberate use of `never` is **exhaustiveness checking**: in the `default` branch of a `switch` over a discriminated union, assigning the switched value to a `never`-typed variable is a compile error if any variant remains unhandled — the compiler proves all variants were covered by the fact that control flow reaches the `default` branch only when the type is `never`.

## 2. What Constraint It Lets You Express

**Mark branches as provably unreachable; force exhaustive handling of all union variants at compile time; express that a function can never return normally.**

- Adding a new variant to a discriminated union causes a compile error at every exhaustiveness check site, ensuring no handler is forgotten.
- Functions with return type `never` cannot be called in positions that expect a value — they are guaranteed to not produce one.
- `never` in a union simplifies: `string | never` is `string`; `never` as an intersection with anything is `never`.

## 3. Minimal Snippet

```typescript
// --- assertNever: exhaustiveness helper ---
function assertNever(x: never, message?: string): never {
  throw new Error(message ?? `Unexpected value: ${JSON.stringify(x)}`);
}

// --- Discriminated union switch with exhaustiveness check ---
type Shape =
  | { kind: "circle"; radius: number }
  | { kind: "rectangle"; width: number; height: number }
  | { kind: "triangle"; base: number; height: number };

function area(shape: Shape): number {
  switch (shape.kind) {
    case "circle":
      return Math.PI * shape.radius ** 2;
    case "rectangle":
      return shape.width * shape.height;
    case "triangle":
      return 0.5 * shape.base * shape.height;
    default:
      // If a new variant is added to Shape and this switch is not updated,
      // `shape` will not narrow to `never` here — compile error
      return assertNever(shape); // error if any case is unhandled
  }
}

// --- never from incompatible intersection ---
type Impossible = string & number; // never — no value can be both

// --- never as unreachable branch ---
function requireString(x: string | number) {
  if (typeof x === "string") {
    return x.toUpperCase(); // OK — string
  } else if (typeof x === "number") {
    return x.toFixed(2);    // OK — number
  } else {
    const _: never = x;    // OK — no other types possible; would error if x could be something else
  }
}

// --- Function that never returns ---
function fail(message: string): never {
  throw new Error(message);
}

function getOrFail<T>(value: T | null, message: string): T {
  return value ?? fail(message); // OK — fail() returns never, which is T in this position
}
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Algebraic Data Types** [-> T01](T01-algebraic-data-types.md) | Exhaustiveness checking with `never` is the canonical companion to discriminated unions; the `default: assertNever(x)` pattern is the standard way to prove all ADT variants are handled. |
| **Type Narrowing** [-> T14](T14-type-narrowing.md) | `never` is the natural result of TypeScript's narrowing: narrowing a value through all its possible types leaves `never` in the fallthrough branch; the compiler propagates this through all control paths. |
| **Union & Intersection Types** [-> T02](T02-union-intersection.md) | `never` is the identity element for unions (`T \| never` = `T`) and the annihilator for intersections (`T & never` = `never`); conditional types use this to filter union members by producing `never` for excluded members. |
| **Conditional Types** [-> T41](T41-match-types.md) | Conditional types distribute over unions; producing `never` for unwanted members and then simplifying via `T \| never` = `T` is the mechanism behind `Exclude<T, U>`, `Extract<T, U>`, and `NonNullable<T>`. |
| **Callable Types** [-> T22](T22-callable-typing.md) | A callback typed as `(msg: string) => never` signals to the caller that invoking it ends control flow; the compiler marks code after such a call as unreachable, just as with an inline `throw`. |

## 5. Gotchas and Limitations

1. **`never` only enforces exhaustiveness if you use it** — TypeScript does not automatically error on missing `switch` cases; you must explicitly route the `default` branch through a `never`-typed position (variable assignment or `assertNever` call) to get the compile error.
2. **`never` from over-narrowing is silent** — if a conditional or narrowing produces `never` unexpectedly (e.g., conflicting constraints in a generic), TypeScript may not report an error at the `never` site but will error at use sites with cryptic messages.
3. **`never[]` is assignable to any array** — because `never` is a subtype of all types, `never[]` is assignable to `string[]`, `number[]`, etc.; an empty generic array can silently become `never[]` if inference fails.
4. **`never` in generic return types** — a generic function that returns `never` under some condition (`T extends string ? string : never`) will fail to compile at call sites where the branch resolves to `never`, which may be surprising if the `never` was meant to be a fallback.
5. **`assertNever` must have a `never` parameter** — if the `default` branch is unreachable but the function signature accepts `unknown`, the exhaustiveness check is bypassed; the parameter must be typed `never` to trigger the error.
6. **`throw` infers `never` only for unconditional throws** — conditional throws (`if (x) throw new Error()`) do not cause the surrounding function to be typed as `never`-returning; only unconditional throws or infinite loops do.
7. **`void` vs `never`** — `void` means "the caller ignores the return value"; `never` means "the function cannot return at all." A function with an explicit `return undefined` has type `() => undefined`. Annotating it `() => never` is a compile error — `never` requires every code path to diverge, not just to return nothing.

   ```typescript
   function returnsVoid(): void { return undefined; }   // OK
   function returnsUndefined(): undefined { return undefined; } // OK
   function diverges(): never { throw new Error(); }    // OK

   // Mistaken usage:
   function bad(): never {
     console.log("hi");
     // error TS2534: A function returning 'never' cannot have a reachable end point
   }
   ```

8. **`never` from failed type inference** — when TypeScript cannot resolve a conditional type or generic constraint, it may silently default a type parameter to `never` rather than reporting an inference failure. The result is a cascade of cryptic errors at use sites. The fix is usually to supply an explicit type argument or add a constraint to the input, not to patch the `never` downstream.

## 6. Beginner Mental Model

Think of `never` as a **black hole** in the type system. A function returning `never` is a one-way street: execution enters but never comes back. Because a value of type `never` can never actually exist, TypeScript is willing to accept it as any type you need — a `never` value would satisfy any obligation if it could exist, and since it cannot, there is no contradiction.

In the type hierarchy:
- `unknown` is at the top (every type is assignable to it).
- `never` is at the bottom (it is assignable to every type).
- Every concrete type sits between them: `never extends string extends unknown`.

This bottom-type position has two practical consequences:
- **Assignability flows up:** a `never`-returning expression (`throw`, `fail()`) can appear in any branch regardless of the expected type.
- **Narrowing flows down:** when control-flow analysis has eliminated every possible type for a variable, its type becomes `never` — the compiler has proven the branch is impossible.

`never | T` = `T` (identity for unions) and `never & T` = `never` (annihilator for intersections) follow directly from `never` being the bottom type.

## 7. Example A — Distributive Conditional Types and Union Filtering

Conditional types distribute over union members when the checked type is a bare type parameter. Branches that evaluate to `never` drop that member from the result union, because `T | never` = `T`. This is the mechanism behind the built-in utility types:

```typescript
// How Exclude is implemented in the standard library:
type Exclude<T, U> = T extends U ? never : T;

type A = Exclude<string | number | boolean, number>;
//   A = string | boolean  (number branch produced never, then simplified away)

// How NonNullable is implemented:
type NonNullable<T> = T extends null | undefined ? never : T;

type B = NonNullable<string | null | undefined>;
//   B = string

// Custom: keep only function-shaped members of a union
type FunctionMembers<T> = T extends (...args: never[]) => unknown ? T : never;

type C = FunctionMembers<string | (() => void) | number | ((x: number) => string)>;
//   C = (() => void) | ((x: number) => string)
```

The `never[]` in `(...args: never[]) => unknown` is the correct way to say "a function that accepts any arguments" in a contravariant position — `never` as an element type means the array can never be populated, which is vacuously compatible with any argument list.

## 8. Example B — `never`-Returning Functions as Callbacks

A function typed as `(msg: string) => never` communicates to the compiler that calling it ends the current control path. This is useful for error-handler registries and result-unwrapping utilities:

```typescript
type ErrorHandler = (message: string) => never;

function withErrorHandler(
  op: () => string,
  onError: ErrorHandler,
): string {
  try {
    return op();
  } catch (err) {
    onError(String(err));
    // The compiler knows onError() returns never, so this line is unreachable.
    // No return needed here; the function's return type string is still satisfied.
  }
}

function panic(msg: string): never {
  throw new Error(msg);
}

const result = withErrorHandler(() => "hello", panic); // OK

// --- never as a utility for unwrapping Results ---
type Result<T, E> =
  | { ok: true; value: T }
  | { ok: false; error: E };

function unwrap<T, E>(result: Result<T, E>, onError: (e: E) => never): T {
  if (result.ok) return result.value;
  return onError(result.error); // type-safe: onError() returns never, which widens to T
}

const val = unwrap({ ok: true, value: 42 }, (e) => { throw new Error(String(e)); });
//    val: number
```

## 9. Common Type-Checker Errors

### `Argument of type 'X' is not assignable to parameter of type 'never'`

The `assertNever` call received a value of type `X`, meaning a variant of the union was not handled above it. Add a branch that narrows `X` before the `default` case.

```typescript
type Status = "ok" | "error" | "pending";

function describe(s: Status): string {
  switch (s) {
    case "ok": return "all good";
    case "error": return "something failed";
    // "pending" is unhandled
    default: return assertNever(s);
    //   error: Argument of type 'string' is not assignable to parameter of type 'never'
    //   Fix: add  case "pending": return "in progress";
  }
}
```

### `A function returning 'never' cannot have a reachable end point`

A function annotated `(): never` has a code path that can return normally (including an implicit `return undefined`). Every path must diverge.

### `Type 'X' is not assignable to type 'never'` (in a variable assignment)

Appearing as `const _: never = x` in a `default` branch usually means the same as the first error above — `x` still has a non-`never` type, so a variant is unhandled.

### `Type 'never[]' is not assignable to type 'string[]'` (or similar)

Appears when an empty array literal is inferred as `never[]` and then used where a typed array is expected. Fix by annotating the variable:

```typescript
const items = [];          // inferred: never[]
items.push("hello");       // error: Argument of type 'string' is not assignable to parameter of type 'never'

const items2: string[] = []; // OK
```

### Unexpectedly seeing `never` in `reveal_type` output

This almost always means a conditional type branch evaluated to `never` due to failed inference. Check the type arguments flowing into the conditional; the fix is usually a missing constraint or an incorrect extends clause.

## 10. Use-Case Cross-References

- [-> UC-03](../usecases/UC03-exhaustiveness.md) Use `never` and `assertNever` to enforce compile-time exhaustive handling of every discriminated union variant
- [-> UC-01](../usecases/UC01-invalid-states.md) Use `never` in intersection types to make invalid state combinations unrepresentable at the type level

## 11. Source Anchors

- [TypeScript Handbook — Narrowing: The `never` type](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#the-never-type)
- [TypeScript Handbook — Functions: `never` return type](https://www.typescriptlang.org/docs/handbook/2/functions.html#never)
- [TypeScript Handbook — Conditional Types: distributive conditional types](https://www.typescriptlang.org/docs/handbook/2/conditional-types.html#distributive-conditional-types)
- TypeScript source: `lib/lib.es5.d.ts` — `Exclude`, `Extract`, `NonNullable` implementations
