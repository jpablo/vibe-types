# Type Classes — Not Supported in TypeScript

> **Status:** × Not expressible in TypeScript

## Not a TypeScript Feature

TypeScript does not have type classes. The T05 slot in the shared taxonomy requires *capability evidence with automatic instance dispatch*: a mechanism where the compiler searches for and supplies an implementation (instance, dictionary, given) based solely on the type. TypeScript has no such mechanism — there are no implicit parameters, no instance search, and no dictionary passing.

What TypeScript **does** have is **structural interfaces**: named shapes that any value can satisfy without explicit registration, and which must be passed explicitly as function parameters. This is documented under [-> T07 Structural Typing](T07-structural-typing.md).

For cross-language context: Haskell type classes, Scala 3 `given`/`using`, Rust traits with blanket impls, and Lean type classes all provide automatic dispatch. TypeScript interfaces do not.

---

*The remainder of this document covers the closest TypeScript approximations, in order of how closely they match the type-class pattern.*

---

## Approximation 1: Structural Interfaces

TypeScript uses `interface` declarations (and equivalent `type` aliases for object shapes) to define **structural contracts**: a named specification of the properties, methods, and index signatures a value must have. Unlike Haskell or Scala type classes, TypeScript has no typeclass dispatch mechanism — there is no automatic instance search, no implicit parameters, and no dictionary passing. Instead, conformance is checked **structurally**: any value that has the required shape satisfies the interface, regardless of whether it was declared with `implements` or even whether its author knew about the interface. The optional `class Foo implements Bar` annotation adds a compile-time check that `Foo` satisfies `Bar`, but it is not required for assignability.

### What Constraint It Lets You Express

**Any value with the right shape satisfies the contract, regardless of its nominal type; the compiler rejects values that are missing required properties or have incompatible property types.**

- A plain object literal satisfies an interface if it has the required shape; no class, `implements`, or factory is needed.
- Optional properties (`x?: T`) and readonly properties (`readonly x: T`) are part of the contract and are enforced at every assignment and call site.
- Interfaces can extend multiple other interfaces, and a single type can satisfy multiple unrelated interfaces simultaneously.

### Minimal Snippet

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

---

## Approximation 2: Abstract Classes (Nominal Enforcement)

Abstract classes are TypeScript's closest analog to Python's ABCs and Rust/Java interfaces with required implementations. Unlike structural interfaces, `abstract class` enforces:

1. The class cannot be instantiated directly — `new Shape()` is a compile error.
2. All abstract members must be implemented by concrete subclasses before they can be instantiated.
3. The class can carry shared concrete method implementations (unlike a pure interface).

This is a **nominal** mechanism: a subclass must explicitly `extends` the abstract class. An object with the right shape but no inheritance chain does not satisfy an `abstract class` type.

```typescript
abstract class Shape {
  abstract area(): number;
  abstract perimeter(): number;

  // Concrete method shared by all subclasses
  describe(): string {
    return `area=${this.area().toFixed(2)}, perimeter=${this.perimeter().toFixed(2)}`;
  }
}

class Circle extends Shape {
  constructor(private radius: number) { super(); }

  area(): number      { return Math.PI * this.radius ** 2; }
  perimeter(): number { return 2 * Math.PI * this.radius; }
}

// new Shape();  // error: Cannot create an instance of an abstract class.

const c = new Circle(5);
c.describe();  // "area=78.54, perimeter=31.42"

// Missing implementation
class BadShape extends Shape {
  area(): number { return 0; }
  // perimeter() is not implemented
}
// new BadShape();  // error: Non-abstract class 'BadShape' does not implement
//                  //        inherited abstract member 'perimeter'.
```

Abstract classes also support abstract properties and accessors:

```typescript
abstract class BaseService {
  abstract readonly serviceName: string;
  abstract readonly timeoutMs: number;

  describe(): string {
    return `${this.serviceName} (timeout=${this.timeoutMs}ms)`;
  }
}

class AuthService extends BaseService {
  readonly serviceName = "auth";
  readonly timeoutMs   = 5000;
}

new AuthService().describe();  // "auth (timeout=5000ms)"
```

**When to prefer abstract class over interface:** use `abstract class` when you need shared implementation, want to prevent direct instantiation, or need nominal checking (ensuring `instanceof` works). Use `interface` when you want structural matching and don't need a shared base implementation.

---

## Approximation 3: Explicit Dictionary Pattern (Type Class Simulation)

The closest simulation of actual type class dispatch in TypeScript is the **explicit dictionary** (or "witness") pattern: define an interface parameterized by the type, create one object per concrete type that satisfies it, and pass it explicitly to generic functions. This is exactly how [`fp-ts`](https://gcanti.github.io/fp-ts/) and [`effect`](https://effect.website/) work.

```typescript
// "Type class" declaration — the interface parameterized by the type
interface Eq<A> {
  readonly equals: (a: A, b: A) => boolean;
}

// "Instances" — one dictionary object per concrete type
const numberEq: Eq<number> = {
  equals: (a, b) => a === b,
};

const stringEq: Eq<string> = {
  equals: (a, b) => a.toLowerCase() === b.toLowerCase(),
};

// Generic function that requires the "instance" explicitly
function distinct<A>(items: A[], eq: Eq<A>): A[] {
  return items.filter(
    (item, i) => items.findIndex(other => eq.equals(item, other)) === i
  );
}

distinct([1, 2, 1, 3], numberEq);          // [1, 2, 3]
distinct(["a", "A", "b"], stringEq);       // ["a", "b"]
```

### Interface Hierarchy (Supertrait Analog)

Just as Rust traits can require supertraits and Lean classes can `extends`, you can chain interface constraints:

```typescript
interface Semigroup<A> {
  readonly concat: (a: A, b: A) => A;
}

interface Monoid<A> extends Semigroup<A> {
  readonly empty: A;
}

// Concrete instance satisfying both interfaces
const stringMonoid: Monoid<string> = {
  empty:  "",
  concat: (a, b) => a + b,
};

const sumMonoid: Monoid<number> = {
  empty:  0,
  concat: (a, b) => a + b,
};

function fold<A>(monoid: Monoid<A>, items: A[]): A {
  return items.reduce(monoid.concat, monoid.empty);
}

fold(stringMonoid, ["hello", " ", "world"]);  // "hello world"
fold(sumMonoid, [1, 2, 3, 4]);                // 10
```

### Conditional Instances (Higher-Kinded Simulation)

TypeScript cannot express `given listOrd: [T: Ord] => Ord[List[T]]` natively, but you can write factory functions:

```typescript
interface Ord<A> extends Eq<A> {
  readonly compare: (a: A, b: A) => -1 | 0 | 1;
}

const numberOrd: Ord<number> = {
  equals:  (a, b) => a === b,
  compare: (a, b) => a < b ? -1 : a > b ? 1 : 0,
};

// "Conditional instance" as a function — like Lean's conditional given
function arrayOrd<A>(ordA: Ord<A>): Ord<A[]> {
  return {
    equals:  (xs, ys) => xs.length === ys.length && xs.every((x, i) => ordA.equals(x, ys[i])),
    compare: (xs, ys) => {
      for (let i = 0; i < Math.min(xs.length, ys.length); i++) {
        const c = ordA.compare(xs[i], ys[i]);
        if (c !== 0) return c;
      }
      return numberOrd.compare(xs.length, ys.length);
    },
  };
}

const ordNumArrays = arrayOrd(numberOrd);
ordNumArrays.compare([1, 2], [1, 3]);  // -1
```

---

## Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Structural Typing** [-> T07](T07-structural-typing.md) | Interfaces are the primary way to name a structural shape; structural typing is what makes a value satisfy an interface without `implements`. |
| **Union & Intersection Types** [-> T02](T02-union-intersection.md) | Intersecting interfaces (`A & B`) is the idiomatic way to compose multiple contracts; `interface C extends A, B` is nearly equivalent for object types. |
| **Generics & Bounds** [-> T04](T04-generics-bounds.md) | Interfaces are the constraint language for generic type parameters. `function f<T extends Printable>(x: T)` restricts `T` to values satisfying the interface. |
| **Callable Typing** [-> T22](T22-callable-typing.md) | Interfaces can carry call signatures (`(arg: T): R`) and construct signatures (`new (arg: T): R`), making them the type of functions and constructors as well as objects. |
| **Type Narrowing** [-> T14](T14-type-narrowing.md) | Narrowing against interface-shaped discriminated unions and `in` operator checks allows the compiler to confirm a value implements a specific interface subset at runtime. |

---

## Beginner Mental Model

Think of a TypeScript interface as a **job description posted on a bulletin board**: it lists the abilities a candidate must have. Unlike Rust or Haskell, nobody has to sign up or register — *any* object that happens to have all the listed abilities qualifies automatically (structural typing). A class with `implements Printable` is just the developer explicitly pinning the job description to the class to catch mismatches early.

Abstract classes are more like a **staffing agency with a mandatory training program**: to work through the agency, you must attend (extend) and complete all the required modules (abstract methods). You cannot send the agency itself to do the work; only graduates can be placed.

The explicit dictionary pattern is the **closest to Haskell/Rust type classes**, but with one big difference: the compiler never finds the dictionary for you. You always carry the dictionary yourself and pass it to any function that needs it. The burden of dispatch falls on the caller, not the compiler.

---

## Named Examples

### Example A — Interface hierarchy as supertrait chain

```typescript
interface Printable {
  print(): void;
}

// Requires satisfying Printable first — analog of Rust's supertrait
interface PrettyPrintable extends Printable {
  prettyPrint(indent: number): void;
}

function display(item: PrettyPrintable): void {
  item.prettyPrint(2);
}

class JsonDoc implements PrettyPrintable {
  constructor(private data: unknown) {}
  print()                    { console.log(JSON.stringify(this.data)); }
  prettyPrint(indent: number){ console.log(JSON.stringify(this.data, null, indent)); }
}

display(new JsonDoc({ x: 1 }));  // OK
```

### Example B — Generic repository with abstract class (Python ABC analog)

```typescript
abstract class Repository<T, ID> {
  abstract get(id: ID): T | undefined;
  abstract listAll(): T[];
  abstract save(entity: T): void;
  abstract delete(id: ID): boolean;

  // Concrete method shared by all implementations
  exists(id: ID): boolean {
    return this.get(id) !== undefined;
  }
}

class InMemoryUserRepo extends Repository<{ id: string; name: string }, string> {
  private store = new Map<string, { id: string; name: string }>();

  get(id: string)                               { return this.store.get(id); }
  listAll()                                     { return [...this.store.values()]; }
  save(entity: { id: string; name: string })    { this.store.set(entity.id, entity); }
  delete(id: string)                            { return this.store.delete(id); }
}

const repo = new InMemoryUserRepo();
repo.save({ id: "1", name: "Alice" });
repo.exists("1");   // true — uses inherited concrete method
```

### Example C — Fully qualified disambiguation when interfaces collide

Unlike Rust's explicit `<Type as Trait>::method` syntax, TypeScript resolves method collisions via the `implements` declaration order and `as` casts:

```typescript
interface UsLocale {
  format(n: number): string;
}

interface EuLocale {
  format(n: number): string;
}

// TypeScript cannot distinguish which `format` was called — both share the same slot
class Price implements UsLocale, EuLocale {
  // A single method satisfies both; there is no per-interface disambiguation.
  format(n: number): string {
    return n.toFixed(2);
  }
}

// If you need separate implementations, use composition instead:
class LocalizedPrice {
  readonly us: UsLocale = { format: n => `$${n.toFixed(2)}` };
  readonly eu: EuLocale = { format: n => `€${n.toFixed(2).replace(".", ",")}` };
}

const p = new LocalizedPrice();
p.us.format(9.9);  // "$9.90"
p.eu.format(9.9);  // "€9,90"
```

**TypeScript has no fully-qualified-call syntax.** When two interfaces have identical method signatures, a class can only provide one implementation. If you need different behavior per interface, use composition (delegation to separate objects) rather than a single class implementing both.

---

## Gotchas and Limitations

1. **No implicit dispatch** — TypeScript interfaces are not type classes. There is no automatic selection of an implementation based on the type argument; you must pass the implementation explicitly (often as a parameter or via module-level singletons).
2. **Interface vs type alias** — `interface` supports declaration merging (multiple declarations with the same name are merged); `type` aliases do not. For library authors, `interface` is preferable for extensibility; for internal code the difference is minor.
3. **Excess property checks only at fresh literals** — assigning a variable (not a literal) to an interface-typed slot skips excess property checks. `const x: Printable = { print() {}, extra: 1 }` is an error at the literal, but `const obj = { print() {}, extra: 1 }; const x: Printable = obj;` is not.
4. **`implements` does not change assignability** — removing `implements Printable` from a class that has the right shape does not affect whether its instances are assignable to `Printable`. The annotation is for the developer's benefit, not the type system's.
5. **Method vs function-property variance** — a method declared as `method(): void` in an interface is checked bivariantly (unsound under `--strictFunctionTypes`); a function-property `method: () => void` is checked contravariantly in parameter position. Prefer function-property syntax in strict codebases.
6. **Index signatures conflict with specific properties** — an interface with `[key: string]: unknown` cannot also have `name: string` unless `string` extends `unknown` (it does), but trying to add `name: number` where the index signature says `string` is an error.
7. **No method disambiguation across interfaces** — unlike Rust's `<Type as Trait>::method`, TypeScript cannot route a call to a specific interface's implementation when two interfaces share a method name. Use composition instead of double inheritance.
8. **Abstract class ≠ interface for structural matching** — an object literal `{ area() { return 0; } }` cannot be assigned to `Shape` if `Shape` is an `abstract class`, even if it has the right shape. Abstract classes are checked nominally; interfaces are checked structurally.

---

## Common Type-Checker Errors

### `Property 'X' is missing in type '...' but required in type 'Y'`

A value is used where an interface is expected but is missing a required property.

```
error TS2345: Argument of type '{ print: () => void; }' is not assignable
              to parameter of type 'Printable & Serializable'.
  Property 'serialize' is missing in type '{ print: () => void; }'.
```

**Fix:** Add the missing property/method, or widen the parameter type to not require it.

### `Cannot create an instance of an abstract class`

```
error TS2511: Cannot create an instance of an abstract class.
```

**Fix:** Instantiate a concrete subclass that extends the abstract class and implements all abstract members, not the abstract class itself.

### `Non-abstract class 'X' does not implement inherited abstract member 'Y'`

A concrete class extends an abstract class but leaves an abstract method unimplemented.

```
error TS2515: Non-abstract class 'BadShape' does not implement
              inherited abstract member 'perimeter' from class 'Shape'.
```

**Fix:** Add the missing method to the concrete class. If the class itself should remain abstract, add the `abstract` keyword to its declaration.

### `Type 'X' does not satisfy the constraint 'Y'`

A generic type argument does not satisfy the interface bound.

```typescript
function print<T extends Printable>(item: T): void { item.print(); }

print(42);
// error TS2345: Argument of type 'number' is not assignable to parameter
//               of type 'Printable'.
```

**Fix:** Ensure the type argument's shape includes all members required by the constraint interface.

### `Interface 'A' incorrectly extends interface 'B'` / `Types of property 'X' are incompatible`

An extending interface tries to narrow or change a property type in an incompatible way.

```typescript
interface Base    { value: number | string; }
interface Derived extends Base { value: boolean; }  // error: boolean not assignable to number | string
```

**Fix:** The extending interface must keep property types compatible (same or subtypes) with the base.

---

## Coming from Other Languages

**Rust:** TypeScript interfaces ≈ Rust traits, but without the orphan rule and without automatic dispatch. `implements` ≈ `impl Trait for Type` (but optional for assignability). Abstract classes are closer to a Rust trait with provided methods. TypeScript has no equivalent to blanket implementations; the dictionary pattern requires explicit wiring.

**Scala 3 / Lean:** TypeScript's explicit dictionary pattern ≈ Scala's `given`/`using` but with you doing the compiler's job. There is no `summon`, no context bounds, and no coherence checking. The absence of higher-kinded types makes encoding `Functor`, `Monad`, etc. awkward — fp-ts uses a "URI" encoding hack to work around this.

**Python:** Abstract classes (`abstract class`) ≈ Python's `abc.ABC` + `@abstractmethod`. The key difference: TypeScript abstract classes are checked at compile time only; Python enforces them at runtime too. TypeScript has no equivalent to `ABCMeta.register()` (virtual subclasses that bypass structural checking).

## Coming from JavaScript

JavaScript objects are already structurally typed at runtime — any object with the right methods works. TypeScript interfaces make that implicit contract explicit and checked at compile time, turning runtime duck-typing surprises into compile-time errors.

---

## Recommended Libraries

| Library | Description |
|---------|-------------|
| [fp-ts](https://gcanti.github.io/fp-ts/) | Functional programming via explicit type class dictionaries (`Functor`, `Monad`, `Eq`, `Ord`, etc.) — the canonical example of the dictionary pattern at scale |
| [effect](https://effect.website/) | Production-grade effects + services built on the dictionary pattern; brings the `Service`/`Layer` abstraction closest to Scala's `ZIO` |
| [io-ts](https://gcanti.github.io/io-ts/) | Runtime validation codecs as explicit dictionaries — pairs with fp-ts |

---

## Use-Case Cross-References

- [-> UC-04](../usecases/UC04-generic-constraints.md) Interfaces as bounds on generic type parameters
- [-> UC-05](../usecases/UC05-structural-contracts.md) Structural contracts enforced at module boundaries without inheritance
- [-> UC-14](../usecases/UC14-extensibility.md) Open/closed extensibility via interface extension and declaration merging

---

## When to Use Interfaces (Structural Pattern)

Use structural interfaces when you need **compile-time shape checking** without forcing nominal inheritance:

- **Ad-hoc polymorphism**: Any value with the right shape works, no registration needed.
  ```typescript
  interface ToString { toString(): string }
  function log(x: ToString) { console.log(x.toString()) }
  log({ toString: () => "hello" }) // OK — no class needed
  ```
- **Library APIs**: Consumers implement interfaces without importing your base class.
- **Testing**: Mock objects satisfy interfaces by shape, not mock frameworks.
  ```typescript
  interface Repo { get(id: string): User | null }
  const mock: Repo = { get: jest.fn() } // OK — shape match
  ```
- **Merging contracts**: Combine multiple unrelated interfaces via intersection.
  ```typescript
  interface Readable { read(): string }
  interface writable { write(s: string): void }
  function rwStream(s: Readable & writable) { /*...*/ }
  ```

---

## When NOT to Use Interfaces

Avoid interfaces when:

- **You need shared implementation**: Interfaces have no code — use abstract class or mixin.
  ```typescript
  // Bad: interface with no implementation, duplicated code everywhere
  interface Logger { log(msg: string): void; warn(msg: string): void }
  const logger1: Logger = {
    log: m => console.log(m),
    warn: m => console.warn(m)
  }
  const logger2: Logger = {
    log: m => console.log(m),  // duplicated
    warn: m => console.warn(m) // duplicated
  }

  // Better: abstract class with shared implementation
  abstract class BaseLogger {
    log(m: string) { console.log(m) }
    warn(m: string) { console.warn(m) }
  }
  class FileLogger extends BaseLogger {} // inherits both methods
  ```
- **You need runtime type identification**: Interfaces erase at runtime — use `instanceof` with classes.
  ```typescript
  interface Animal { move(): void }
  const dog: Animal = { move: () => {} }
  // typeof dog === "object" — no way to check "is Animal" at runtime
  ```
- **You need type class dispatch**: Interfaces don't auto-dispatch — you must pass them explicitly.
- **You need to enforce nominal boundaries**: Structural matching can be too permissive.

---

## Antipatterns When Using Interfaces

### Antipattern 1: Interface Bloat (God Interface)

Defining interfaces with too many methods forces all implementers to provide them, violating single responsibility.

```typescript
// Bad: God interface — every user must implement ALL methods
interface UserManager {
  createUser(u: User): void
  deleteUser(id: string): void
  updateUser(u: User): void
  listUsers(): User[]
  banUser(id: string): void
  grantRole(id: string, role: string): void
  sendEmail(id: string, msg: string): void
  // ... 20+ more methods
}
```

**Better**: Split into focused interfaces.

```typescript
interface UserRepository {
  createUser(u: User): void
  deleteUser(id: string): void
  updateUser(u: User): void
  listUsers(): User[]
}

interface UserSecurity {
  banUser(id: string): void
  grantRole(id: string, role: string): void
}

interface UserNotifier {
  sendEmail(id: string, msg: string): void
}

// Compose only what you need
function processUser(userDb: UserRepository, notifier: UserNotifier) {
  // ...
}
```

---

### Antipattern 2: Redundant Interface Declaration

Declaring an interface when the shape is used once — adds noise without benefit.

```typescript
// Bad: interface used only once
interface TransformParams {
  x: number
  y: number
}
function transform(p: TransformParams) { /*...*/ }
transform({ x: 1, y: 2 })

// Better: inline the shape
function transform(p: { x: number; y: number }) { /*...*/ }
```

---

### Antipattern 3: Interface for Every Single-Use Object

Creating a named interface for each one-off object literal.

```typescript
// Bad: naming every temporary shape
interface OneOff1 { id: number; name: string }
interface OneOff2 { status: "active" | "inactive"; updatedAt: Date }

function process(data: OneOff1, meta: OneOff2) { /*...*/ }
```

**Better**: Use inline types unless the shape appears in multiple places.

```typescript
function process(data: { id: number; name: string },
                 meta: { status: "active" | "inactive"; updatedAt: Date }) {
  /*...*/
}
```

---

### Antipattern 4: Overusing `any` Inside Interfaces

Putting `any` in interfaces defeats type safety.

```typescript
// Bad: defeats the purpose of interfaces
interface Config {
  name: string
  options: any // dangerous — no checking
}
const cfg: Config = { name: "app", options: "anything goes" }
```

**Better**: Constrain with union types or unknown.

```typescript
interface Config {
  name: string
  options: { theme: "light" | "dark"; debug: boolean }
}
```

---

### Antipattern 5: Circular Interface Dependencies Without Break

```typescript
// Bad: circular references everywhere
interface Node { children: Node[] }
interface Tree { root: Node }
// Both are valid but creates infinite nesting confusion
```

**Better**: Use type aliases for breaking cycles when needed.

```typescript
type Node = { children: Node[] }
interface Tree { root: Node }
```

---

## Antipatterns with Other Techniques (Where Interfaces Improve Code)

### Antipattern A: Using `any` Instead of Interfaces

```typescript
// Bad: no type safety
function handleRequest(req: any) {
  console.log(req.method, req.url) // runtime error if .method missing
}

// Better: interface ensures shape
interface Request {
  method: string
  url: string
  headers: Record<string, string>
}
function handleRequest(req: Request) {
  console.log(req.method, req.url) // compile error if wrong shape
}
```

---

### Antipattern B: Runtime Type Guards Instead of Compile-Time Interfaces

```typescript
// Bad: checking types at runtime
function processData(x: unknown) {
  if (typeof x === "object" && x !== null && "id" in x && typeof x.id === "string") {
    console.log(x.id)
  }
}

// Better: interface gives compile-time guarantee
interface DataWithId {
  id: string
}
function processData(x: DataWithId) {
  console.log(x.id) // always safe
}
```

---

### Antipattern C: Duplicating Type Definitions

```typescript
// Bad: same shape defined in multiple places
function createUser(u: { id: string; name: string }) { /*...*/ }
function updateUser(u: { id: string; name: string }) { /*...*/ }
function deleteUser(u: { id: string; name: string }) { /*...*/ }

// When you change the shape, you must update all three (error-prone)

// Better: single interface definition
interface User {
  id: string
  name: string
}
function createUser(u: User) { /*...*/ }
function updateUser(u: User) { /*...*/ }
function deleteUser(u: User) { /*...*/ }
```

---

### Antipattern D: Using Union Types for Everything

```typescript
// Bad: huge union for related functionality
type Processable =
  | { kind: "file"; path: string; read(): string }
  | { kind: "url"; href: string; fetch(): Promise<string> }
  | { kind: "memory"; data: string; get(): string }

function process(p: Processable) {
  switch (p.kind) {
    case "file": return p.read()
    case "url": return p.fetch()
    case "memory": return p.get()
  }
}

// Better: extract common interface
interface ContentSource {
  getContent(): string | Promise<string>
}

function process(s: ContentSource): string | Promise<string> {
  return s.getContent()
}

// Implementations satisfy the interface
class FileSource implements ContentSource {
  constructor(private path: string) {}
  getContent() { return fs.readFileSync(this.path, "utf8") }
}
```

---

### Antipattern E: Using Abstract Class When Interface Would Suffice

```typescript
// Bad: abstract class forces inheritance hierarchy
abstract class Service {
  abstract call(): void
}

class ApiService extends Service {
  call() { /*...*/ }
}

// To mock it, you MUST extend Service (boilerplate)
class MockService extends Service {
  call() { /*...*/ }
}

// Better: interface allows structural mocking
interface Service {
  call(): void
}

const mock: Service = { call: jest.fn() } // no class needed
```

---

### Antipattern F: Manual Type Checking Instead of Interface Constraint

```typescript
// Bad: runtime checks for type safety
function sortItems(items: unknown[], cmp: (a: unknown, b: unknown) => number) {
  if (!Array.isArray(items)) throw new Error("array required")
  return items.slice().sort(cmp)
}

// Better: interface constraint
interface Comparable {
  compareTo(other: Comparable): number
}

function sortItems<T extends Comparable>(items: T[]): T[] {
  return items.slice().sort((a, b) => a.compareTo(b))
}
```

---

### Antipattern G: Using Tagged Unions Excessively Instead of Polymorphism

```typescript
// Bad: repetitive switch on tags
type Shape =
  | { type: "circle"; radius: number }
  | { type: "rect"; width: number; height: number }

function area(s: Shape): number {
  if (s.type === "circle") return Math.PI * s.radius ** 2
  if (s.type === "rect") return s.width * s.height
  throw new Error("unknown shape")
}

// Every time you add a shape, you update all switches

// Better: interface with polymorphism
interface Shape {
  area(): number
}

class Circle implements Shape {
  constructor(private radius: number) {}
  area() { return Math.PI * this.radius ** 2 }
}

class Rect implements Shape {
  constructor(private w: number, private h: number) {}
  area() { return this.w * this.h }
}

function totalArea(shapes: Shape[]): number {
  return shapes.reduce((sum, s) => sum + s.area(), 0)
}
// Adding new shapes doesn't require updating totalArea
```

---

### Antipattern H: Passing Multiple Separate Arguments Instead of Interface

```typescript
// Bad: many arguments that logically belong together
function createServer(host: string, port: number, timeout: number, keepAlive: boolean, maxConnections: number) {
  // ...
}

// Easy to pass wrong values, hard to remember order

// Better: interface as single parameter
interface ServerConfig {
  host: string
  port: number
  timeout: number
  keepAlive: boolean
  maxConnections: number
}

function createServer(config: ServerConfig) {
  // ...
}

// Named parameters are clear, can add defaults
const defaults: ServerConfig = {
  host: "localhost",
  port: 3000,
  timeout: 5000,
  keepAlive: true,
  maxConnections: 100
}
createServer({ ...defaults, port: 8080 })
```

---
