# Runtime Polymorphism via Interfaces

> **Since:** TypeScript 1.0

## 1. What It Is

TypeScript achieves runtime polymorphism through three complementary mechanisms.

**Structural interfaces (open, implicit):** any value whose shape satisfies an interface is accepted by functions expecting that interface — no explicit `implements` declaration is required, though it aids error messages. Multiple classes, plain objects, or even functions can satisfy the same interface, and the caller dispatches through the interface without knowing the concrete type. This is TypeScript's default and corresponds to Go's implicit interfaces or Rust's `dyn Trait`.

**Abstract classes (nominal, explicit):** TypeScript also supports `abstract class`, which require explicit `extends` inheritance and can enforce implementation of abstract methods at the class-definition site rather than only at call sites. Abstract classes can carry constructor parameters, concrete default implementations, and `protected` members — things interfaces cannot express. This mirrors Python's `ABC` or Java's abstract classes. A class can extend only one abstract class but can implement multiple interfaces.

**Discriminated union dispatch:** a closed union of specific types, each carrying a literal discriminant tag, is narrowed to the exact member type in each branch — an alternative to open-ended interface polymorphism when the set of variants is known and fixed. The choice between interface/abstract-class and union mirrors the Rust `dyn Trait` vs enum pattern: interfaces for open extension, unions for closed exhaustive sets.

## 2. What Constraint It Lets You Express

**Pass values conforming to an interface without knowing their concrete type (open, extensible); or use discriminated unions for closed sets where every variant must be handled (exhaustive, no extension needed).**

- An interface-based API accepts any future implementor without recompilation; new types can be added anywhere and will work with existing consumers.
- A discriminated union-based API is exhaustively checked: adding a new variant causes a compile error at every unhandled switch, ensuring all cases are covered.
- The two can be combined: a union of interface types, where each member of the union satisfies a common interface but has additional variant-specific methods.

## 3. Minimal Snippet

```typescript
// --- Interface-based polymorphism (open set) ---
interface Logger {
  log(message: string): void;
  error(message: string, err?: Error): void;
}

class ConsoleLogger implements Logger {
  log(message: string) { console.log(message); }
  error(message: string, err?: Error) { console.error(message, err); }
}

class NoopLogger implements Logger {
  log(_message: string) {}
  error(_message: string, _err?: Error) {}
}

// Plain object also works — no class required
const fileLogger: Logger = {
  log: (msg) => fs.appendFileSync("app.log", msg + "\n"),
  error: (msg, err) => fs.appendFileSync("app.log", `ERROR: ${msg} ${err}\n`),
};

function processRequest(logger: Logger, data: unknown): void {
  logger.log("Processing request");
  // Works with any Logger implementor — current or future
}

processRequest(new ConsoleLogger(), {});
processRequest(new NoopLogger(), {});
processRequest(fileLogger, {});           // OK — plain object satisfies Logger

// --- Discriminated union dispatch (closed set) ---
type Notification =
  | { kind: "email"; to: string; subject: string }
  | { kind: "sms"; phone: string; body: string }
  | { kind: "push"; deviceToken: string; title: string };

function send(notification: Notification): void {
  switch (notification.kind) {
    case "email":
      sendEmail(notification.to, notification.subject);
      break;
    case "sms":
      sendSms(notification.phone, notification.body);
      break;
    case "push":
      sendPushNotification(notification.deviceToken, notification.title);
      break;
    default: {
      const _: never = notification; // error if a new variant is added without handling
    }
  }
}

// --- Combining: union of interface-typed objects ---
interface Serializer { serialize(data: unknown): string }
interface Parser { parse(raw: string): unknown }
type Codec = { kind: "json" } & Serializer & Parser | { kind: "xml" } & Serializer & Parser;
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Type Classes via Interfaces** [-> T05](T05-type-classes.md) | TypeScript interfaces function as structural type classes; an interface with a method like `compare(other: this): number` is an ad-hoc type class that any conforming type implicitly satisfies. |
| **Algebraic Data Types** [-> T01](T01-algebraic-data-types.md) | Discriminated unions are the alternative to interface polymorphism for closed type sets; the two patterns are complementary: use ADT when the set is fixed and exhaustiveness is required, use interface when the set is open and extension is expected. |
| **Type Narrowing** [-> T14](T14-type-narrowing.md) | When a parameter type is an interface, narrowing via `instanceof` (for class implementors), discriminant checks, or custom type guard functions brings the specific concrete type back into scope. |
| **Structural Typing** [-> T07](T07-structural-typing.md) | TypeScript's structural type system is what makes interface-based polymorphism work without explicit registration: any object with the right shape satisfies the interface, including plain object literals and objects from third-party libraries. |
| **Generics / Constraints** [-> T04](T04-generics-bounds.md) | `function render<T extends Drawable>(item: T): T` preserves the concrete type in the return while constraining the input — the TypeScript analogue of Rust's static dispatch via monomorphization. Use generics when the concrete return type matters; use interface parameters when it does not. |
| **Callable Typing** [-> T22](T22-callable-typing.md) | An interface with a `call` signature (e.g., `interface Handler { (req: Request): Response }`) is a typed function trait — more precise than a bare `(req: Request) => Response` because it can carry additional named properties alongside the call signature. |

## 5. Gotchas and Limitations

1. **Interfaces are open, unions are closed — choose deliberately** — accidentally using an interface for a set of types that should be exhaustively handled (e.g., a fixed set of HTTP status categories) gives up compile-time exhaustiveness checking; and accidentally using a union for an extensible plugin API makes adding new plugins require modifying the core union definition.
2. **No runtime type information from interfaces** — TypeScript interfaces are erased; there is no way to `instanceof` check against an interface at runtime; if runtime dispatch is needed, add a discriminant field or use `in` checks for key presence.
3. **Structural compatibility can be surprising** — an object with extra fields is assignable to an interface (structural excess is allowed in variables, not object literals); this means a `Dog` with a `bark()` method is assignable to a `Logger` if it also has `log` and `error`, which is usually not the intent.
4. **Method signature vs property function** — `interface { foo(): void }` and `interface { foo: () => void }` differ in variance: method signatures are bivariant under `--strictFunctionTypes`, while property functions are properly contravariant in parameters; prefer property function signatures for stricter checking.
5. **Union member count affects performance** — very large discriminated unions (hundreds of members) can slow TypeScript's type checker significantly; consider grouping related variants or using interface dispatch for large open sets.
6. **`implements` does not change runtime behavior** — `class Foo implements Logger` adds no runtime code; it only causes the compiler to verify `Foo`'s shape at the class declaration; a class without `implements` that satisfies the interface is equally usable.
7. **Abstract classes cannot be used with plain objects** — only an `extends` subclass satisfies an abstract class type; a plain object literal with the right shape does not, unlike interfaces. Choose `abstract class` when the nominal guarantee matters, `interface` when structural openness is desired.
8. **No downcast without a type guard** — TypeScript interfaces are erased at runtime; `instanceof MyInterface` is a compile error. Recovery from an interface type to a concrete type requires either `instanceof ClassName` (for class-based implementors) or a custom type predicate function. Mixing implementations that are not classes (plain objects) with those that are means `instanceof` alone is insufficient — write a discriminant-based type guard instead.

## 6. Beginner Mental Model

Think of a **structural interface** as a job posting that lists required skills — anyone who has those skills gets the role, no formal certificate (class declaration) required. A plain object with the right shape, a class that never wrote `implements`, and a mock in a test all qualify equally.

An **abstract class** is more like a franchise agreement — you must formally sign up (`extends`) and agree to supply the missing pieces (`abstract` methods), but the franchisor provides shared infrastructure (concrete methods, constructor parameters, protected state) that every franchisee inherits.

A **discriminated union** is a sealed enumeration of named cases. The dispatcher is a `switch` that must cover every case or the compiler complains. Add a new variant and every unhandled switch turns into a compile error — the opposite of open extension.

The key choice: **use an interface (or abstract class) when new implementors should be addable without touching existing code; use a discriminated union when the full set of variants must be known and every handler must be exhaustive.**

## 7. Extended Examples

### Example A — Abstract class (nominal) for shared infrastructure

```typescript
abstract class Exporter {
  abstract export(data: Record<string, unknown>): Uint8Array;
  abstract contentType(): string;

  // Shared concrete behavior — subclasses inherit this for free
  send(data: Record<string, unknown>): void {
    const payload = this.export(data);
    console.log(`Sending ${payload.byteLength} bytes as ${this.contentType()}`);
  }
}

class JsonExporter extends Exporter {
  export(data: Record<string, unknown>): Uint8Array {
    return new TextEncoder().encode(JSON.stringify(data));
  }
  contentType() { return "application/json"; }
}

class CsvExporter extends Exporter {
  export(data: Record<string, unknown>): Uint8Array {
    const header = Object.keys(data).join(",");
    const values = Object.values(data).join(",");
    return new TextEncoder().encode(`${header}\n${values}`);
  }
  contentType() { return "text/csv"; }
}

function sendReport(exporter: Exporter, data: Record<string, unknown>) {
  exporter.send(data);               // dispatches to the concrete subclass
}

sendReport(new JsonExporter(), { name: "Alice", score: 95 });
sendReport(new CsvExporter(), { name: "Alice", score: 95 });
// new Exporter()  // compile error: cannot instantiate abstract class
```

### Example B — Heterogeneous collection with interface

```typescript
interface Shape {
  area(): number;
  perimeter(): number;
}

class Circle implements Shape {
  constructor(private r: number) {}
  area() { return Math.PI * this.r ** 2; }
  perimeter() { return 2 * Math.PI * this.r; }
}

class Rect implements Shape {
  constructor(private w: number, private h: number) {}
  area() { return this.w * this.h; }
  perimeter() { return 2 * (this.w + this.h); }
}

// Plain object also satisfies Shape — no class needed
const triangle: Shape = {
  area: () => 0.5 * 6 * 4,
  perimeter: () => 6 + 4 + Math.hypot(6, 4),
};

const shapes: Shape[] = [new Circle(3), new Rect(4, 5), triangle];

const totalArea = shapes.reduce((sum, s) => sum + s.area(), 0);
console.log(totalArea.toFixed(2)); // 56.27
```

### Example C — Static vs dynamic dispatch

```typescript
interface Renderer { render(): string; }

class Png implements Renderer { render() { return "PNG bytes"; } }
class Svg implements Renderer { render() { return "<svg/>"; } }

// Static-style: generic preserves the concrete type in the return
function transformStatic<T extends Renderer>(item: T): T {
  console.log(item.render()); // TypeScript resolves via the static type bound
  return item;               // return type is T, not Renderer
}

// Dynamic-style: single function body, concrete type erased
function transformDynamic(item: Renderer): string {
  return item.render();      // return type is string, not the concrete class
}

const png = transformStatic(new Png()); // type is Png, not Renderer
const result = transformDynamic(new Svg()); // type is string
```

### Example D — Runtime narrowing and downcast

```typescript
interface Animal { name: string; speak(): string; }

class Dog implements Animal {
  constructor(public name: string) {}
  speak() { return "Woof"; }
  fetch() { return `${this.name} fetches the ball`; }
}

class Cat implements Animal {
  constructor(public name: string) {}
  speak() { return "Meow"; }
  purr() { return `${this.name} purrs`; }
}

// Type predicate: manual downcast for interface types
function isDog(a: Animal): a is Dog { return a instanceof Dog; }

const animals: Animal[] = [new Dog("Rex"), new Cat("Whiskers"), new Dog("Buddy")];

for (const animal of animals) {
  console.log(animal.speak()); // polymorphic dispatch — no type info needed

  if (isDog(animal)) {
    console.log(animal.fetch()); // narrowed to Dog — Dog-specific method available
  }
}

// For plain-object implementors (no class), use 'in' or a discriminant field
interface Vehicle { kind: "car" | "bike"; move(): void; }
const car: Vehicle = { kind: "car", move() { console.log("vroom"); } };

if (car.kind === "car") {
  // narrowed to the "car" variant
}
```

### Example E — Plugin registry (open extension without modifying core)

```typescript
interface Plugin {
  id: string;
  execute(input: string): string;
}

class PluginRegistry {
  private plugins = new Map<string, Plugin>();

  register(plugin: Plugin): void {
    this.plugins.set(plugin.id, plugin);
  }

  run(id: string, input: string): string {
    const plugin = this.plugins.get(id);
    if (!plugin) throw new Error(`Unknown plugin: ${id}`);
    return plugin.execute(input);   // dispatch to whatever was registered
  }
}

// Core ships with no knowledge of these concrete types
const registry = new PluginRegistry();

registry.register({ id: "upper", execute: (s) => s.toUpperCase() });
registry.register({ id: "reverse", execute: (s) => s.split("").reverse().join("") });

console.log(registry.run("upper", "hello"));   // HELLO
console.log(registry.run("reverse", "hello")); // olleh
// New plugins can be registered without touching PluginRegistry
```

## 8. Use-Case Cross-References

- [-> UC-14](../usecases/UC14-extensibility.md) Use interface-based polymorphism for extensible plugin APIs where new implementations can be added without modifying existing code
- [-> UC-05](../usecases/UC05-structural-contracts.md) Define structural contracts as interfaces so that any conforming value — class, plain object, or function — can satisfy the contract

## 9. When to Use

- **Plugins/extensions**: When third parties should add implementations without modifying your core code.
- **Strategy pattern**: When behavior should be swappable at runtime (e.g., `PaymentStrategy`, `CompressionStrategy`).
- **Testing**: When you want to inject mocks/stubs that satisfy the same interface as production code.
- **Heterogeneous collections**: When you need a single collection holding different concrete types that share behavior.

```typescript
// Strategy pattern — behavior is swappable
interface Strategy { execute(x: number): number; }
const double: Strategy = { execute: (x) => x * 2 };
const square: Strategy = { execute: (x) => x * x };
function apply(s: Strategy, x: number) { return s.execute(x); }
apply(double, 5); // 10
apply(square, 5); // 25
```

## 10. When Not to Use

- **Closed sets requiring exhaustive handling**: Use discriminated unions — interfaces give no compile-time warning when a variant is unhandled.
- **Stateless utility functions**: A plain function or generic is simpler; interfaces add unnecessary indirection.
- **Performance-critical hot paths**: Dynamic dispatch has runtime cost; generics (static dispatch) may be preferable.
- **When you need `this` typing**: Interfaces cannot type member methods against `this`; use a base class instead.

```typescript
// Anti-example: closed set with interface loses exhaustiveness
interface Status { kind: "ok" | "err"; }
function handle(s: Status) {
  if (s.kind === "ok") { /* "err" case easily forgotten */ }
}

// Better: discriminated union enforces exhaustiveness
type Status = { kind: "ok" } | { kind: "err"; code: number };
function handle(s: Status) {
  switch (s.kind) {
    case "ok": break;
    case "err": break; // compiler enforces handling both
  }
}
```

## 11. Antipatterns When Using This Technique

### A. Fat interface — coupling unrelated concerns

```typescript
// BAD: mixes orthogonal concerns
interface Service {
  process(): void;
  toJSON(): string;
  saveToFile(): void;
  log(): void;
}

// BETTER: separate interfaces per concern
interface Processable { process(): void; }
interface Serializable { toJSON(): string; }
```

### B. Accidentally allowing unrelated types (structural overmatch)

```typescript
// BAD: Dog satisfies Pet interface by accident
interface Pet { meow(): string; }
class Dog { meow() { return ""; } } // wrong but type-checks!
const pet: Pet = new Dog();

// BETTER: add a nominal tag or use abstract class
interface Pet { _pet: true; meow(): string; }
```

### C. Interface drift — modifying core interface breaks all consumers

```typescript
// BAD: adding required field to shared interface breaks existing implementors
interface Payload { id: string; }
// later: interface Payload { id: string; metadata: Record<string, unknown>; } // breaks existing code!

// BETTER: use interface merging or extend with optional
interface Payload { id: string; }
interface PayloadWithMeta extends Payload { metadata?: Record<string, unknown>; }
```

## 12. Antipatterns with Other Techniques (Where This Helps)

### A. Using generics when interface is sufficient

```typescript
// BAD: generic preserves concrete type unnecessarily, complicates API
function process<T extends { run(): void }>(item: T) { item.run(); }
process({ run() {} }); // type is inferred fully, harder to compose

// BETTER: interface erases concrete type, simpler to combine
function process(item: Runnable) { item.run(); }
interface Runnable { run(): void; }
```

### B. Deep inheritance hierarchies instead of composition

```typescript
// BAD: inheritance explosion
class Reader {}
class FileReader extends Reader {}
class BufferedReader extends FileReader {}
class ErrorHandlingBufferedReader extends BufferedReader {} // fragile

// BETTER: compose via interfaces
class ReaderImpl implements Reader { /* ... */ }
class BufferedReaderImpl implements Reader {
  constructor(private inner: Reader) {}
  read() { /* wraps inner */ }
}
class ErrorHandlingReader implements Reader {
  constructor(private inner: Reader) {}
  read() { /* catches errors from inner */ }
}
```

### C. Repeating type definitions per union variant

```typescript
// BAD: duplicated structure across union
type Entity =
  | { type: "user"; id: string; name: string; save(): void; }
  | { type: "post"; id: string; title: string; save(): void; };

// BETTER: interface shares common structure
type Entity =
  | ({ type: "user" } & Saveable & { name: string })
  | ({ type: "post" } & Saveable & { title: string });
interface Saveable { id: string; save(): void; }
```

## Source Anchors

- [TypeScript Handbook — Interfaces](https://www.typescriptlang.org/docs/handbook/2/objects.html)
- [TypeScript Handbook — Classes (abstract)](https://www.typescriptlang.org/docs/handbook/2/classes.html#abstract-classes-and-members)
- [TypeScript Handbook — Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- [TypeScript Handbook — More on Functions (generics vs overloads)](https://www.typescriptlang.org/docs/handbook/2/functions.html)
- [TypeScript FAQ — Why are function parameters bivariant?](https://github.com/microsoft/TypeScript/wiki/FAQ#why-are-function-parameters-bivariant)
