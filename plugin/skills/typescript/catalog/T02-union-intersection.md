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

## 5. Gotchas and Limitations

1. **Conflicting property types in intersections produce `never`** — `{ x: string } & { x: number }` yields `{ x: never }`, making the type uninhabited. This silently produces an unusable type rather than a compile error at the intersection site.
2. **Union member ordering affects error messages** — TypeScript displays union members in declaration order; putting the "primary" type first improves diagnostics.
3. **Excess property checks only apply at fresh object literals** — assigning a variable of type `A` to a context requiring `A | B` skips excess property checks; only direct object literals are checked strictly.
4. **Distributive conditional types treat union members individually** — `T extends string ? "yes" : "no"` applied to `string | number` yields `"yes" | "no"`, not `"no"`. This is intentional but surprises newcomers.
5. **Intersecting function types** — `((x: string) => void) & ((x: number) => void)` creates an overloaded function type, not an error, but calling it requires satisfying both overloads simultaneously, which is rarely what you want.
6. **`null` and `undefined` in unions** — before `--strictNullChecks`, all types implicitly included `null | undefined`; under strict mode these are explicit union members, which is the correct behavior but requires migrating older code.

## Coming from JavaScript

JavaScript has no type-level union or intersection. The closest runtime equivalent is duck-typing: a function that accepts "either shape" and uses `typeof` or property checks at runtime. TypeScript's union/intersection types make those runtime patterns statically checked, moving errors from runtime crashes to compile time.

## 6. Use-Case Cross-References

- [-> UC-01](../usecases/UC01-invalid-states.md) Union types prevent invalid state by restricting values to named variants
- [-> UC-05](../usecases/UC05-structural-contracts.md) Intersection types compose structural contracts without inheritance
- [-> UC-08](../usecases/UC08-error-handling.md) `Result<T, E>` as a union type for explicit, typed error handling
