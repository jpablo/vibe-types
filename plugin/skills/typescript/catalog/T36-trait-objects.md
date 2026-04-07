# Runtime Polymorphism via Interfaces

> **Since:** TypeScript 1.0

## 1. What It Is

TypeScript achieves runtime polymorphism through two complementary mechanisms. The first is **structural interfaces with multiple implementors**: any value whose shape satisfies an interface is accepted by functions expecting that interface — no explicit `implements` declaration is required, though it aids error messages. Multiple classes, plain objects, or even functions can satisfy the same interface, and the caller dispatches through the interface without knowing the concrete type. The second is **discriminated union dispatch**: a closed union of specific types, each carrying a literal discriminant tag, is narrowed to the exact member type in each branch — an alternative to open-ended interface polymorphism when the set of variants is known and fixed. The choice between the two mirrors the Rust `dyn Trait` vs enum pattern: interfaces for open extension, unions for closed exhaustive sets.

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
| **Type Narrowing** [-> T14](T14-type-narrowing.md) | When a parameter type is an interface, narrowing via `instanceof` (for class implementors) or discriminant checks (for union members implementing an interface) brings the specific type into scope. |
| **Structural Typing** [-> T07](T07-structural-typing.md) | TypeScript's structural type system is what makes interface-based polymorphism work without explicit registration: any object with the right shape satisfies the interface, including plain object literals and objects from third-party libraries. |

## 5. Gotchas and Limitations

1. **Interfaces are open, unions are closed — choose deliberately** — accidentally using an interface for a set of types that should be exhaustively handled (e.g., a fixed set of HTTP status categories) gives up compile-time exhaustiveness checking; and accidentally using a union for an extensible plugin API makes adding new plugins require modifying the core union definition.
2. **No runtime type information from interfaces** — TypeScript interfaces are erased; there is no way to `instanceof` check against an interface at runtime; if runtime dispatch is needed, add a discriminant field or use `in` checks for key presence.
3. **Structural compatibility can be surprising** — an object with extra fields is assignable to an interface (structural excess is allowed in variables, not object literals); this means a `Dog` with a `bark()` method is assignable to a `Logger` if it also has `log` and `error`, which is usually not the intent.
4. **Method signature vs property function** — `interface { foo(): void }` and `interface { foo: () => void }` differ in variance: method signatures are bivariant under `--strictFunctionTypes`, while property functions are properly contravariant in parameters; prefer property function signatures for stricter checking.
5. **Union member count affects performance** — very large discriminated unions (hundreds of members) can slow TypeScript's type checker significantly; consider grouping related variants or using interface dispatch for large open sets.
6. **`implements` does not change runtime behavior** — `class Foo implements Logger` adds no runtime code; it only causes the compiler to verify `Foo`'s shape at the class declaration; a class without `implements` that satisfies the interface is equally usable.

## 6. Use-Case Cross-References

- [-> UC-14](../usecases/UC14-extensibility.md) Use interface-based polymorphism for extensible plugin APIs where new implementations can be added without modifying existing code
- [-> UC-05](../usecases/UC05-structural-contracts.md) Define structural contracts as interfaces so that any conforming value — class, plain object, or function — can satisfy the contract
