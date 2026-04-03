# Phantom Types

> **Since:** TypeScript community pattern; `unique symbol` since TypeScript 2.7

## 1. What It Is

A **phantom type** carries type-level information that has no runtime representation. In TypeScript, the pattern is achieved via brand intersection: `type Tagged<T, Brand> = T & { readonly __tag: Brand }`. The `__tag` field is never actually present on the value at runtime — the cast is performed with `as` in a smart constructor — so there is zero runtime overhead. Phantom types are used to encode categorical properties: units of measure (prevent adding meters to feet), state-machine states (prevent calling `send()` on an already-sent email), capability tokens (only code that holds a `Permission<"admin">` can call admin APIs), and phantom lifetimes (ensure a borrowed reference does not outlive its owner, at the type level).

## 2. What Constraint It Lets You Express

**Type-level markers track states or properties with zero runtime overhead; operations that mix incompatible phantom types or violate state transitions are compile errors.**

- A value of type `Quantity<Meters>` is structurally a `number`, but the compiler rejects adding it to a `Quantity<Feet>` without explicit conversion.
- A `Connection<"open">` can call `.query()` while a `Connection<"closed">` cannot, with no runtime check needed in `.query()` itself.
- Phantom type parameters can be covariant or contravariant, enabling fine-grained subtyping relationships between phantom-branded values.

## 3. Minimal Snippet

```typescript
// --- Units of measure phantom type ---
declare const __unit: unique symbol;
type Quantity<Unit> = number & { readonly [__unit]: Unit };

// Phantom "tag" types — never instantiated as values
declare const Meters: unique symbol;
declare const Feet: unique symbol;
type Meters = typeof Meters;
type Feet = typeof Feet;

function meters(n: number): Quantity<Meters> {
  return n as Quantity<Meters>;
}

function feet(n: number): Quantity<Feet> {
  return n as Quantity<Feet>;
}

function addMeters(a: Quantity<Meters>, b: Quantity<Meters>): Quantity<Meters> {
  return (a + b) as Quantity<Meters>;
}

const m1 = meters(10);
const f1 = feet(30);
addMeters(m1, meters(5));    // OK
// addMeters(m1, f1);           // error — Quantity<Feet> is not assignable to Quantity<Meters>

// --- Phantom state: typestate pattern ---
declare const __state: unique symbol;
type EmailMessage<State extends "draft" | "sent"> = {
  readonly body: string;
  readonly [__state]: State;
};

function createDraft(body: string): EmailMessage<"draft"> {
  return { body } as EmailMessage<"draft">;
}

function send(msg: EmailMessage<"draft">): EmailMessage<"sent"> {
  console.log("Sending:", msg.body);
  return msg as unknown as EmailMessage<"sent">;
}

// Only drafts can be sent; sent messages cannot be re-sent
const draft = createDraft("Hello!");
const sent = send(draft);        // OK
// send(sent);                      // error — EmailMessage<"sent"> not assignable to EmailMessage<"draft">
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Newtypes & Opaque Types** [-> T03](T03-newtypes-opaque.md) | Branded types and phantom types share the same implementation technique in TypeScript (brand intersection with `as` cast); the difference is intent: brands encode predicate proofs, phantoms encode categorical properties or states. |
| **Typestate** [-> T57](T57-typestate.md) | Typestate programming uses phantom type parameters to track which methods are legal in each state; the phantom parameter changes with each state transition, and the compiler rejects out-of-order calls. |
| **Refinement Types** [-> T26](T26-refinement-types.md) | Refinement brands (T26) and phantom types (T27) both use brand intersections; refinements prove a value satisfies a predicate, while phantoms encode a categorical label. The two patterns are often combined. |

## 5. Gotchas and Limitations

1. **The phantom field does not exist at runtime** — never access `value[__unit]` or `value.__tag` at runtime; the field is a compile-time fiction; the `as` cast in the constructor is the only place the phantom is established.
2. **Unsafe casts in constructors** — the constructor is the trust boundary; a bug in the constructor (wrong state cast) produces values with lying types; there is no runtime guard.
3. **`unique symbol` is required for global uniqueness** — if two modules each define `declare const __tag: unique symbol`, the resulting phantom types are incompatible even if conceptually the same; export and reuse a single symbol to share phantom tags across modules.
4. **Phantom parameters are invariant by default** — TypeScript checks generic parameters invariantly unless the type is structurally consistent with co/contravariance; if you need `Quantity<Meters>` to be a subtype of `Quantity<number>`, you need to add a covariant position to the type structure.
5. **Type parameter must appear in the type** — TypeScript will warn (or in strict mode, error) if a type parameter is unused; a phantom parameter that genuinely does not appear in the value shape requires using the brand intersection pattern to make it "used" without affecting runtime.
6. **IDE tooling shows the intersection** — hover types and error messages show `number & { readonly [__unit]: Meters }` rather than `Quantity<Meters>`, which is verbose; name intermediate types well to mitigate this.

## 6. Use-Case Cross-References

- [-> UC-01](../usecases/UC01-invalid-states.md) Use phantom types to make invalid combinations of values (e.g., wrong unit of measure) unrepresentable at the type level
- [-> UC-13](../usecases/UC13-state-machines.md) Encode state machine states as phantom type parameters so that illegal transitions are compile errors
- [-> UC-09](../usecases/UC09-builder-config.md) Use phantom types to track which builder steps have been completed, preventing `build()` from being called before required fields are set
