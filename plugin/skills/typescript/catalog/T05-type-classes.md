# Interfaces & Structural Contracts

> **Since:** TypeScript 1.0

## 1. What It Is

TypeScript uses `interface` declarations (and equivalent `type` aliases for object shapes) to define **structural contracts**: a named specification of the properties, methods, and index signatures a value must have. Unlike Haskell or Scala type classes, TypeScript has no typeclass dispatch mechanism — there is no automatic instance search, no implicit parameters, and no dictionary passing. Instead, conformance is checked **structurally**: any value that has the required shape satisfies the interface, regardless of whether it was declared with `implements` or even whether its author knew about the interface. The optional `class Foo implements Bar` annotation adds a compile-time check that `Foo` satisfies `Bar`, but it is not required for assignability.

## 2. What Constraint It Lets You Express

**Any value with the right shape satisfies the contract, regardless of its nominal type; the compiler rejects values that are missing required properties or have incompatible property types.**

- A plain object literal satisfies an interface if it has the required shape; no class, `implements`, or factory is needed.
- Optional properties (`x?: T`) and readonly properties (`readonly x: T`) are part of the contract and are enforced at every assignment and call site.
- Interfaces can extend multiple other interfaces, and a single type can satisfy multiple unrelated interfaces simultaneously.

## 3. Minimal Snippet

```typescript
interface Printable {
  print(): void;
}

interface Serializable {
  serialize(): string;
}

// Any object with these shapes satisfies both interfaces — no declaration needed
const doc = {
  content: "hello",
  print()      { console.log(this.content); },
  serialize()  { return JSON.stringify(this.content); },
};

function printAndSave(item: Printable & Serializable): void {
  item.print();
  const data = item.serialize();
  console.log("Saved:", data);
}

printAndSave(doc); // OK — structural match

// Class with explicit implements — adds compile-time guarantee on the class itself
class Report implements Printable, Serializable {
  constructor(private title: string) {}
  print()     { console.log(`Report: ${this.title}`); }
  serialize() { return JSON.stringify({ title: this.title }); }
}

printAndSave(new Report("Q1")); // OK

// Objects that lack required members are rejected
const incomplete = { print: () => {} };
// printAndSave(incomplete); // error — Property 'serialize' is missing

// Interface with optional and readonly members
interface Config {
  readonly host: string;
  port?: number;
}

const cfg: Config = { host: "localhost" };     // OK — port is optional
// cfg.host = "other";                         // error — readonly
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Structural Typing** [-> T07](T07-structural-typing.md) | Interfaces are the primary way to name a structural shape; structural typing is what makes a value satisfy an interface without `implements`. |
| **Union & Intersection Types** [-> T02](T02-union-intersection.md) | Intersecting interfaces (`A & B`) is the idiomatic way to compose multiple contracts; `interface C extends A, B` is nearly equivalent for object types. |
| **Callable Typing** [-> T22](T22-callable-typing.md) | Interfaces can carry call signatures (`(arg: T): R`) and construct signatures (`new (arg: T): R`), making them the type of functions and constructors as well as objects. |
| **Type Narrowing** [-> T14](T14-type-narrowing.md) | Narrowing against interface-shaped discriminated unions and `in` operator checks allows the compiler to confirm a value implements a specific interface subset at runtime. |

## 5. Gotchas and Limitations

1. **No implicit dispatch** — TypeScript interfaces are not type classes. There is no automatic selection of an implementation based on the type argument; you must pass the implementation explicitly (often as a parameter or via module-level singletons).
2. **Interface vs type alias** — `interface` supports declaration merging (multiple declarations with the same name are merged); `type` aliases do not. For library authors, `interface` is preferable for extensibility; for internal code the difference is minor.
3. **Excess property checks only at fresh literals** — assigning a variable (not a literal) to an interface-typed slot skips excess property checks. `const x: Printable = { print() {}, extra: 1 }` is an error at the literal, but `const obj = { print() {}, extra: 1 }; const x: Printable = obj;` is not.
4. **`implements` does not change assignability** — removing `implements Printable` from a class that has the right shape does not affect whether its instances are assignable to `Printable`. The annotation is for the developer's benefit, not the type system's.
5. **Method vs function-property variance** — a method declared as `method(): void` in an interface is checked bivariantly (unsound under `--strictFunctionTypes`); a function-property `method: () => void` is checked contravariantly in parameter position. Prefer function-property syntax in strict codebases.
6. **Index signatures conflict with specific properties** — an interface with `[key: string]: unknown` cannot also have `name: string` unless `string` extends `unknown` (it does), but trying to add `name: number` where the index signature says `string` is an error.

## Coming from JavaScript

JavaScript objects are already structurally typed at runtime — any object with the right methods works. TypeScript interfaces make that implicit contract explicit and checked at compile time, turning runtime duck-typing surprises into compile-time errors.

## 6. Use-Case Cross-References

- [-> UC-04](../usecases/UC04-generic-constraints.md) Interfaces as bounds on generic type parameters
- [-> UC-05](../usecases/UC05-structural-contracts.md) Structural contracts enforced at module boundaries without inheritance
- [-> UC-14](../usecases/UC14-extensibility.md) Open/closed extensibility via interface extension and declaration merging
