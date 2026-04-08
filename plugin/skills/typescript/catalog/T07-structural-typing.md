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
| **Generics & Bounds** [-> T04](T04-generics-bounds.md) | Generic type parameters are constrained with `extends`, which is a structural check: `T extends Closeable` accepts any `T` with a compatible shape. |
| **Branded / Opaque Types** [-> T03](T03-newtypes-opaque.md) | Brands escape structural typing by adding a phantom property that acts like a nominal tag, preventing unintended cross-assignment of identically shaped types. |

## 5. Gotchas and Limitations

1. **Semantic confusion between structurally identical types** — `Point2D` and `Vector2D` are assignable to each other, which may be a bug. Branded types (T03) or nominal wrappers are the remedy when structural identity is insufficient.
2. **Excess property checks only at fresh literals** — assigning a variable bypasses excess property checks, so stale objects can silently carry extra properties into typed contexts. Use `satisfies` to check at the definition site.
3. **Function parameter bivariance (pre-`--strictFunctionTypes`)** — without `--strict`, method parameters in interfaces are checked bivariantly, allowing unsound assignments. `--strictFunctionTypes` fixes this for function types but not method signatures.
4. **Private class members break structural equivalence** — two classes with private fields of the same name are *not* mutually assignable even if everything else matches; private fields are nominally tracked.
5. **`satisfies` does not narrow the variable type** — `satisfies` checks the type but the variable's type is still the inferred literal type of the expression, not the `satisfies` type. This is the intended behavior but surprises users who expect it to behave like a type annotation.
6. **Index signatures widen structural types** — a type with `[key: string]: unknown` is structurally compatible with almost everything, which can mask missing property errors.
7. **Optional properties are not required** — a type with `x?: number` is satisfied by a value with no `x` at all, or with `x: number`. The check is one-sided: the target may have it, or not.
8. **Structural typing has no runtime presence** — TypeScript types are erased. An `instanceof` check against an interface name does not exist. Use user-defined type guards or discriminant properties for runtime narrowing.

## 6. Function Structural Typing

Function types are also compared structurally. The rules are:

- **Return types are covariant**: a function returning `string` satisfies a slot expecting `string | null` (narrower return is fine).
- **Parameter types are contravariant** (under `--strictFunctionTypes`): a function accepting `Animal` satisfies a slot expecting `(x: Cat) => void` only if `Cat extends Animal`, not the other way.
- **Fewer parameters are always assignable**: TypeScript follows JavaScript convention — a callback that ignores arguments is always compatible with a caller that provides them. This is the "you may ignore arguments" rule.

```typescript
type Handler = (event: MouseEvent, index: number) => void;

// Fewer parameters: OK — ignoring extra args is safe
const h1: Handler = (event) => console.log(event.type);
const h2: Handler = () => {};              // zero params also OK

// Return type covariance
type GetString = () => string;
const gs: GetString = () => "hello";      // OK

type GetStringOrNull = () => string | null;
// const bad: GetStringOrNull = gs;       // OK — string is assignable to string | null
const wider: GetStringOrNull = gs;        // OK (covariant return)

// Parameter contravariance (--strictFunctionTypes)
interface Animal { name: string }
interface Cat extends Animal { meow(): void }

type HandleAnimal = (a: Animal) => void;
type HandleCat    = (c: Cat) => void;

declare let handleAnimal: HandleAnimal;
declare let handleCat: HandleCat;

handleCat = handleAnimal;  // OK — Animal handler can safely handle a Cat (contravariant params)
// handleAnimal = handleCat;  // error — Cat handler cannot handle any Animal
```

## 7. Generic Structural Typing

Generic interfaces define structural contracts parameterised over a type. Any class or object literal that provides the required members with matching type parameters satisfies the interface — no `implements` needed.

```typescript
interface Container<T> {
  get(): T;
  set(value: T): void;
}

// Satisfies Container<number> structurally — no implements declaration
class Box<T> {
  constructor(private value: T) {}
  get(): T { return this.value; }
  set(value: T): void { this.value = value; }
}

function swap<T>(c: Container<T>, next: T): T {
  const old = c.get();
  c.set(next);
  return old;
}

const box = new Box(10);
swap(box, 20);   // OK — Box<number> satisfies Container<number>

// Bounded type parameter: T extends the structural shape
interface Closeable {
  close(): void;
}

function withResource<T extends Closeable>(resource: T, fn: (r: T) => void): void {
  try {
    fn(resource);
  } finally {
    resource.close();
  }
}

// Any object with close() satisfies the bound
const conn = { close: () => console.log("closed"), query: () => [] };
withResource(conn, (c) => c.query());   // OK — conn has close()
```

## 8. Callable Structural Typing

Interfaces can declare a **call signature**, making any function with a compatible signature satisfy the interface. This is TypeScript's analogue of Python's `Protocol.__call__` — it lets an interface carry both callable behavior and additional properties.

```typescript
// Interface with a call signature and a property
interface Formatter {
  (value: number): string;   // callable
  locale: string;            // additional property
}

function applyFormatter(values: number[], fmt: Formatter): string[] {
  return values.map(fmt);
}

// Must be a function object with a locale property
const usFmt: Formatter = Object.assign(
  (n: number) => n.toLocaleString("en-US"),
  { locale: "en-US" }
);

applyFormatter([1000, 2000], usFmt);   // OK

// Plain function type (no extra properties) — simpler but no metadata
type SimpleFormatter = (value: number) => string;
```

## 9. Structural Typing vs Runtime: Type Guards

TypeScript types are erased at runtime, so there is no equivalent of Python's `@runtime_checkable` + `isinstance()` for arbitrary interface checks. The idiomatic TypeScript alternatives are:

**User-defined type guards** — write a function that checks the shape at runtime and tells the type checker the result:

```typescript
interface Closeable {
  close(): void;
}

function isCloseable(value: unknown): value is Closeable {
  return (
    typeof value === "object" &&
    value !== null &&
    "close" in value &&
    typeof (value as any).close === "function"
  );
}

function safeClose(resource: unknown): void {
  if (isCloseable(resource)) {
    resource.close();   // narrowed to Closeable here
  }
}
```

**Discriminant properties** — add a `kind` or `type` literal field to distinguish shapes at runtime without full property enumeration:

```typescript
interface Circle   { kind: "circle";   radius: number }
interface Rectangle { kind: "rectangle"; width: number; height: number }
type Shape = Circle | Rectangle;

function area(s: Shape): number {
  switch (s.kind) {          // discriminant narrows structurally
    case "circle":    return Math.PI * s.radius ** 2;
    case "rectangle": return s.width * s.height;
  }
}
```

## 10. Common Type-Checker Errors and How to Read Them

### `Property 'x' is missing in type 'A' but required in type 'B'`

A required property is absent. The shape does not match.

```
error TS2345: Argument of type '{ timeout: number }' is not assignable to
              parameter of type 'Options'.
  Property 'retries' is missing in type '{ timeout: number }' but required
  in type 'Options'.
```

**Fix:** Add the missing property, or make it optional in the target type with `?:`.

---

### `Object literal may only specify known properties, and 'x' does not exist in type 'Y'`

Excess property check on a fresh object literal.

```
error TS2353: Object literal may only specify known properties, and 'retries'
              does not exist in type 'Options'.
```

**Fix:** Remove the extra property, add it to the target interface, or assign to an intermediate variable to bypass the fresh-literal check (intentionally).

---

### `Type '(x: Cat) => void' is not assignable to type '(x: Animal) => void'`

Parameter type contravariance violation — the callback expects a narrower type than the caller provides.

```
error TS2322: Type '(c: Cat) => void' is not assignable to type '(a: Animal) => void'.
  Types of parameters 'c' and 'a' are incompatible.
    Type 'Animal' is not assignable to type 'Cat'.
      Property 'meow' is missing in type 'Animal' but required in type 'Cat'.
```

**Fix:** Widen the parameter type of the callback, or use a union.

---

### `Index signature for type 'string' is missing in type 'X'`

A target type has an index signature but the candidate type does not declare one.

```
error TS2345: Argument of type '{ name: string }' is not assignable to
              parameter of type 'Record<string, unknown>'.
  Index signature for type 'string' is missing in type '{ name: string }'.
```

**Fix:** Add an index signature to the candidate type, or use a type assertion (`as Record<string, unknown>`) where safe.

---

### `Private property 'x' of class 'A' is not assignable to the same property in class 'B'`

Two classes share a private field name, breaking structural equivalence.

```
error TS2345: Argument of type 'B' is not assignable to parameter of type 'A'.
  Types have separate declarations of a private property '_id'.
```

**Fix:** Use `protected` or a public getter, or share a common base class.

## Coming from JavaScript

JavaScript is already structurally typed at runtime — objects are bags of properties, and any object with the right methods works as a substitute. TypeScript's structural type system makes this implicit runtime contract explicit and verified statically, while adding the safety of excess property checks at fresh literal sites.

## Beginner Mental Model

Think of TypeScript's type checker as a **shape stencil**. When you pass a value to a function, the checker holds up the stencil (the parameter type) against the value. If every hole in the stencil is covered by a matching property on the value, the value fits — even if the value has extra material sticking out beyond the stencil's edges (extra properties on a variable reference are allowed). The stencil is about what is *required*, not about what the value was originally called or where it was made.

The exception: when you hand a brand-new piece of material (a fresh object literal) directly to the stencil, the checker also checks for *extra* protrusions — the excess property check. This extra step catches typos that would otherwise be silently swallowed.

## 11. Use-Case Cross-References

- [-> UC-05](../usecases/UC05-structural-contracts.md) Structural contract enforcement across module and library boundaries
- [-> UC-04](../usecases/UC04-generic-constraints.md) Generic bounds as structural requirements on type parameters
- [-> UC-14](../usecases/UC14-extensibility.md) Open extensibility without requiring shared base classes or explicit registration

## Source Anchors

- [TypeScript Handbook — Type Compatibility](https://www.typescriptlang.org/docs/handbook/type-compatibility.html)
- [TypeScript Handbook — Interfaces](https://www.typescriptlang.org/docs/handbook/2/objects.html)
- [TypeScript 4.9 release notes — `satisfies` operator](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-9.html#the-satisfies-operator)
- [TypeScript deep dive — Freshness / Excess Property Checking](https://basarat.gitbook.io/typescript/type-system/freshness)
- [TypeScript FAQ — Why are function parameters bivariant?](https://github.com/Microsoft/TypeScript/wiki/FAQ#why-are-function-parameters-bivariant)
