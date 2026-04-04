# Callable Types & Overloads

> **Since:** TypeScript 1.0

## 1. What It Is

TypeScript models functions as first-class types in several ways. A **function type** `(a: A, b: B) => C` describes the shape of a function inline. A **call signature** in an interface `{ (a: A): B; label: string }` allows objects that are both callable and have properties. A **construct signature** `{ new (a: A): B }` describes a class constructor as a type. **Overload signatures** express that a single function has multiple valid input/output combinations: you write several signature-only declarations above the single implementation signature, and TypeScript ensures callers can only use the listed overloads. Generic functions (`<T>(x: T) => T`) abstract over types while preserving the relationship between inputs and outputs. The utility types `ReturnType<F>`, `Parameters<F>`, `ConstructorParameters<F>`, and `ThisParameterType<F>` extract type information from function types.

## 2. What Constraint It Lets You Express

**Constrain which input/output type combinations are valid for a function; overload signatures make impossible or undefined argument combinations into compile errors.**

- Overloads document and enforce which argument combinations are meaningful — for example, `createElement("div")` returning `HTMLDivElement` and `createElement("canvas")` returning `HTMLCanvasElement`, but not `createElement(unknown)` returning `HTMLElement`.
- Generic functions preserve the relationship between input and output types — `identity<T>(x: T): T` guarantees the return type equals the input type, not just `unknown`.
- Call signatures on interfaces allow typed callable objects with additional properties (e.g., middleware chains, event emitters).

## 3. Minimal Snippet

```typescript
// --- Overloaded function: createElement ---
function createElement(tag: "div"): HTMLDivElement;
function createElement(tag: "canvas"): HTMLCanvasElement;
function createElement(tag: "input"): HTMLInputElement;
function createElement(tag: string): HTMLElement {
  return document.createElement(tag);
}

const div = createElement("div");       // OK — HTMLDivElement
const canvas = createElement("canvas"); // OK — HTMLCanvasElement
// const unknown = createElement("span"); // error — not an overloaded signature

// --- Generic identity: preserves input type ---
function identity<T>(x: T): T {
  return x;
}
const s = identity("hello"); // OK — string (not widened to unknown)
const n = identity(42);      // OK — number

// --- Callable interface with properties ---
interface Formatter {
  (value: unknown): string;
  locale: string;
}

const fmt: Formatter = Object.assign(
  (v: unknown) => String(v),
  { locale: "en-US" }
);
console.log(fmt(42), fmt.locale); // OK

// --- ReturnType / Parameters utility types ---
function fetchUser(id: string, token: string): Promise<User> {
  return fetch(`/users/${id}`).then(r => r.json());
}

type FetchParams = Parameters<typeof fetchUser>; // OK — [id: string, token: string]
type FetchReturn = ReturnType<typeof fetchUser>;  // OK — Promise<User>
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Generics & Bounds** [-> T04](T04-generics-bounds.md) | Generic function types are the most common use of generics; bounds (`<T extends Comparable>`) restrict which types can be substituted, combining callable typing with constraint enforcement. |
| **Variadic Tuple Types** [-> T45](T45-paramspec-variadic.md) | `...args: T[]` and `ParameterSpec` (via `infer` in conditional types) allow generic functions that forward or wrap arbitrary parameter lists, enabling typed middleware and decorator patterns. |
| **Associated Types / Utility Types** [-> T49](T49-associated-types.md) | `ReturnType<F>`, `Parameters<F>`, and `ConstructorParameters<F>` are built-in type-level functions that extract type information from callable types, acting as TypeScript's associated-type analogs. |
| **Polymorphic `this`** [-> T33](T33-self-type.md) | Methods with a `this` return type use `this` as an implicit callable type; the receiver's type flows through call chains, composing with overloads in fluent builders. |

## 5. Gotchas and Limitations

1. **Overload implementation is not a public overload** — the implementation signature (the last one with a body) is not visible to callers; only the preceding signature-only declarations are; the implementation signature must be broad enough to accept all listed overloads.
2. **Overloads are checked top-to-bottom** — TypeScript picks the first matching overload; if a broader overload appears before a narrower one, the narrower one is unreachable; always order from most-specific to least-specific.
3. **Generic inference can fail with overloads** — when a generic function is passed as a callback, TypeScript may not be able to infer the type parameter through overload resolution; explicit type arguments may be required.
4. **`Function` type is too broad** — using `Function` as a parameter type accepts any callable but loses all parameter and return type information; prefer explicit function types or generics over `Function`.
5. **Call signatures in interfaces vs `type`** — call signatures can be written in both `interface` and `type` aliases; prefer `type` for plain function types (cleaner syntax) and `interface` only when you need declaration merging or a callable-with-properties shape.
6. **Optional and rest parameters in overloads** — rest parameters in overloads interact with inference in subtle ways; a rest overload `(...args: string[])` can shadow more specific earlier overloads if types overlap.

## 6. Use-Case Cross-References

- [-> UC-07](../usecases/UC07-callable-contracts.md) Enforce callable contracts with precise input/output type pairings via overloads and generic function types
- [-> UC-04](../usecases/UC04-generic-constraints.md) Express generic algorithms that preserve the relationship between parameter types and return types
