# Encapsulation & Module Boundaries

> **Since:** TypeScript 1.0 (access modifiers); `#private` fields since TypeScript 3.8

## 1. What It Is

TypeScript offers several layers of encapsulation. **Access modifiers** — `public`, `protected`, and `private` — are purely type-level: they constrain what the compiler will allow, but have no runtime enforcement (all properties are accessible via JavaScript at runtime). **ES private fields** (`#field` syntax) are part of the JavaScript language itself and are enforced at runtime; even reflection and `Object.keys` cannot see them in conformant engines. TypeScript has no `internal` keyword; the closest equivalent is **module-level encapsulation** — a type or value that is not exported from a module simply does not exist outside it, regardless of access modifiers. `readonly` on class properties and utility types prevents reassignment after construction.

## 2. What Constraint It Lets You Express

**Control what crosses type boundaries and, with `#private`, what is accessible at runtime; hide implementation details behind interfaces and module exports.**

- `private` and `protected` create type-level barriers: the compiler rejects access from outside the class or subclass hierarchy.
- `#field` creates a runtime barrier: the field is not on the prototype chain and is inaccessible from outside the class, even by casting to `any` and accessing the property name as a string.
- Not exporting a type or value from a module is the strongest encapsulation: it simply does not exist in the consumer's namespace.
- Exposing only an `interface` (not the implementing `class`) from a module hides the constructor, the implementation details, and any internal methods.

## 3. Minimal Snippet

```typescript
// --- TypeScript private vs ES private ---
class Counter {
  private tsCount = 0;    // type-level only
  #jsCount = 0;           // runtime-enforced

  increment() {
    this.tsCount++;
    this.#jsCount++;
  }

  get value() { return this.#jsCount; }
}

const c = new Counter();
c.increment();
// c.tsCount   // error — TypeScript rejects access
// (c as any).tsCount  // OK at runtime — TypeScript private is not enforced at runtime
// c.#jsCount  // error — syntax error; ES private cannot be accessed outside class

// --- Interface as public surface, class hidden inside module ---
// (file: userStore.ts — only the interface is exported)
export interface UserStore {
  get(id: string): User | undefined;
  save(user: User): void;
}

class InMemoryUserStore implements UserStore {
  readonly #store = new Map<string, User>();

  get(id: string) { return this.#store.get(id); }
  save(user: User) { this.#store.set(user.id, user); }
}

export function createUserStore(): UserStore {
  return new InMemoryUserStore(); // OK — class is an implementation detail
}

// Consumer cannot access InMemoryUserStore or its internals
// import { InMemoryUserStore } from "./userStore"; // error — not exported

// --- readonly prevents post-construction mutation ---
class Config {
  readonly host: string;
  readonly port: number;

  constructor(host: string, port: number) {
    this.host = host;
    this.port = port;
  }
}

const cfg = new Config("localhost", 8080);
// cfg.host = "other"; // error — readonly property
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Immutability Markers** [-> T32](T32-immutability-markers.md) | `readonly` on class properties is both an encapsulation tool (preventing external mutation) and an immutability marker; `Readonly<T>` extends this to utility types. |
| **Record Types & Interfaces** [-> T31](T31-record-types.md) | Exposing only an `interface` (not the `class`) from a module is the idiomatic TypeScript way to hide implementation details while preserving a structural contract. |
| **Structural Typing** [-> T07](T07-structural-typing.md) | TypeScript's structural type system means that `private` is checked structurally (two classes with identically-shaped `private` fields are not compatible); this is sometimes surprising when comparing class instances. |
| **Type Narrowing** [-> T14](T14-type-narrowing.md) | `protected` and `private` interact with narrowing: a `private` method can use `this is SubType` predicates to narrow within the class hierarchy. |
| **Newtypes / Opaque Types** [-> T03](T03-newtypes-opaque.md) | A class with a `private` constructor and `#brand` field is the idiomatic TypeScript opaque type — private fields make the wrapper truly unpierceable without the module's cooperation. |

## 5. Gotchas and Limitations

1. **`private` is erased at runtime** — casting to `any` bypasses TypeScript's `private` check entirely; `private` provides no security guarantee, only a development-time contract.
2. **`#private` changes the property name at the source level** — you cannot access `#field` via a computed string key (`obj["#field"]` does not work); this is both the source of its runtime enforcement and a potential surprise when serializing.
3. **No `internal` keyword** — TypeScript has no equivalent to Rust's `pub(crate)`. The closest patterns are: (a) a barrel `index.ts` that selectively re-exports only the public surface; (b) the `@internal` JSDoc tag, which tools like TypeDoc and some bundlers respect; (c) `package.json` `exports` field, which prevents deep imports entirely at the Node/bundler level.
4. **Structural compatibility of `private`** — two classes with a `private field: T` are not mutually assignable even if every other property matches; this differs from `#private`, where compatibility is based on the structural shape as seen from outside the class.
5. **`readonly` is shallow** — `readonly items: string[]` prevents reassigning the array reference but not mutating the array contents; use `readonly string[]` or `ReadonlyArray<string>` for a deeper constraint.
6. **Declaration merging bypasses interface hiding** — if a consumer imports and extends an interface, they can add methods; this is not a runtime bypass, but it weakens the abstraction boundary in the type system.
7. **`protected` is not a module boundary** — `protected` allows access within subclasses regardless of which module they live in. It expresses inheritance intent, not deployment boundary. Two unrelated subclasses in different packages can both reach `protected` members.
8. **Getters without setters are not deeply immutable** — a `get items()` that returns a mutable array still exposes the underlying reference; callers can mutate the contents. Return `ReadonlyArray` or a defensive copy for true read-only semantics.

## 6. Example A — Private constructor with static factory

A `private` constructor funnels all construction through a validated factory, analogous to Rust's private struct fields:

```typescript
// temperature.ts
export class Celsius {
  // #value is runtime-private; cannot be forged from outside
  readonly #value: number;

  private constructor(value: number) {
    this.#value = value;
  }

  static create(value: number): Celsius {
    if (value < -273.15) {
      throw new RangeError(`${value}°C is below absolute zero`);
    }
    return new Celsius(value);
  }

  get value(): number { return this.#value; }

  toFahrenheit(): number { return this.#value * 9 / 5 + 32; }
}

// Consumer
const t = Celsius.create(100);
console.log(t.toFahrenheit()); // 212

// new Celsius(100);  // error TS2673: constructor is private
// Celsius.create(-300);  // throws RangeError at runtime
```

The combination of `private constructor` + `#value` field provides two complementary barriers: the type checker refuses `new Celsius(...)` anywhere outside the class, and the runtime refuses external reads of `#value` even via `(t as any)["#value"]`.

## 7. Example B — Getter/setter for validated property access

TypeScript `get`/`set` accessors provide the same validation hooks as Python's `@property`:

```typescript
class Temperature {
  #celsius: number;

  constructor(celsius: number) {
    // route through setter so validation runs at construction too
    this.celsius = celsius;
  }

  get celsius(): number { return this.#celsius; }

  set celsius(value: number) {
    if (value < -273.15) {
      throw new RangeError(`${value}°C is below absolute zero`);
    }
    this.#celsius = value;
  }

  /** Read-only derived property — no setter */
  get fahrenheit(): number { return this.#celsius * 9 / 5 + 32; }
}

const t = new Temperature(100);
console.log(t.fahrenheit);  // 212
t.celsius = -300;            // RangeError at runtime
// t.fahrenheit = 0;         // error TS2540: cannot assign to read-only property
```

## 8. Example C — Module-level encapsulation with selective re-exports

The TypeScript equivalent of Python's `__all__` is a barrel file that exports only the intended public surface. `package.json` `exports` enforces this at the bundler/Node level:

```typescript
// src/geometry/circle.ts  (implementation — not exported from barrel)
export class Circle {
  readonly #radius: number;

  constructor(radius: number) {
    if (radius <= 0) throw new RangeError("radius must be positive");
    this.#radius = radius;
  }

  get radius(): number { return this.#radius; }
  area(): number { return Math.PI * this.#radius ** 2; }
}

// src/geometry/_helpers.ts  (internal — underscore convention + not re-exported)
export function approxEqual(a: number, b: number, eps = 1e-9): boolean {
  return Math.abs(a - b) < eps;
}

// src/geometry/index.ts  (barrel — explicit public surface)
export type { Circle } from "./circle";
export { Circle } from "./circle";
// _helpers is deliberately not re-exported

// package.json
// {
//   "exports": {
//     ".": "./dist/geometry/index.js"   // deep import of ./dist/geometry/circle.js blocked
//   }
// }
```

For stronger enforcement, a `@internal` JSDoc comment communicates intent to documentation generators and some language-server tooling:

```typescript
/** @internal Not part of the public API; may change without notice. */
export function approxEqual(a: number, b: number): boolean { /* … */ }
```

## 9. Use-Case Cross-References

- [-> UC-10](../usecases/UC10-encapsulation.md) Hide implementation details behind module boundaries and expose only the minimal interface needed by consumers
- [-> UC-01](../usecases/UC01-invalid-states.md) Private constructors + static factories make invalid states unrepresentable by forcing all construction through validated paths
- [-> UC-02](../usecases/UC02-domain-modeling.md) Domain types use `#private` fields and interface-only exports to expose a minimal, stable contract

## Source Anchors

- TypeScript Handbook — [Classes: Member Visibility](https://www.typescriptlang.org/docs/handbook/2/classes.html#member-visibility)
- TypeScript Handbook — [Classes: Private Fields](https://www.typescriptlang.org/docs/handbook/2/classes.html#caveats)
- TC39 — [Private class fields (stage 4)](https://github.com/tc39/proposal-class-fields)
- Node.js docs — [package.json `exports` field](https://nodejs.org/api/packages.html#exports)
- TypeDoc — [`@internal` tag](https://typedoc.org/tags/internal/)
