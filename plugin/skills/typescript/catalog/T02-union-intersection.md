# Union & Intersection Types

> **Since:** TypeScript 1.4 (union types); TypeScript 2.1 (intersection types)

## 1. What It Is

TypeScript's **union type** `A | B` expresses a value that is *either* `A` or `B` — only the properties common to both are accessible without narrowing. **Intersection type** `A & B` expresses a value that is *simultaneously* both `A` and `B` — every property from both types is available. Unions are the foundation for discriminated unions, nullable types, and open polymorphism without class hierarchies. Intersections are the primary mechanism for composing capabilities (mixins, role objects, merged option shapes) purely at the type level, without runtime inheritance. Both operators distribute over generics and conditional types in ways that enable advanced type-level programming.

## 2. What Constraint It Lets You Express

**Unions enforce that callers handle all possible shapes; intersections enforce that a value satisfies every requirement simultaneously — both without requiring a class hierarchy.**

- A union `A | B` is assignable to a context expecting `A` only after narrowing; attempting to access a property that exists only on `B` is a compile error without a guard.
- An intersection `A & B` is assignable wherever either `A` or `B` is expected; it can be used to "mix in" a capability type onto an existing type without inheritance.
- Unions and intersections compose: `(A & B) | (C & D)` is a valid type expressing two distinct capability bundles.

## 3. Minimal Snippet

```typescript
// Union: Result type — caller must narrow before accessing variant fields
type Result<T, E> = { ok: true; value: T } | { ok: false; error: E };

function divide(a: number, b: number): Result<number, string> {
  if (b === 0) return { ok: false, error: "Division by zero" };
  return { ok: true, value: a / b };
}

const r = divide(10, 2);
// r.value; // error — 'value' does not exist on the 'error' variant
if (r.ok) {
  console.log(r.value); // OK — narrowed to { ok: true; value: number }
}

// Intersection: compose capability interfaces without inheritance
interface Loggable {
  log(message: string): void;
}

interface Storable {
  save(): Promise<void>;
}

type LoggableStorable = Loggable & Storable;

function process(service: LoggableStorable): void {
  service.log("saving..."); // OK
  service.save();           // OK
}

// Any object satisfying both interfaces works — no shared base class needed
const myService: LoggableStorable = {
  log: (msg) => console.log(msg),
  save: async () => { /* persist */ },
};
process(myService); // OK
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Discriminated Unions & ADTs** [-> T01](T01-algebraic-data-types.md) | Discriminated unions are the most powerful use of union types: each member is a distinct object shape with a literal discriminant, enabling exhaustive narrowing via control-flow analysis. |
| **Type Narrowing** [-> T14](T14-type-narrowing.md) | Unions require narrowing before variant-specific properties are accessible; `typeof`, `instanceof`, discriminant checks, and user-defined type guards all narrow unions. |
| **Structural Typing** [-> T07](T07-structural-typing.md) | Intersection types rely on structural compatibility: `A & B` is valid as long as the property sets of `A` and `B` are compatible (conflicting property types produce `never` for that property). |
| **Interfaces & Structural Contracts** [-> T05](T05-type-classes.md) | Intersecting interfaces is the idiomatic alternative to multi-interface inheritance; `interface C extends A, B` and `type C = A & B` are nearly equivalent for object types. |
| **Literal Types** [-> T52](T52-literal-types.md) | String, number, and boolean literals are the building blocks of literal union types (`"GET" \| "POST"`, `1 \| 2 \| 3`). Literal unions are the TypeScript equivalent of Python's `Literal["GET", "POST"]` or a closed enum. |
| **`never` and Bottom Type** [-> T34](T34-never-bottom.md) | `never` is the identity element for unions (`T \| never = T`) and the absorbing element for intersections (`T & never = never`). `unknown` is the absorbing element for unions (`T \| unknown = unknown`) and the identity for intersections (`T & unknown = T`). Exhaustiveness checks exploit the fact that narrowing all union members leaves `never`. |
| **Template Literal Types** [-> T63](T63-template-literal-types.md) | Unions distribute over template literal positions: `` `${"GET" \| "POST"} /api` `` expands to `` "GET /api" \| "POST /api" ``. |
| **Mapped Types** [-> T62](T62-mapped-types.md) | Mapping over a union key type produces a union of mapped results; intersections can merge mapped shapes. |

## 5. Gotchas and Limitations

1. **Conflicting property types in intersections produce `never`** — `{ x: string } & { x: number }` yields `{ x: never }`, making the type uninhabited. This silently produces an unusable type rather than a compile error at the intersection site.
2. **Union member ordering affects error messages** — TypeScript displays union members in declaration order; putting the "primary" type first improves diagnostics.
3. **Excess property checks only apply at fresh object literals** — assigning a variable of type `A` to a context requiring `A | B` skips excess property checks; only direct object literals are checked strictly.
4. **Distributive conditional types treat union members individually** — `T extends string ? "yes" : "no"` applied to `string | number` yields `"yes" | "no"`, not `"no"`. This is intentional but surprises newcomers. Wrap `T` in a tuple (`[T] extends [string]`) to suppress distribution.
5. **Intersecting function types** — `((x: string) => void) & ((x: number) => void)` creates an overloaded function type, not an error, but calling it requires satisfying both overloads simultaneously, which is rarely what you want.
6. **`null` and `undefined` in unions** — before `--strictNullChecks`, all types implicitly included `null | undefined`; under strict mode these are explicit union members, which is the correct behavior but requires migrating older code.
7. **Literal types widen without annotation** — `let method = "GET"` infers `string`, not `"GET"`. Use `const method = "GET"` (infers `"GET"`), an explicit annotation, or `as const` on arrays: `["GET", "POST"] as const` gives `readonly ["GET", "POST"]` whose elements are the narrow literal types.
8. **Unions are not inferred from if/ternary branches** — TypeScript widens to the common supertype, not a union, for many expression forms. Annotate the binding explicitly or use `as const` when you need the union preserved.
9. **`A & B` where A and B are primitives is `never`** — `string & number` is immediately `never`. This is correct (no value inhabits both) but can appear unexpectedly in generic code.

## Beginner Mental Model

Think of a **union type** as a package that could contain exactly one of several items — you must open it and check which item is inside before using it. Think of an **intersection type** as a checklist: the value must have every item on the list checked off before it is accepted.

- `A | B` widens the set of accepted values ("either will do").
- `A & B` narrows the set of accepted values ("must satisfy everything").

Coming from JavaScript: `typeof x === "string"` and property-existence checks are the runtime patterns TypeScript's union narrowing makes statically verified. Coming from Rust: `enum` variants ≈ discriminated union members; `T: Clone + Debug` trait bounds ≈ intersection types. Coming from Scala 3: TypeScript's `A | B` and `A & B` syntax maps directly.

## Coming from JavaScript

JavaScript has no type-level union or intersection. The closest runtime equivalent is duck-typing: a function that accepts "either shape" and uses `typeof` or property checks at runtime. TypeScript's union/intersection types make those runtime patterns statically checked, moving errors from runtime crashes to compile time.

## Example A — Literal Union as a Closed Set

Literal unions restrict a parameter to a specific set of values, equivalent to Python's `Literal["GET", "POST"]` or Rust's enum variants. The type checker rejects values outside the set and enables exhaustive handling.

```typescript
type HttpMethod = "GET" | "POST" | "PUT" | "DELETE";

function fetch(url: string, method: HttpMethod): Promise<Response> {
  return window.fetch(url, { method });
}

fetch("/api/users", "GET");     // OK
fetch("/api/users", "PATCH");   // error: Argument of type '"PATCH"' is not assignable
                                //        to parameter of type 'HttpMethod'

// Exhaustive handling: the compiler proves all cases are covered
function assertNever(x: never): never {
  throw new Error(`Unhandled method: ${String(x)}`);
}

function describe(method: HttpMethod): string {
  switch (method) {
    case "GET":    return "read";
    case "POST":   return "create";
    case "PUT":    return "update";
    case "DELETE": return "remove";
    default:       return assertNever(method); // compile error if a case is missing
  }
}
```

If you add `"PATCH"` to `HttpMethod` without updating the switch, `assertNever(method)` becomes a type error: `Argument of type '"PATCH"' is not assignable to parameter of type 'never'`. This is the TypeScript analogue of Rust's exhaustive `match` and Python's `assert_never()`.

## Example B — Intersection for Capability Composition

Intersections are the idiomatic way to compose capabilities without inheritance. This is the TypeScript analogue of Rust's `T: Clone + Debug` trait bounds or Lean's multiple type-class constraints.

```typescript
interface Serializable {
  serialize(): string;
}

interface Validatable {
  validate(): boolean;
}

// Intersection: the value must satisfy both interfaces simultaneously
function processIfValid<T extends Serializable & Validatable>(item: T): string | null {
  return item.validate() ? item.serialize() : null;
}

// Build an intersection at the call site — no shared base class required
const record = {
  data: { id: 1 },
  serialize() { return JSON.stringify(this.data); },
  validate() { return this.data.id > 0; },
};

processIfValid(record); // OK — satisfies both Serializable and Validatable
```

## Common Compiler Errors

### Accessing a property that does not exist on all union members

```
error TS2339: Property 'value' does not exist on type
  '{ ok: true; value: number } | { ok: false; error: string }'.
  Property 'value' does not exist on type '{ ok: false; error: string }'.
```

**Cause:** You accessed a property that exists on only one union member without narrowing first.
**Fix:** Add a discriminant check (`if (r.ok)`) or a `typeof`/`instanceof` guard before accessing the property.

### Incompatible types in an intersection produce `never`

```
type Bad = { x: string } & { x: number };
// Bad["x"] is `never` — no value can satisfy both `string` and `number`
```

**Cause:** Both sides of `&` declare the same property with incompatible types.
**Fix:** Ensure the property types are compatible, or rename one of the properties.

### Argument is not assignable to a literal union

```
error TS2345: Argument of type 'string' is not assignable to parameter
  of type '"GET" | "POST" | "PUT" | "DELETE"'.
```

**Cause:** A `string`-typed variable was passed where a literal union is expected. The variable widened from its initializer.
**Fix:** Use `const` instead of `let`, add an explicit type annotation (`const method: HttpMethod = "GET"`), or assert with `as const`.

### Missing exhaustiveness — `never` leaks into return type

```
error TS2345: Argument of type '"PATCH"' is not assignable to parameter of type 'never'.
```

**Cause:** A new union member was added but a `switch`/`if` chain does not handle it, reaching the `assertNever` call.
**Fix:** Add the missing case branch for the new member.

## 6. Use-Case Cross-References

- [-> UC-01](../usecases/UC01-invalid-states.md) Union types prevent invalid state by restricting values to named variants
- [-> UC-05](../usecases/UC05-structural-contracts.md) Intersection types compose structural contracts without inheritance
- [-> UC-08](../usecases/UC08-error-handling.md) `Result<T, E>` as a union type for explicit, typed error handling

## Source Anchors

- [TypeScript Handbook — Union Types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#union-types)
- [TypeScript Handbook — Intersection Types](https://www.typescriptlang.org/docs/handbook/2/objects.html#intersection-types)
- [TypeScript Handbook — Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- [TypeScript Handbook — Literal Types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#literal-types)
- [TypeScript Deep Dive — Type Guard](https://basarat.gitbook.io/typescript/type-system/typeguard)
- TypeScript source: `src/compiler/checker.ts` — `getUnionType`, `getIntersectionType`
