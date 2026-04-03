# Type Narrowing & Exhaustiveness

> **Since:** TypeScript 2.0 (type guards); TypeScript 4.4 (control-flow analysis for aliased conditions)

## 1. What It Is

**Type narrowing** is TypeScript's control-flow analysis: the compiler tracks which types are possible at each point in the code based on the checks performed before that point. After an `if (x !== null)` check, `x` is typed as the non-null version for the rest of the `if` block. After a `switch (shape.kind)` on a discriminated union, each `case` branch has `shape` narrowed to the exact variant. Narrowing mechanisms include: `typeof` (primitive type), `instanceof` (class prototype chain), `in` operator (property presence), discriminant property checks (literal equality), truthiness narrowing, equality narrowing (`=== / !==`), user-defined **type guards** (`function isString(x: unknown): x is string`), and **assertion functions** (`function assert(x: unknown): asserts x is string`). **Exhaustiveness** is enforced by assigning the value in the `default` branch to a `never`-typed variable: if any variant is unhandled, the value is not `never`, causing a compile error.

## 2. What Constraint It Lets You Express

**After a check, the type in each branch is narrowed to the most specific type consistent with the check; a `switch` over all discriminated union variants fails to compile if any variant is missing a case.**

- The compiler understands that `if (typeof x === "string")` makes `x` a `string` in the `then` branch and narrows the `else` branch by removing `string` from the union.
- User-defined type guards encode arbitrary runtime checks as compile-time narrowing, extending control-flow analysis beyond built-in predicates.
- The `never` exhaustiveness check turns adding a new variant into a compile error at every unupdated switch site.

## 3. Minimal Snippet

```typescript
// Discriminated union with exhaustive switch
type Shape =
  | { kind: "circle";    radius: number }
  | { kind: "rectangle"; width: number; height: number }
  | { kind: "triangle";  base: number; height: number };

function area(shape: Shape): number {
  switch (shape.kind) {
    case "circle":
      return Math.PI * shape.radius ** 2;     // narrowed to circle variant
    case "rectangle":
      return shape.width * shape.height;       // narrowed to rectangle variant
    case "triangle":
      return 0.5 * shape.base * shape.height; // narrowed to triangle variant
    default: {
      const _exhaustive: never = shape; // error if a new variant is added without a case
      return _exhaustive;
    }
  }
}

// typeof narrowing
function stringify(x: string | number | boolean): string {
  if (typeof x === "string")  return x.toUpperCase();  // string
  if (typeof x === "number")  return x.toFixed(2);     // number
  return x ? "yes" : "no";                             // boolean
}

// User-defined type guard
interface Cat { meow(): void }
interface Dog { bark(): void }

function isCat(animal: Cat | Dog): animal is Cat {
  return "meow" in animal; // runtime check
}

function speak(animal: Cat | Dog): void {
  if (isCat(animal)) {
    animal.meow(); // OK — narrowed to Cat
  } else {
    animal.bark(); // OK — narrowed to Dog
  }
}

// Assertion function
function assertString(x: unknown): asserts x is string {
  if (typeof x !== "string") throw new TypeError("Expected string");
}

function process(raw: unknown): string {
  assertString(raw); // throws if not string; after this line, raw is string
  return raw.toUpperCase(); // OK — narrowed to string
}
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Discriminated Unions & ADTs** [-> T01](T01-algebraic-data-types.md) | Discriminated union narrowing is the primary consumer of control-flow analysis; the discriminant field is the cue that drives the `switch` narrowing. |
| **Union Types** [-> T02](T02-union-intersection.md) | Every narrowing step progressively eliminates union members; after all members are handled the remainder is `never`. |
| **Null Safety** [-> T13](T13-null-safety.md) | Null narrowing is the most common narrowing operation: `x !== null` removes `null` from `x`'s type in the true branch. |
| **Never / Bottom** [-> T34](T34-never-bottom.md) | `never` is the type that results when all union members have been narrowed away; the exhaustiveness trick exploits the fact that assigning to `never` is only valid when the type is actually `never`. |
| **Literal Types** [-> T52](T52-literal-types.md) | Discriminant fields must be literal types; literal equality checks are the trigger for discriminated-union narrowing. |

## 5. Gotchas and Limitations

1. **Narrowing does not survive function boundaries** — passing a narrowed value to another function loses the narrowing; the callee sees the original union type. Use type guards or assertion functions to re-establish narrowing inside the callee.
2. **Type aliases for conditions (TS 4.4)** — before TypeScript 4.4, assigning a narrowing condition to a `const` alias (`const isString = typeof x === "string"`) and then using the alias in an `if` did not narrow; TypeScript 4.4 fixed this for `const` discriminant aliases.
3. **`in` narrowing requires the property to be optional or missing** — `"x" in obj` narrows correctly when `x` is optional; if `x` is present on all members of the union, the `in` check does not meaningfully narrow.
4. **Type guards are trust-based** — the body of a user-defined type guard is not verified; `function isString(x: unknown): x is string { return true; }` compiles without error but is incorrect. Tests are the only safety net.
5. **Assertion functions require `asserts` in the return type annotation** — without the explicit annotation, TypeScript does not treat the function as an assertion and no narrowing occurs.
6. **Control-flow analysis is intraprocedural** — TypeScript analyzes narrowing within a single function body; cross-function narrowing (e.g., narrowing in a callback) may not propagate as expected.
7. **Narrowing through truthiness is imprecise with `0`, `""`, and `false`** — `if (x)` narrows out `null`, `undefined`, `0`, `""`, and `false`; if `0` is a valid value for `x: number | null`, use `!== null` instead.

## Coming from JavaScript

JavaScript developers use `typeof`, `instanceof`, and property checks at runtime for the same purpose. TypeScript's innovation is making the compiler understand these runtime checks and use them to narrow the *static* type — so that after the check, you get compile-time autocomplete and error detection appropriate to the narrowed type, not just the original broad type.

## 6. Use-Case Cross-References

- [-> UC-03](../usecases/UC03-exhaustiveness.md) Exhaustive variant handling with the `never` check pattern
- [-> UC-01](../usecases/UC01-invalid-states.md) Narrowing prevents access to variant-specific fields on the wrong variant
- [-> UC-16](../usecases/UC16-nullability.md) Null narrowing as the primary mechanism for safe nullable value access
