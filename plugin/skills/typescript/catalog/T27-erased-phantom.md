# Phantom Types

> **Since:** TypeScript community pattern; `unique symbol` since TypeScript 2.7

## 1. What It Is

A **phantom type** carries type-level information that has no runtime representation. In TypeScript, the pattern is achieved via brand intersection: `type Tagged<T, Brand> = T & { readonly __tag: Brand }`. The `__tag` field is never actually present on the value at runtime — the cast is performed with `as` in a smart constructor — so there is zero runtime overhead. Phantom types are used to encode categorical properties: units of measure (prevent adding meters to feet), state-machine states (prevent calling `send()` on an already-sent email), capability tokens (only code that holds a `Permission<"admin">` can call admin APIs), and phantom lifetimes (ensure a borrowed reference does not outlive its owner, at the type level).

**Tag types** — the phantom parameters themselves — are declared with `declare const` or as empty interfaces and are never instantiated at runtime. They are the TypeScript equivalent of Rust's zero-size marker types and Python's `TYPE_CHECKING`-only classes: they exist purely for the type checker, costing zero bytes at runtime.

```typescript
// These tag types are compile-time fictions — no runtime value is ever created
declare const Meters: unique symbol;
declare const Feet:   unique symbol;
type Meters = typeof Meters;
type Feet   = typeof Feet;
```

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

## 4. Beginner Mental Model

Think of phantom types as **invisible ink stamps on a document**. At runtime, a "draft email" and a "sent email" are identical JavaScript objects — both have just a `body` string, nothing more. But the type checker sees the invisible stamp: red ink for `"draft"`, blue ink for `"sent"`. The smart constructor applies the stamp (the `as` cast), and from that point on the compiler refuses to treat a blue-stamped value as a red-stamped one.

The stamp costs absolutely nothing at runtime — it is pure fiction in the type system — but the compiler enforces it strictly at every call site.

**Compared to other languages:**
- *Rust's `PhantomData<T>`*: the closest analogue. Rust requires an explicit zero-size field to hold the marker; TypeScript uses a brand intersection with a `unique symbol` key instead. Both are zero-cost at runtime.
- *Lean's `Prop` erasure*: more powerful — entire proof computations are erased, not just marker types. TypeScript has no dependent types or proof obligations; the phantom field is the entirety of the mechanism.
- *Python's `Generic[S]` phantom parameters*: identical intent. Python's runtime equally ignores the phantom parameter; the type checker enforces it. The main difference is that TypeScript brand intersections also prevent implicit structural compatibility between different brands, whereas Python relies entirely on the checker's nominal treatment of generics.

## 5. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Newtypes & Opaque Types** [-> T03](T03-newtypes-opaque.md) | Branded types and phantom types share the same implementation technique in TypeScript (brand intersection with `as` cast); the difference is intent: brands encode predicate proofs, phantoms encode categorical properties or states. |
| **Generics & Type Bounds** [-> T04](T04-generics-bounds.md) | Phantom parameters only have meaning inside generic types. Constrain the phantom parameter (`State extends "locked" \| "unlocked"`) to limit which tag values are valid and to enable exhaustive checks. |
| **Variance & Subtyping** [-> T08](T08-variance-subtyping.md) | TypeScript checks generic parameters structurally; a phantom parameter that appears only in a covariant position makes the outer type covariant in that parameter. Invariance is the default when the parameter has no explicit position in the shape — the brand field supplies that position. |
| **Union Types** [-> T02](T02-union-intersection.md) | `Request<"authenticated"> \| Request<"anonymous">` accepts both phantom states where a single state is required for secure endpoints. Use discriminated unions of phantom-branded values to model multi-state inputs. |
| **Typestate** [-> T57](T57-typestate.md) | Typestate programming uses phantom type parameters to track which methods are legal in each state; the phantom parameter changes with each state transition, and the compiler rejects out-of-order calls. |
| **Refinement Types** [-> T26](T26-refinement-types.md) | Refinement brands (T26) and phantom types (T27) both use brand intersections; refinements prove a value satisfies a predicate, while phantoms encode a categorical label. The two patterns are often combined. |

## 6. Gotchas and Limitations

1. **The phantom field does not exist at runtime** — never access `value[__unit]` or `value.__tag` at runtime; the field is a compile-time fiction; the `as` cast in the constructor is the only place the phantom is established.
2. **Unsafe casts in constructors** — the constructor is the trust boundary; a bug in the constructor (wrong state cast) produces values with lying types; there is no runtime guard.
3. **`unique symbol` is required for global uniqueness** — if two modules each define `declare const __tag: unique symbol`, the resulting phantom types are incompatible even if conceptually the same; export and reuse a single symbol to share phantom tags across modules.
4. **Phantom parameters are invariant by default** — TypeScript checks generic parameters invariantly unless the type is structurally consistent with co/contravariance; if you need `Quantity<Meters>` to be a subtype of `Quantity<number>`, you need to add a covariant position to the type structure.
5. **Type parameter must appear in the type** — TypeScript will warn (or in strict mode, error) if a type parameter is unused; a phantom parameter that genuinely does not appear in the value shape requires using the brand intersection pattern to make it "used" without affecting runtime.
6. **IDE tooling shows the intersection** — hover types and error messages show `number & { readonly [__unit]: Meters }` rather than `Quantity<Meters>`, which is verbose; name intermediate types well to mitigate this.
7. **No runtime introspection** — unlike a discriminated union with a `kind` field, you cannot branch on a phantom parameter at runtime. If you need both compile-time tracking *and* runtime inspection, use a discriminated union instead.

## 7. Example A — Typestate door lock

```typescript
declare const __lockState: unique symbol;

// Phantom tag types — zero runtime cost
interface Locked   { readonly [__lockState]: "locked" }
interface Unlocked { readonly [__lockState]: "unlocked" }

type Door<State> = { readonly name: string } & State;

function createDoor(name: string): Door<Locked> {
  return { name } as Door<Locked>;
}

function unlock(door: Door<Locked>, key: string): Door<Unlocked> {
  console.log(`Unlocking ${door.name} with key ${key}`);
  return door as unknown as Door<Unlocked>;
}

function enter(door: Door<Unlocked>): void {
  console.log(`Entering through ${door.name}`);
}

function lock(door: Door<Unlocked>): Door<Locked> {
  console.log(`Locking ${door.name}`);
  return door as unknown as Door<Locked>;
}

const front = createDoor("front");
// enter(front);             // error — Door<Locked> is not assignable to Door<Unlocked>
const open = unlock(front, "secret");
enter(open);                 // OK
const closed = lock(open);
// enter(closed);            // error — back to Locked
```

## 8. Example B — Validated vs. unvalidated IDs

```typescript
declare const __validated: unique symbol;

type Unvalidated<T> = T & { readonly [__validated]?: false };
type Validated<T>   = T & { readonly [__validated]: true };

type Email = string;

function validateEmail(raw: Unvalidated<Email>): Validated<Email> | null {
  const parts = raw.split("@");
  if (parts.length === 2 && parts[1].includes(".")) {
    return raw as Validated<Email>;
  }
  return null;
}

function sendWelcome(email: Validated<Email>): void {
  console.log(`Sending welcome to ${email}`);
}

const raw = "alice@example.com" as Unvalidated<Email>;
// sendWelcome(raw);                          // error — Unvalidated not assignable to Validated

const validated = validateEmail(raw);
if (validated !== null) {
  sendWelcome(validated);                    // OK — narrowed to Validated<Email>
}
```

## 9. Use-Case Cross-References

- [-> UC-01](../usecases/UC01-invalid-states.md) Use phantom types to make invalid combinations of values (e.g., wrong unit of measure) unrepresentable at the type level
- [-> UC-02](../usecases/UC02-domain-modeling.md) Domain boundaries use phantom-branded types to distinguish semantically different values that share the same runtime representation
- [-> UC-04](../usecases/UC04-generic-constraints.md) Generic phantom parameters encode state machines and capability tracking without runtime cost
- [-> UC-09](../usecases/UC09-builder-config.md) Use phantom types to track which builder steps have been completed, preventing `build()` from being called before required fields are set
- [-> UC-13](../usecases/UC13-state-machines.md) Encode state machine states as phantom type parameters so that illegal transitions are compile errors

## 10. Source Anchors

- TypeScript Handbook — *Literal Types* and *Template Literal Types* (brand intersection foundation)
- TypeScript 2.7 release notes — `unique symbol`
- TypeScript Deep Dive — *Nominal Typing* (brand pattern)
- `microsoft/TypeScript` issues #202 (nominal/opaque types tracking issue)
