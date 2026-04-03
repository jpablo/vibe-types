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

## 5. Gotchas and Limitations

1. **`never` only enforces exhaustiveness if you use it** — TypeScript does not automatically error on missing `switch` cases; you must explicitly route the `default` branch through a `never`-typed position (variable assignment or `assertNever` call) to get the compile error.
2. **`never` from over-narrowing is silent** — if a conditional or narrowing produces `never` unexpectedly (e.g., conflicting constraints in a generic), TypeScript may not report an error at the `never` site but will error at use sites with cryptic messages.
3. **`never[]` is assignable to any array** — because `never` is a subtype of all types, `never[]` is assignable to `string[]`, `number[]`, etc.; an empty generic array can silently become `never[]` if inference fails.
4. **`never` in generic return types** — a generic function that returns `never` under some condition (`T extends string ? string : never`) will fail to compile at call sites where the branch resolves to `never`, which may be surprising if the `never` was meant to be a fallback.
5. **`assertNever` must have a `never` parameter** — if the `default` branch is unreachable but the function signature accepts `unknown`, the exhaustiveness check is bypassed; the parameter must be typed `never` to trigger the error.
6. **`throw` infers `never` only for unconditional throws** — conditional throws (`if (x) throw new Error()`) do not cause the surrounding function to be typed as `never`-returning; only unconditional throws or infinite loops do.

## 6. Use-Case Cross-References

- [-> UC-03](../usecases/UC03-exhaustiveness.md) Use `never` and `assertNever` to enforce compile-time exhaustive handling of every discriminated union variant
- [-> UC-01](../usecases/UC01-invalid-states.md) Use `never` in intersection types to make invalid state combinations unrepresentable at the type level
