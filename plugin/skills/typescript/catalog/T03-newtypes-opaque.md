# Branded & Opaque Types

> **Since:** TypeScript community pattern; `unique symbol` available since TypeScript 2.7

## 1. What It Is

TypeScript has no native `newtype` or `opaque type` keyword. The **branded type pattern** is the idiomatic workaround: intersect a base type with a phantom object type carrying a `unique symbol` brand property that never exists at runtime. Because `unique symbol` creates a globally unique type that cannot be constructed without explicit typing, two branded types over the same base — `UserId` and `OrderId`, both wrapping `string` — are structurally incompatible even though their runtime representation is identical. A **smart constructor** is a function (or namespace function) that validates a raw value and returns the branded type, serving as the single creation point. Some codebases use string-literal brands (`{ readonly __brand: "UserId" }`) instead of `unique symbol`; this is simpler but allows accidental brand forgery with an explicit cast.

## 2. What Constraint It Lets You Express

**Two values with the same runtime representation are incompatible at compile time; passing a raw value where a branded type is required is a compile error.**

- `UserId` and `OrderId` are both `string` at runtime, but `function getUser(id: UserId)` rejects a plain `string` or an `OrderId`.
- The brand can encode validation: `type NonEmptyString = string & { readonly __brand: unique symbol }` is only constructible via a smart constructor that checks `s.length > 0`.
- Brands compose: `type PositiveInt = number & Branded<"PositiveInt">` can be further intersected with other brands.

## 3. Minimal Snippet

```typescript
// Unique-symbol brand helper
declare const __brand: unique symbol;
type Brand<B> = { readonly [__brand]: B };
type Branded<T, B> = T & Brand<B>;

// Two branded string types — incompatible despite same base
type UserId  = Branded<string, "UserId">;
type OrderId = Branded<string, "OrderId">;

// Smart constructors — the only way to create branded values
function makeUserId(raw: string): UserId {
  if (!raw.startsWith("usr_")) throw new Error("Invalid UserId");
  return raw as UserId; // safe: validated above
}

function makeOrderId(raw: string): OrderId {
  if (!raw.startsWith("ord_")) throw new Error("Invalid OrderId");
  return raw as OrderId;
}

function getUser(id: UserId): string {
  return `User: ${id}`;
}

const uid  = makeUserId("usr_42");
const oid  = makeOrderId("ord_99");

getUser(uid);         // OK
// getUser(oid);      // error — Argument of type 'OrderId' is not assignable to 'UserId'
// getUser("usr_42"); // error — Argument of type 'string' is not assignable to 'UserId'

// Simpler string-literal brand (allows forgery via cast, but more readable)
type Email = string & { readonly __brand: "Email" };
const forged = "bad" as Email; // OK at compile time — brand is not enforced at runtime
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Phantom / Erased Types** [-> T27](T27-erased-phantom.md) | Brands are a specific application of phantom types: the brand property exists in the type system only, never at runtime. The `unique symbol` technique is one way to create an uninhabitable phantom field. |
| **Refinement Types** [-> T26](T26-refinement-types.md) | Branded types approximate refinement types by encoding a predicate in the brand name and enforcing it in the smart constructor; unlike true refinement types the compiler does not verify the predicate itself. |
| **Discriminated Unions & ADTs** [-> T01](T01-algebraic-data-types.md) | ADT variants can carry branded field types: `{ kind: "order"; id: OrderId }` ensures that even after narrowing, the ID cannot be confused with a user ID. |
| **Callable Typing** [-> T22](T22-callable-typing.md) | Smart constructors are often expressed as overloaded functions or as a namespace+type pair, using call signatures to make the construction point explicit and testable. |

## 5. Gotchas and Limitations

1. **No runtime enforcement** — the brand is entirely erased at runtime. If you bypass the smart constructor with `as`, the brand offers no protection. Smart constructors are the discipline that makes the pattern safe.
2. **String-literal brands can be forged** — `"anything" as Email` compiles without error when the brand is a string literal field. `unique symbol` brands are harder to forge accidentally but require a shared declaration.
3. **JSON round-trips erase brands** — deserializing JSON always yields unbranded `string`/`number`/etc. You must re-validate and re-brand at the deserialization boundary.
4. **`unique symbol` must be `declare const`** — the brand symbol must be declared with `declare const`, not `const`, to avoid emitting a runtime value.
5. **Type errors can be verbose** — when a branded type mismatch occurs, the error message includes the phantom brand field, which can confuse developers unfamiliar with the pattern.
6. **Libraries may not accept branded types** — third-party APIs typed as accepting `string` will accept a `UserId` (because `UserId` structurally extends `string`), but APIs returning `string` will not automatically produce a `UserId`; you need an explicit re-brand.

## Coming from JavaScript

JavaScript has no type-level distinction between two `string` values. The branded type pattern is purely a TypeScript compile-time enforcement mechanism; at runtime, a `UserId` is just a `string`. The pattern fills the gap left by the absence of `newtype` (Haskell/Rust/Scala) or `opaque type` (Flow) in TypeScript's type system.

## 6. Use-Case Cross-References

- [-> UC-01](../usecases/UC01-invalid-states.md) Prevent mixing of semantically distinct IDs or values with the same runtime type
- [-> UC-02](../usecases/UC02-domain-modeling.md) Model domain primitives (UserId, OrderId, Email) as incompatible types
- [-> UC-09](../usecases/UC09-builder-config.md) Smart constructors as the branded-type equivalent of validated builder steps
