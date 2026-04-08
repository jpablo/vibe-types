# Branded & Opaque Types

> **Since:** TypeScript community pattern; `unique symbol` available since TypeScript 2.7

## 1. What It Is

TypeScript has no native `newtype` or `opaque type` keyword. The **branded type pattern** is the idiomatic workaround: intersect a base type with a phantom object type carrying a `unique symbol` brand property that never exists at runtime. Because `unique symbol` creates a globally unique type that cannot be constructed without explicit typing, two branded types over the same base — `UserId` and `OrderId`, both wrapping `string` — are structurally incompatible even though their runtime representation is identical. A **smart constructor** is a function (or namespace function) that validates a raw value and returns the branded type, serving as the single creation point. Some codebases use string-literal brands (`{ readonly __brand: "UserId" }`) instead of `unique symbol`; this is simpler but allows accidental brand forgery with an explicit cast.

Contrast this with plain **type aliases** (`type UserId = string`), which create a transparent synonym: the compiler treats `UserId` and `string` as identical everywhere. Aliases are appropriate for readability; branded types are required when you need the compiler to reject accidental mixing. See [→ T23](T23-type-aliases.md).

## 2. What Constraint It Lets You Express

**Two values with the same runtime representation are incompatible at compile time; passing a raw value where a branded type is required is a compile error.**

- `UserId` and `OrderId` are both `string` at runtime, but `function getUser(id: UserId)` rejects a plain `string` or an `OrderId`.
- The brand can encode validation: `type NonEmptyString = string & { readonly __brand: unique symbol }` is only constructible via a smart constructor that checks `s.length > 0`.
- Brands compose: `type PositiveInt = number & Branded<"PositiveInt">` can be further intersected with other brands.
- The smart constructor is the single enforcement point: once the brand is applied there, it propagates through the type system automatically.

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
| **Type Aliases** [→ T23](T23-type-aliases.md) | Type aliases (`type UserId = string`) are transparent: the compiler treats them as identical to the base type. Branded types are the opaque end of the spectrum — use aliases for readability, branded types when you need compile-time separation. |
| **Phantom / Erased Types** [→ T27](T27-erased-phantom.md) | Brands are a specific application of phantom types: the brand property exists in the type system only, never at runtime. The `unique symbol` technique is one way to create an uninhabitable phantom field. |
| **Refinement Types** [→ T26](T26-refinement-types.md) | Branded types approximate refinement types by encoding a predicate in the brand name and enforcing it in the smart constructor; unlike true refinement types the compiler does not verify the predicate itself. |
| **Discriminated Unions & ADTs** [→ T01](T01-algebraic-data-types.md) | ADT variants can carry branded field types: `{ kind: "order"; id: OrderId }` ensures that even after narrowing, the ID cannot be confused with a user ID. |
| **Callable Typing** [→ T22](T22-callable-typing.md) | Smart constructors are often expressed as overloaded functions or as a namespace+type pair, using call signatures to make the construction point explicit and testable. |
| **Encapsulation** [→ T21](T21-encapsulation.md) | Module boundaries enforce the smart-constructor pattern: export the branded `type` but keep the raw cast unexported. Callers can use the type in signatures but cannot mint values without going through the constructor. |
| **Literal Types** [→ T52](T52-literal-types.md) | String-literal brands (`{ readonly __brand: "Email" }`) use TypeScript's literal type system. Unique-symbol brands are stronger: each `unique symbol` declaration is a singleton type that cannot be constructed outside its declaration site. |

## 5. Gotchas and Limitations

1. **No runtime enforcement** — the brand is entirely erased at runtime. If you bypass the smart constructor with `as`, the brand offers no protection. Smart constructors are the discipline that makes the pattern safe.
2. **String-literal brands can be forged** — `"anything" as Email` compiles without error when the brand is a string literal field. `unique symbol` brands are harder to forge accidentally but require a shared declaration.
3. **JSON round-trips erase brands** — deserializing JSON always yields unbranded `string`/`number`/etc. You must re-validate and re-brand at the deserialization boundary.
4. **`unique symbol` must be `declare const`** — the brand symbol must be declared with `declare const`, not `const`, to avoid emitting a runtime value.
5. **Type errors can be verbose** — when a branded type mismatch occurs, the error message includes the phantom brand field, which can confuse developers unfamiliar with the pattern.
6. **Libraries may not accept branded types** — third-party APIs typed as accepting `string` will accept a `UserId` (because `UserId` structurally extends `string`), but APIs returning `string` will not automatically produce a `UserId`; you need an explicit re-brand.
7. **Arithmetic erases the brand** — `UserId(1) + UserId(2)` does not exist in TypeScript as a type-level concept, but for branded numbers: `type Milliseconds = Branded<number, "Milliseconds">; const a: Milliseconds = ...; const b: Milliseconds = ...; const c = a + b;` — `c` is inferred as `number`, not `Milliseconds`. Re-wrap explicitly if the result should remain branded: `(a + b) as Milliseconds`.
8. **No automatic method delegation** — unlike Rust newtypes or Haskell's `newtype deriving`, branded types provide no mechanism to automatically expose the underlying type's methods under the new name. The brand is an intersection, so the base type's methods are directly available — which can undermine the abstraction if you want to prevent certain operations.

## 6. Beginner Mental Model

Think of a branded type as a **colored sticker on a value**. A `UserId` is a `string` with a "user-id" sticker. The type checker can see the sticker and will complain if you try to use a "user-id" sticker where an "order-id" sticker is expected. At runtime, the sticker does not exist — it is purely a compile-time label.

The smart constructor is the **sticker gun**: it validates the value and applies the sticker. Once applied, the sticker travels with the value through the type system. `as UserId` is a manual sticker application — valid inside the constructor where validation has already happened, but dangerous if scattered through the codebase.

Coming from other languages:
- Rust: `struct UserId(String)` with a private field ≈ a branded type plus module-level encapsulation. Rust's version has stronger runtime guarantees; TypeScript's is zero-cost.
- Python `NewType`: same semantic goal, same zero-runtime-cost. Python has `isinstance` limitations; TypeScript has the same runtime-erasure limitation.
- Scala `opaque type`: enforced at module scope by the compiler; TypeScript relies on the discipline of not using `as` outside smart constructors.
- Flow: had a native `opaque type` keyword. TypeScript's branded pattern is the community-standard substitute.

## 7. Module-Level Encapsulation Pattern

Export the type but keep the raw cast inside the module boundary. Callers can use `UserId` in type positions but cannot create values without going through `make`:

```typescript
// userId.ts
declare const __userIdBrand: unique symbol;
export type UserId = string & { readonly [__userIdBrand]: true };

export function makeUserId(raw: string): UserId {
  if (!/^usr_\w+$/.test(raw)) throw new Error(`Invalid UserId: ${raw}`);
  return raw as UserId; // the only `as UserId` in the codebase
}

export function unwrapUserId(id: UserId): string {
  return id; // UserId extends string, so this is safe and implicit
}
```

```typescript
// elsewhere.ts
import { UserId, makeUserId } from "./userId";

// Cannot write `"usr_42" as UserId` — __userIdBrand is not exported
// Must go through the constructor:
const id = makeUserId("usr_42");
```

This is the TypeScript analog of Lean's `private` constructor or Rust's private field — the module boundary replaces the language keyword.

## 8. Example A — Swapped-argument bug prevention

```typescript
declare const __brand: unique symbol;
type Brand<B> = { readonly [__brand]: B };
type Branded<T, B> = T & Brand<B>;

type UserId  = Branded<string, "UserId">;
type OrderId = Branded<string, "OrderId">;

declare function makeUserId(s: string): UserId;
declare function makeOrderId(s: string): OrderId;

function cancelOrder(orderId: OrderId, cancelledBy: UserId): void {
  console.log(`Order ${orderId} cancelled by ${cancelledBy}`);
}

const user  = makeUserId("usr_1001");
const order = makeOrderId("ord_5042");

cancelOrder(order, user);   // OK
// cancelOrder(user, order); // error: Argument of type 'UserId' is not assignable to 'OrderId'
```

## 9. Example B — Sanitized HTML (security use case)

Branded types work for safety invariants beyond IDs. Here the type encodes "this string has been HTML-escaped":

```typescript
declare const __safeHtmlBrand: unique symbol;
type SafeHtml = string & { readonly [__safeHtmlBrand]: true };

function escapeHtml(raw: string): SafeHtml {
  return raw
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;") as SafeHtml;
}

function renderPage(title: string, body: SafeHtml): string {
  // title is unescaped — intentional (we control it)
  // body is guaranteed to be escaped by the type system
  return `<html><head><title>${title}</title></head><body>${body}</body></html>`;
}

const userInput = "<script>alert('xss')</script>";

// renderPage("Home", userInput);       // error: 'string' is not assignable to 'SafeHtml'
renderPage("Home", escapeHtml(userInput)); // OK — must go through the sanitizer

// SafeHtml is still a string — existing string operations work:
console.log(escapeHtml(userInput).length); // OK
const log: string = escapeHtml(userInput); // OK — SafeHtml extends string
```

## Common Type-Checker Errors

### Passing base type where branded type is expected

```
Argument of type 'string' is not assignable to parameter of type 'UserId'.
  Type 'string' is not assignable to type '{ readonly [__brand]: "UserId"; }'.
```

**Cause:** You passed a raw value without wrapping it.
**Fix:** Pass the value through the smart constructor: `makeUserId(raw)`.

### Swapping two branded types of the same base

```
Argument of type 'OrderId' is not assignable to parameter of type 'UserId'.
  Type 'OrderId' is not assignable to type '{ readonly [__brand]: "UserId"; }'.
```

**Cause:** Two branded types built on the same base are not interchangeable. Arguments are in the wrong order.
**Fix:** Check parameter order and use the correct branded value.

### Arithmetic result is no longer branded

```
Type 'number' is not assignable to type 'Milliseconds'.
```

**Cause:** `a + b` where both are `Branded<number, "Milliseconds">` returns `number`, not `Milliseconds`.
**Fix:** Re-wrap: `(a + b) as Milliseconds` inside a function that semantically validates this is correct.

## 10. Use-Case Cross-References

- [→ UC-01](../usecases/UC01-invalid-states.md) Prevent mixing of semantically distinct IDs or values with the same runtime type
- [→ UC-02](../usecases/UC02-domain-modeling.md) Model domain primitives (UserId, OrderId, Email) as incompatible types
- [→ UC-09](../usecases/UC09-builder-config.md) Smart constructors as the branded-type equivalent of validated builder steps
