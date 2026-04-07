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

## 5. Gotchas and Limitations

1. **`private` is erased at runtime** — casting to `any` bypasses TypeScript's `private` check entirely; `private` provides no security guarantee, only a development-time contract.
2. **`#private` changes the property name at the source level** — you cannot access `#field` via a computed string key (`obj["#field"]` does not work); this is both the source of its runtime enforcement and a potential surprise when serializing.
3. **No `internal` keyword** — TypeScript has no way to mark a type as visible within a package but not externally; the closest pattern is using a barrel file that selectively re-exports, or a separate `internal.ts` module with a convention.
4. **Structural compatibility of `private`** — two classes with a `private field: T` are not mutually assignable even if every other property matches; this differs from `#private`, where compatibility is based on the structural shape as seen from outside the class.
5. **`readonly` is shallow** — `readonly items: string[]` prevents reassigning the array reference but not mutating the array contents; use `readonly string[]` or `ReadonlyArray<string>` for a deeper constraint.
6. **Declaration merging bypasses interface hiding** — if a consumer imports and extends an interface, they can add methods; this is not a runtime bypass, but it weakens the abstraction boundary in the type system.

## 6. Use-Case Cross-References

- [-> UC-10](../usecases/UC10-encapsulation.md) Hide implementation details behind module boundaries and expose only the minimal interface needed by consumers
