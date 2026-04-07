# Structural Typing

> **Since:** TypeScript 1.0 (core design principle)

## 1. What It Is

TypeScript is a **structurally typed** language: two types are compatible if they have compatible shapes, regardless of their names or declaration sites. A value of type `Cat` is assignable to a variable of type `Animal` not because `Cat extends Animal` was declared, but because `Cat` has at least all the properties that `Animal` requires — with compatible types. This is TypeScript's most fundamental and distinguishing design choice compared to nominally typed languages like Java, C#, and Go (partially). The flip side is **excess property checking**: when assigning a *fresh* object literal directly to a typed variable, TypeScript additionally rejects properties not present in the target type — a deliberate extra check to catch typos. TypeScript 4.9 added the `satisfies` operator, which checks a value against a type structurally without widening the inferred type of the variable.

## 2. What Constraint It Lets You Express

**Shape conformance is checked at compile time without requiring explicit type declarations, class hierarchies, or `implements` annotations; any value with the right shape satisfies any type that requires that shape.**

- Libraries can accept interfaces they never import; consumer code never needs to import the library's base classes.
- Two completely unrelated classes with the same shape are mutually assignable — this is a feature (open integration) and a hazard (semantic confusion).
- `satisfies` constrains the shape at the point of definition without losing the inferred literal types of the value.

## 3. Minimal Snippet

```typescript
// Two unrelated classes with the same shape are mutually assignable
class Point2D {
  constructor(public x: number, public y: number) {}
}

class Vector2D {
  constructor(public x: number, public y: number) {}
}

function distance(a: Point2D, b: Point2D): number {
  return Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2);
}

const p = new Point2D(0, 0);
const v = new Vector2D(3, 4);

distance(p, p); // OK
distance(p, v); // OK — Vector2D has the same shape as Point2D (may be undesired!)
distance(v, p); // OK — structural, not nominal

// Excess property check: only at fresh object literals
interface Options { timeout: number }

function connect(opts: Options): void { /* ... */ }

connect({ timeout: 5000 });                          // OK
connect({ timeout: 5000, retries: 3 });              // error — 'retries' not in Options (fresh literal)

const cfg = { timeout: 5000, retries: 3 };
connect(cfg);                                        // OK — stale object, no excess check

// satisfies: check shape without losing inferred literal types
const palette = {
  red:   [255, 0, 0],
  green: "#00ff00",
} satisfies Record<string, string | number[]>;       // OK — shape checked

palette.red;    // inferred as number[] (not string | number[])
palette.green;  // inferred as string (not string | number[])
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Interfaces & Structural Contracts** [-> T05](T05-type-classes.md) | Interfaces name structural shapes; structural typing is what makes a value satisfy an interface without `implements`. The two features are inseparable. |
| **Union & Intersection Types** [-> T02](T02-union-intersection.md) | Intersection types extend the structural model: `A & B` is structurally the shape that has all properties of `A` and all properties of `B`. |
| **Record Types** [-> T31](T31-record-types.md) | Record and mapped types produce structural shapes; structurally typed values satisfy mapped-type constraints without explicit annotations. |
| **Type Narrowing** [-> T14](T14-type-narrowing.md) | Narrowing uses structural checks (`in` operator, discriminant fields) to progressively restrict the structural type within a branch. |

## 5. Gotchas and Limitations

1. **Semantic confusion between structurally identical types** — `Point2D` and `Vector2D` are assignable to each other, which may be a bug. Branded types (T03) or nominal wrappers are the remedy when structural identity is insufficient.
2. **Excess property checks only at fresh literals** — assigning a variable bypasses excess property checks, so stale objects can silently carry extra properties into typed contexts. Use `satisfies` to check at the definition site.
3. **Function parameter bivariance (pre-`--strictFunctionTypes`)** — without `--strict`, method parameters in interfaces are checked bivariantly, allowing unsound assignments. `--strictFunctionTypes` fixes this for function types but not method signatures.
4. **Private class members break structural equivalence** — two classes with private fields of the same name are *not* mutually assignable even if everything else matches; private fields are nominally tracked.
5. **`satisfies` does not narrow the variable type** — `satisfies` checks the type but the variable's type is still the inferred literal type of the expression, not the `satisfies` type. This is the intended behavior but surprises users who expect it to behave like a type annotation.
6. **Index signatures widen structural types** — a type with `[key: string]: unknown` is structurally compatible with almost everything, which can mask missing property errors.

## Coming from JavaScript

JavaScript is already structurally typed at runtime — objects are bags of properties, and any object with the right methods works as a substitute. TypeScript's structural type system makes this implicit runtime contract explicit and verified statically, while adding the safety of excess property checks at fresh literal sites.

## 6. Use-Case Cross-References

- [-> UC-05](../usecases/UC05-structural-contracts.md) Structural contract enforcement across module and library boundaries
- [-> UC-04](../usecases/UC04-generic-constraints.md) Generic bounds as structural requirements on type parameters
- [-> UC-14](../usecases/UC14-extensibility.md) Open extensibility without requiring shared base classes or explicit registration
